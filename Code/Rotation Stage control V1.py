# servo_control_panel.py
# This script creates a graphical user interface (GUI) using Tkinter to control
# an MKS SERVO42D motor via a CAN bus connection. It allows for setting the motor's
# angle, speed, acceleration, and other configurations, while providing real-time
# feedback on the motor's current angle.

import tkinter as tk
from tkinter import ttk, messagebox
import can
from mks_servo_can import MksServo
from enum import Enum
import threading
import time
import traceback

# --- Enum and Error Handling ---
# Attempt to import necessary enums and custom error types from the mks_servo_can library.
# If the specific imports fail, it falls back to more generic imports or placeholder classes
# to ensure the script can run even with different library versions.
try:
    from mks_servo_can.mks_enums import Enable as MksEnableEnum
    from mks_servo_can.mks_enums import Direction as MksDirectionEnum
    from mks_servo_can.mks_enums import SuccessStatus
    from mks_servo_can.mks_enums import GoHomeResult
    from mks_servo_can.mks_servo import InvalidResponseError as MksInvalidResponseError
except ImportError:
    try:
        from mks_servo_can import Enable as MksEnableEnum
        from mks_servo_can import Direction as MksDirectionEnum
        from mks_servo_can import SuccessStatus
        from mks_servo_can import GoHomeResult
        class MksInvalidResponseError(Exception): pass # Placeholder error class
    except ImportError:
        # Fallback placeholder enums if the library is not installed or is an old version
        class MksEnableEnum(Enum): Disable = 0; Enable = 1
        class MksDirectionEnum(Enum): CW = 0; CCW = 1
        class SuccessStatus(Enum): Fail = 0; Success = 1
        class GoHomeResult(Enum): Fail = 0; Start = 1; Success = 2
        class MksInvalidResponseError(Exception): pass

# --- Configuration Constants ---
# These constants define the connection parameters and physical properties of the system.
CAN_INTERFACE = "socketcan"  # Type of CAN interface (e.g., 'socketcan', 'pcan', 'vector')
CAN_CHANNEL = "can0"         # Channel name for the CAN interface
CAN_BITRATE = 500000         # CAN bus speed in bits per second
SERVO_CAN_ID = 1             # The unique ID of the servo on the CAN bus
GEAR_RATIO = 17.0            # The gear ratio of the gearbox attached to the motor

# This constant defines the number of abstract "pulses" the servo's firmware expects
# for one full motor revolution when using absolute positioning commands. This is a
# fixed value defined by the servo's command protocol.
PULSES_PER_MOTOR_REVOLUTION_FOR_COMMAND = 16384

# --- Global Variables ---
# These variables hold the state of the application and are accessed by multiple functions.
bus = None                                  # Holds the python-can bus object
notifier = None                             # Holds the python-can notifier object
servo_wrapper = None                        # Holds the MksServo library object
current_output_angle_deg = 0.0              # Stores the last calculated output angle in degrees
stop_reading_thread = False                 # Flag to signal the feedback reading thread to stop
gui_ready = False                           # Flag to indicate if the GUI is fully initialized
app_running = True                          # Flag to indicate if the main application loop is active
e_stop_active = False                       # Flag to indicate if the emergency stop is active
library_feedback_raw_offset_at_zero = 0     # Stores the raw encoder reading at the logical zero position

# This dictionary maps the servo's subdivision codes to a calibrated value representing
# the number of raw feedback units per degree of motor rotation. This is essential for
# converting the raw encoder feedback into a meaningful angle.
# These values should be determined by running a calibration script for your specific setup.
CALIBRATION_FEEDBACK_MAP = {
    1:   15941.0 / 360.0,   # Approx 44.28 (Full Step)
    2:   16231.0 / 360.0,   # Approx 45.09
    4:   16401.0 / 360.0,   # Approx 45.56
    8:   16378.0 / 360.0,   # Approx 45.49
    16:  16378.0 / 360.0,   # Approx 45.49
    32:  16378.0 / 360.0,   # Approx 45.49
    64:  16377.0 / 360.0,   # Approx 45.49
    128: 16383.0 / 360.0,   # Approx 45.51
    255: 16321.0 / 360.0,   # Approx 45.34
}
# The list of subdivision codes to be displayed in the GUI dropdown.
SUBDIVISION_CODES_FOR_GUI = [1, 2, 4, 8, 16, 32, 64, 128, 255]

# --- Tkinter Global Variables ---
# These variables are Tkinter-specific and are linked to GUI widgets.
current_speed_tkvar = None
current_acceleration_tkvar = None
current_subdivision_tkvar = None
current_interpolation_enabled_tkvar = None
current_feedback_scaling_display_tkvar = None
enable_val_for_interpolation_type = None # Stores the correct type (Enum or bool) for enabling interpolation

# --- Core Functions ---

def update_feedback_scaling_for_subdivision(subdivision_code_from_gui):
    """
    Updates the feedback scaling factor based on the selected subdivision code.
    This is called whenever the subdivision is changed in the GUI. It also resets
    the zero offset, requiring the user to re-zero the system.
    """
    global FEEDBACK_UNITS_PER_MOTOR_DEGREE_CURRENT, library_feedback_raw_offset_at_zero, gui_ready
    global current_feedback_scaling_display_tkvar

    subdivision_value = int(subdivision_code_from_gui)

    # Look up the calibration value from the map
    if subdivision_value in CALIBRATION_FEEDBACK_MAP:
        FEEDBACK_UNITS_PER_MOTOR_DEGREE_CURRENT = CALIBRATION_FEEDBACK_MAP[subdivision_value]
        if current_feedback_scaling_display_tkvar:
            current_feedback_scaling_display_tkvar.set(f"{FEEDBACK_UNITS_PER_MOTOR_DEGREE_CURRENT:.4f} units/deg")
    else:
        # If the subdivision is not in our map, we cannot convert feedback to degrees
        FEEDBACK_UNITS_PER_MOTOR_DEGREE_CURRENT = None
        if current_feedback_scaling_display_tkvar:
            current_feedback_scaling_display_tkvar.set("N/A (Uncalibrated)")
        if gui_ready:
            messagebox.showwarning("Calibration Needed",
                                   "No feedback scaling factor for this subdivision code.\n"
                                   "To show degrees, run a calibration script and update CALIBRATION_FEEDBACK_MAP.")

    # Reset the zero offset since the feedback scaling has changed
    library_feedback_raw_offset_at_zero = 0
    if gui_ready:
        messagebox.showinfo("Re-Zero Recommended",
                            f"Subdivision changed to {subdivision_value}.\n"
                            "Display offset has been reset. Please press 'Set Zero' or 'Home Motor'.")

def set_servo_configuration_from_gui():
    """
    Sends the selected subdivision and interpolation settings from the GUI to the servo.
    """
    global servo_wrapper, app_running, gui_ready
    global current_subdivision_tkvar, current_interpolation_enabled_tkvar, enable_val_for_interpolation_type

    if not (servo_wrapper and app_running):
        if gui_ready: messagebox.showwarning("Config Error", "Servo not connected.")
        return
    if not all([current_subdivision_tkvar, current_interpolation_enabled_tkvar]):
        if gui_ready: messagebox.showerror("Internal Error", "GUI config variables not ready.")
        return

    subdiv_code_val = current_subdivision_tkvar.get()
    interp_bool_val = current_interpolation_enabled_tkvar.get()

    # Determine the correct type to send for the interpolation setting (Enum or boolean)
    if isinstance(enable_val_for_interpolation_type, type(MksEnableEnum.Enable)):
        interp_setting_for_servo = MksEnableEnum.Enable if interp_bool_val else MksEnableEnum.Disable
    else:
        interp_setting_for_servo = interp_bool_val

    try:
        # Send the commands to the servo
        servo_wrapper.set_subdivisions(subdiv_code_val)
        servo_wrapper.set_subdivision_interpolation(interp_setting_for_servo)
        time.sleep(0.1)
        # Update our internal scaling to match the new servo setting
        update_feedback_scaling_for_subdivision(subdiv_code_val)
    except AttributeError as ae:
        if gui_ready: messagebox.showerror("Config Error", f"AttributeError: {ae}.\nMksServo library might be missing this function.")
    except Exception as e_conf:
        if gui_ready: messagebox.showerror("Config Error", f"Error: {e_conf}")

def _apply_default_servo_config():
    """
    Applies a default configuration to the servo on initial connection.
    Sets subdivision to the first available option and enables interpolation.
    """
    global servo_wrapper, current_subdivision_tkvar, current_interpolation_enabled_tkvar
    if not servo_wrapper:
        return

    try:
        # Set the GUI widgets to the default values
        if current_subdivision_tkvar: current_subdivision_tkvar.set(SUBDIVISION_CODES_FOR_GUI[0])
        if current_interpolation_enabled_tkvar: current_interpolation_enabled_tkvar.set(True)

        # Apply the configuration to the servo
        if current_subdivision_tkvar and current_interpolation_enabled_tkvar:
            set_servo_configuration_from_gui()
        else:
            # Fallback if GUI variables aren't ready for some reason
            servo_wrapper.set_subdivisions(SUBDIVISION_CODES_FOR_GUI[0])
            interp_val_direct = MksEnableEnum.Enable if isinstance(enable_val_for_interpolation_type, type(MksEnableEnum.Enable)) else True
            servo_wrapper.set_subdivision_interpolation(interp_val_direct)
            update_feedback_scaling_for_subdivision(SUBDIVISION_CODES_FOR_GUI[0])

    except Exception as e:
        if gui_ready: messagebox.showerror("Config Error", f"Failed to apply default servo config: {e}")

def connect_can():
    """
    Establishes the connection to the CAN bus and initializes the servo object.
    """
    global bus, notifier, servo_wrapper, app_running, e_stop_active, library_feedback_raw_offset_at_zero
    global enable_val_for_interpolation_type

    if not app_running: return False
    e_stop_active = False
    library_feedback_raw_offset_at_zero = 0

    try:
        # Initialize the CAN bus interface
        bus = can.interface.Bus(interface=CAN_INTERFACE, channel=CAN_CHANNEL, bitrate=CAN_BITRATE)
        notifier = can.Notifier(bus, []) # Notifier with no initial listeners
        servo_wrapper = MksServo(bus, notifier, SERVO_CAN_ID)

        if servo_wrapper:
            # Determine the correct type for 'Enable' based on the library version
            enable_enum = getattr(MksServo, 'Enable', MksEnableEnum)
            if hasattr(enable_enum, 'Enable'):
                enable_val_for_interpolation_type = enable_enum.Enable
            else:
                enable_val_for_interpolation_type = True

            # Apply the default configuration
            _apply_default_servo_config()

            # Take an initial encoder reading to set the starting offset
            initial_feedback_val = servo_wrapper.read_encoder_value_addition()
            if isinstance(initial_feedback_val, int):
                library_feedback_raw_offset_at_zero = initial_feedback_val
        return True
    except Exception as e:
        if gui_ready: messagebox.showerror("CAN Connection Error", f"Error: {e}\nCheck console for details.")
        traceback.print_exc()
        bus, notifier, servo_wrapper = None, None, None
        return False

def disconnect_can():
    """
    Safely disconnects from the CAN bus and releases resources.
    """
    global bus, notifier, servo_wrapper, reading_thread
    
    # Wait for the reading thread to finish if it's running
    if reading_thread and reading_thread.is_alive() and reading_thread != threading.current_thread():
        reading_thread.join(timeout=2.0)

    # Stop the notifier and shut down the bus
    if notifier:
        try: notifier.stop(timeout=1.0)
        except Exception as e: print(f"Error stopping notifier: {e}")
    if bus:
        try: bus.shutdown()
        except Exception as e: print(f"Error shutting down bus: {e}")
    
    bus, notifier, servo_wrapper = None, None, None

def set_output_angle_from_gui():
    """
    Gets the target angle and motion parameters from the GUI and initiates the move.
    """
    global root, gui_ready, servo_wrapper, angle_entry, current_speed_tkvar, current_acceleration_tkvar
    if not app_running or servo_wrapper is None:
        if gui_ready: messagebox.showerror("Error", "Servo not connected or app not running.")
        return

    try:
        angle_str = angle_entry.get()
        speed_val = current_speed_tkvar.get()
        accel_val = current_acceleration_tkvar.get()
        _set_output_angle_command(angle_str, speed_val, accel_val)
    except (tk.TclError, ValueError):
        if gui_ready: messagebox.showerror("Input Error", "Invalid number format in Angle/Speed/Accel entries.")

def _set_output_angle_command(target_output_angle_deg_str, speed, acceleration):
    """
    Calculates the required motor command pulses and sends the move command to the servo.
    """
    global servo_wrapper, e_stop_active, gui_ready, root

    if e_stop_active:
        if gui_ready: messagebox.showwarning("E-STOP Active", "Motion is blocked.")
        return

    try:
        target_output_angle_deg = float(target_output_angle_deg_str)

        # Convert the desired output angle (after gearbox) to the required motor angle
        motor_degrees_relative_to_output_zero = target_output_angle_deg * GEAR_RATIO
        # Convert motor angle to the abstract "command pulses" the servo understands
        pulses_for_relative_move_float = \
            (motor_degrees_relative_to_output_zero / 360.0) * PULSES_PER_MOTOR_REVOLUTION_FOR_COMMAND
        motor_target_command_pulses = round(pulses_for_relative_move_float)

        target_speed = int(speed)
        target_acceleration = int(acceleration)

        # Validate inputs against servo limits
        max_s = MksServo.MAX_SPEED if hasattr(MksServo, 'MAX_SPEED') else 3000
        max_a = MksServo.MAX_ACCELERATION if hasattr(MksServo, 'MAX_ACCELERATION') else 255
        MOTOR_PULSE_CMD_MIN = -(1 << 23)
        MOTOR_PULSE_CMD_MAX = (1 << 23) - 1

        error_messages = []
        if not (0 < target_speed <= max_s): error_messages.append(f"Speed {target_speed} RPM out of range (1-{max_s}).")
        if not (0 < target_acceleration <= max_a): error_messages.append(f"Accel {target_acceleration} out of range (1-{max_a}).")
        if not (MOTOR_PULSE_CMD_MIN <= motor_target_command_pulses <= MOTOR_PULSE_CMD_MAX):
            error_messages.append(f"Target motor command pulses ({motor_target_command_pulses}) exceeds servo's 24-bit range.")

        if error_messages:
            if gui_ready: messagebox.showerror("Input Error(s)", "\n".join(error_messages))
            return

        # Send the absolute motion command
        servo_wrapper.run_motor_absolute_motion_by_axis(target_speed, target_acceleration, motor_target_command_pulses)

    except ValueError:
        if gui_ready: messagebox.showerror("Input Error", "Invalid number format for angle, speed, or acceleration.")
    except Exception as e:
        if gui_ready: messagebox.showerror("Servo Command Error", f"Error sending move command: {e}")
        traceback.print_exc()

def read_current_angle_periodically():
    """
    This function runs in a separate thread to continuously read the servo's encoder value,
    convert it to an angle, and schedule a GUI update.
    """
    global current_output_angle_deg, servo_wrapper, stop_reading_thread, app_running, gui_ready, e_stop_active
    global library_feedback_raw_offset_at_zero, FEEDBACK_UNITS_PER_MOTOR_DEGREE_CURRENT

    while not stop_reading_thread and app_running:
        calculated_out_angle = None
        raw_lib_val = None
        is_calibrated_this_cycle = False

        # Only query the servo if it's connected and not in E-stop
        if servo_wrapper and not e_stop_active:
            try:
                # Read the raw accumulated encoder value from the servo
                raw_lib_val = servo_wrapper.read_encoder_value_addition()
                if isinstance(raw_lib_val, int):
                    # Calculate the position relative to the last zeroing point
                    relative_feedback_units = raw_lib_val - library_feedback_raw_offset_at_zero
                    
                    # If we have a calibration factor, convert raw units to degrees
                    if FEEDBACK_UNITS_PER_MOTOR_DEGREE_CURRENT and FEEDBACK_UNITS_PER_MOTOR_DEGREE_CURRENT != 0:
                        motor_angle_deg = relative_feedback_units / FEEDBACK_UNITS_PER_MOTOR_DEGREE_CURRENT
                        if GEAR_RATIO != 0:
                            calculated_out_angle = motor_angle_deg / GEAR_RATIO
                        else:
                            calculated_out_angle = 0.0
                        is_calibrated_this_cycle = True
                        current_output_angle_deg = calculated_out_angle # Update global state
                    else:
                        # If not calibrated, the value to display is the raw relative units
                        calculated_out_angle = relative_feedback_units
                        is_calibrated_this_cycle = False
            except Exception:
                # Catch any errors during the read and handle them gracefully
                raw_lib_val = "Read Error"
                is_calibrated_this_cycle = False
        
        # Schedule the GUI update. This is safe to call from a background thread.
        if app_running and gui_ready and root:
            try:
                display_value = calculated_out_angle if raw_lib_val is not None else None
                root.after(0, update_angle_display, display_value, is_calibrated_this_cycle)
            except (RuntimeError, tk.TclError):
                # This can happen if the GUI is being destroyed, so we just stop trying to update
                pass
        
        # Wait for a short period to control the loop frequency
        time.sleep(0.1)

def on_set_zero_button():
    """
    Handles the 'Set Zero' button click. Tells the servo to consider its current
    physical position as the new logical zero for commands and updates the script's
    internal feedback offset.
    """
    global servo_wrapper, app_running, root, e_stop_active
    global library_feedback_raw_offset_at_zero

    if e_stop_active or servo_wrapper is None:
        if gui_ready: messagebox.showwarning("Action Blocked", "Cannot set zero while E-STOP is active or servo is disconnected.")
        return

    try:
        # Send the command to the servo to set its internal zero
        servo_wrapper.set_current_axis_to_zero()
    except MksInvalidResponseError as e_mks:
        # This error means the library sent the command but didn't understand the servo's reply.
        # The servo may have still executed the command, so we proceed with a warning.
        if gui_ready: messagebox.showwarning("Set Zero Warning", f"Servo response was unusual: {e_mks}\nAttempting to set offset anyway.")
    except Exception as e_other:
        if gui_ready: messagebox.showerror("Servo Command Error", f"Error sending 'set_current_axis_to_zero': {e_other}")
        return

    # Give the servo a moment to process the command
    time.sleep(0.2)

    # Read the encoder value at this new zero position to get the new feedback offset
    try:
        current_feedback_at_zero = servo_wrapper.read_encoder_value_addition()
        if isinstance(current_feedback_at_zero, int):
            library_feedback_raw_offset_at_zero = current_feedback_at_zero
            if gui_ready: messagebox.showinfo("Set Zero", "Motor logical zero reset and display offset updated.")
        else:
            if gui_ready: messagebox.showerror("Set Zero Error", "Failed to read valid encoder offset after zeroing command.")
    except Exception as e_capture:
        if gui_ready: messagebox.showerror("Set Zero Error", f"Error capturing zero offset: {e_capture}")

    # Update the display to show 0.0
    is_calibrated = FEEDBACK_UNITS_PER_MOTOR_DEGREE_CURRENT is not None
    if app_running and gui_ready and root:
        update_angle_display(0.0, is_calibrated)

def on_home_motor_button():
    """
    Handles the 'Home Motor' button click. Initiates the servo's built-in homing sequence.
    NOTE: Requires the servo to be pre-configured for the desired homing mode (e.g., stall homing).
    """
    global servo_wrapper, app_running, root, e_stop_active, library_feedback_raw_offset_at_zero
    
    if e_stop_active or servo_wrapper is None:
        if gui_ready: messagebox.showwarning("Action Blocked", "Cannot home while E-STOP is active or servo is disconnected.")
        return

    homing_speed_rpm = 50
    homing_direction_val = MksDirectionEnum.CW
    
    # Prompt the user to confirm, as this involves physical motion
    if gui_ready:
        if not messagebox.askokcancel("Confirm Homing",
                                      "Ensure motor path is clear for homing to a hard stop!\n"
                                      "Servo MUST be pre-configured for 'noLimit' (stall) mode via its menu.\n\n"
                                      "Proceed with homing attempt?"):
            return

    try:
        # The MKS library's set_home() may not expose all parameters for stall homing.
        # The servo must be pre-configured.
        servo_wrapper.set_home(0, homing_direction_val, homing_speed_rpm, MksEnableEnum.Disable)
        
        # Execute the homing routine
        homing_run_result = servo_wrapper.b_go_home()
        
        # Check if homing was successful
        is_homing_physical_success = (hasattr(homing_run_result, 'value') and homing_run_result.value == GoHomeResult.Success.value)

        if is_homing_physical_success:
            time.sleep(0.2)
            # After successful homing, set the new zero offset
            pos_after_home = servo_wrapper.read_encoder_value_addition()
            if isinstance(pos_after_home, int):
                library_feedback_raw_offset_at_zero = pos_after_home
                if gui_ready: messagebox.showinfo("Homing", "Homing successful. Display offset updated.")
                # Update display to 0.0
                is_calibrated = FEEDBACK_UNITS_PER_MOTOR_DEGREE_CURRENT is not None
                if app_running and gui_ready and root: update_angle_display(0.0, is_calibrated)
            else:
                if gui_ready: messagebox.showerror("Homing Error", "Homing succeeded, but failed to read position after.")
        else:
            if gui_ready: messagebox.showerror("Homing Error", f"Homing failed. Servo Result: {homing_run_result}")

    except Exception as e:
        if gui_ready: messagebox.showerror("Homing Error", f"An error occurred during homing: {e}")
        traceback.print_exc()

def on_emergency_stop_button():
    """
    Sends an emergency stop command to the servo and disables motion controls in the GUI.
    """
    global servo_wrapper, e_stop_active, gui_ready, root
    if servo_wrapper is None:
        if gui_ready: messagebox.showerror("Error", "Servo not connected.")
        return

    try:
        servo_wrapper.emergency_stop_motor()
        e_stop_active = True
        update_gui_for_e_stop_status(True)
        if gui_ready: messagebox.showinfo("E-STOP", "E-Stop command sent. Motion is blocked.")
    except Exception as e:
        if gui_ready: messagebox.showerror("Servo Command Error", f"E-STOP Error: {e}")
        traceback.print_exc()

def update_angle_display(value, is_calibrated_format=True):
    """
    Updates the main angle display label in the GUI. This function is always
    called from the main thread via root.after().
    """
    global current_angle_label, app_running, root, current_feedback_scaling_display_tkvar

    if not (app_running and root and root.winfo_exists()):
        return

    new_text = ""
    # Format the text based on whether the value is a calibrated degree or raw units
    if value is None:
        new_text = "Output Angle: N/A"
    elif is_calibrated_format:
        try:
            new_text = f"Output Angle: {float(value):.3f}°"
        except (ValueError, TypeError):
            new_text = f"Output Angle: Format Error"
    else:
        new_text = f"Output (Raw Units): {value}"

    # Update the label only if the text has changed to reduce GUI flicker
    if current_angle_label and (not hasattr(update_angle_display, 'last_gui_text') or update_angle_display.last_gui_text != new_text):
        update_angle_display.last_gui_text = new_text
        try:
            current_angle_label.config(text=new_text)
        except tk.TclError:
            pass # Ignore error if the label is destroyed during update

def update_gui_for_e_stop_status(is_estopped: bool):
    """
    Enables or disables motion-related GUI widgets based on the E-stop status.
    """
    global angle_entry, set_angle_gui_button, set_zero_button, home_button
    global speed_entry, accel_entry, subdivision_combobox, apply_config_button, interpolation_check
    global estop_button

    # Set state to DISABLED if estopped, otherwise NORMAL
    new_state = tk.DISABLED if is_estopped else tk.NORMAL

    # List of all widgets to be controlled
    widgets_to_control = [angle_entry, set_angle_gui_button, set_zero_button, home_button,
                          speed_entry, accel_entry, subdivision_combobox,
                          apply_config_button, interpolation_check]

    for widget in widgets_to_control:
        if widget:
            try: widget.config(state=new_state)
            except tk.TclError: pass

    # Change the E-STOP button style to indicate its state
    if estop_button:
        try:
            estop_button.config(style="EstopActive.TButton" if is_estopped else "Emergency.TButton")
        except tk.TclError: pass

def on_closing():
    """
    Handles the application closing event. Ensures threads are stopped and
    the CAN connection is cleanly disconnected.
    """
    global stop_reading_thread, app_running, root
    
    if not app_running: return # Avoid running cleanup multiple times
    
    # Confirm with the user before quitting
    if gui_ready and root and root.winfo_exists():
        if not messagebox.askokcancel("Quit", "Do you want to quit? This will disconnect the CAN bus."):
            return

    # Signal all loops and threads to stop
    app_running = False
    stop_reading_thread = True

    # Disconnect from CAN
    disconnect_can()

    # Destroy the GUI window
    if root:
        try:
            root.destroy()
            root = None
        except tk.TclError: pass

# --- GUI Setup ---
# This section initializes the main Tkinter window and creates all the widgets.
root = tk.Tk()
root.title("Servo Control Panel")

# Initialize Tkinter variables to hold widget states
current_speed_tkvar = tk.IntVar(value=1000)
current_acceleration_tkvar = tk.IntVar(value=255)
current_subdivision_tkvar = tk.IntVar(value=SUBDIVISION_CODES_FOR_GUI[0]) # Default to first in list
current_interpolation_enabled_tkvar = tk.BooleanVar(value=True)
current_feedback_scaling_display_tkvar = tk.StringVar(value="N/A")

# --- Connection & Homing Frame ---
connection_frame = ttk.LabelFrame(root, text="Connection & Homing", padding="10")
connection_frame.pack(padx=10, pady=5, fill="x", expand=True)
connect_button = ttk.Button(connection_frame, text="Connect", command=connect_can)
connect_button.pack(side=tk.LEFT, padx=5)
home_button = ttk.Button(connection_frame, text="Home Motor (Stall)", command=on_home_motor_button)
home_button.pack(side=tk.LEFT, padx=15)

# --- Servo Configuration Frame ---
config_frame = ttk.LabelFrame(root, text="Servo Configuration", padding="10")
config_frame.pack(padx=10, pady=5, fill="x", expand=True)
ttk.Label(config_frame, text="Speed (RPM):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
speed_entry = ttk.Entry(config_frame, textvariable=current_speed_tkvar, width=7)
speed_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
ttk.Label(config_frame, text="Accel (1-255):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
accel_entry = ttk.Entry(config_frame, textvariable=current_acceleration_tkvar, width=7)
accel_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
ttk.Label(config_frame, text="Subdivision Code:").grid(row=0, column=2, sticky="w", padx=15, pady=2)
subdivision_combobox = ttk.Combobox(config_frame, textvariable=current_subdivision_tkvar, values=SUBDIVISION_CODES_FOR_GUI, width=5, state="readonly")
subdivision_combobox.grid(row=0, column=3, sticky="ew", padx=5, pady=2)
interpolation_check = ttk.Checkbutton(config_frame, text="Interpolation On", variable=current_interpolation_enabled_tkvar)
interpolation_check.grid(row=1, column=2, columnspan=2, sticky="w", padx=15, pady=2)
apply_config_button = ttk.Button(config_frame, text="Apply Config to Servo", command=set_servo_configuration_from_gui)
apply_config_button.grid(row=2, column=0, columnspan=4, pady=5)
config_frame.columnconfigure(1, weight=1)
config_frame.columnconfigure(3, weight=1)

# --- Motion Control Frame ---
control_frame = ttk.LabelFrame(root, text="Motion Control", padding="10")
control_frame.pack(padx=10, pady=5, fill="x", expand=True)
cf_left_frame = ttk.Frame(control_frame)
cf_left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
cf_right_frame = ttk.Frame(control_frame)
cf_right_frame.pack(side=tk.RIGHT, fill=tk.X)
ttk.Label(cf_left_frame, text="Output Angle (°):").pack(side=tk.LEFT, padx=5)
angle_entry = ttk.Entry(cf_left_frame, width=10)
angle_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
angle_entry.insert(0, "0.0")
set_angle_gui_button = ttk.Button(cf_right_frame, text="Set Angle", command=set_output_angle_from_gui)
set_angle_gui_button.pack(side=tk.LEFT, padx=5)
set_zero_button = ttk.Button(cf_right_frame, text="Set Zero (Logical)", command=on_set_zero_button)
set_zero_button.pack(side=tk.LEFT, padx=10)
estop_button = ttk.Button(cf_right_frame, text="E-STOP", command=on_emergency_stop_button, style="Emergency.TButton")
estop_button.pack(side=tk.LEFT, padx=10)

# Define custom styles for the E-STOP button
s = ttk.Style()
s.configure("Emergency.TButton", foreground="white", background="red", font=('Helvetica', '10', 'bold'))
s.configure("EstopActive.TButton", foreground="black", background="yellow", font=('Helvetica', '10', 'bold'))

# --- Status Display Frame ---
display_frame = ttk.LabelFrame(root, text="Status", padding="10")
display_frame.pack(padx=10, pady=5, fill="x", expand=True)
current_angle_label = ttk.Label(display_frame, text="Output Angle: N/A")
current_angle_label.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
ttk.Label(display_frame, text="FeedbackUnits/MotorDeg:").pack(side=tk.LEFT, padx=10)
current_ppmd_label = ttk.Label(display_frame, textvariable=current_feedback_scaling_display_tkvar, anchor="w")
current_ppmd_label.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

# --- Main Application Logic ---
# This block runs when the script is executed directly.
if __name__ == "__main__":
    reading_thread = None
    app_running, gui_ready = True, False

    # Attempt to connect to CAN bus on startup
    if connect_can():
        # If connection is successful, start the background thread for reading the angle
        stop_reading_thread = False
        reading_thread = threading.Thread(target=read_current_angle_periodically, daemon=True)
        reading_thread.start()
    else:
        # If connection fails, show a warning
        if root and root.winfo_exists():
            messagebox.showwarning("Startup Warning", "Could not connect to CAN bus. Check setup and use the 'Connect' button.")
        else:
            print("Startup Warning: Could not connect to CAN bus.")

    # Set the gui_ready flag to True after the main window and widgets are created
    gui_ready = True
    
    # Set the initial state of the GUI widgets
    update_gui_for_e_stop_status(e_stop_active)
    if current_subdivision_tkvar:
        update_feedback_scaling_for_subdivision(current_subdivision_tkvar.get())

    # Assign the custom closing function to the window's close button
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the Tkinter main event loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        if app_running: on_closing()
    finally:
        # Final cleanup to ensure threads are stopped
        app_running = False
        stop_reading_thread = True
        if reading_thread and reading_thread.is_alive():
            reading_thread.join(timeout=1.0)

