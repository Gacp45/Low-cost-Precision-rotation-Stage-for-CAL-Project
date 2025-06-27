Low-cost Precision Rotation Stage for CAL Project
This repository contains the complete design files, software, and documentation for a low-cost, 3D-printed, high-precision motorised rotation stage. The project was developed as part of a Master of Engineering Project at NMITE.

The primary motivation for this project is the high cost of commercial rotation stages, which presents a significant barrier to entry for researchers, educators, and enthusiasts in fields like optical automation and volumetric additive manufacturing (VAM), such as Computed Axial Lithography (CAL). This open-source design aims to provide a viable alternative that replicates the core functionality of commercial systems for a fraction of the price.

Software Setup and User Guide
This section provides a complete guide to setting up the hardware, installing the necessary software, and running the servo_control_panel.py application.

Features
Real-time Angle Control: Set absolute target positions for the output shaft.

Dynamic Configuration: Change motor speed, acceleration, and subdivision settings on the fly.

Live Feedback: Displays the current calculated output angle based on encoder feedback.

Logical Zeroing: Set the current motor position as a logical "zero" for relative commands.

Stall Homing: Initiate the servo's built-in sensorless homing sequence (requires servo pre-configuration).

Emergency Stop: Immediately halt all motor activity.

1. Hardware Requirements
MKS SERVO42D or a similar MKS servo motor with CAN bus support.

A host computer with a CAN interface. Common options include:

A Raspberry Pi with a CAN bus HAT (e.g., from Waveshare, Seeed Studio).

A PC/laptop with a USB-to-CAN adapter (e.g., from PEAK-System, Kvaser).

A stable Power Supply for the servo (typically 12V to 24V DC, check your servo's specifications).

CAN Bus Wiring:

A twisted pair of wires for CAN_H and CAN_L.

A 120 Ohm termination resistor at the end of the bus. This is crucial for bus stability.

2. Software Requirements
Operating System: A Linux-based OS is required for socketcan support (e.g., Raspberry Pi OS, Ubuntu, Debian).

Python: Python 3.7 or newer.

Python Libraries:

python-can

mks-servo-can

tkinter (usually included with Python standard installations).

3. Installation and Setup
Step 1: Hardware Connection
Connect the Servo: Wire the CAN_H and CAN_L pins from your servo to the corresponding pins on your CAN interface (e.g., CAN hat or USB adapter).

Power the Servo: Connect the servo's power input (V+, GND) to your power supply. Do not power the servo from your Raspberry Pi's or computer's logic pins.

Terminate the Bus: If the servo is the only other device on the bus besides your controller, place a 120 Ohm resistor across the CAN_H and CAN_L terminals.

Step 2: System CAN Configuration (for Raspberry Pi)
Enable the CAN overlay. Edit the /boot/config.txt file:

sudo nano /boot/config.txt

Add the following lines, adjusting oscillator based on your CAN hat's documentation (8000000 is common for an 8MHz crystal):

# For a standard MCP2515 based CAN HAT
dtparam=spi=on
dtoverlay=mcp2515-can0,oscillator=8000000,interrupt=25
dtoverlay=spi-bcm2835

Reboot your Raspberry Pi after saving the file.

Bring up the CAN interface. Once rebooted, run the following command in your terminal. This sets the bus speed to 500 kbit/s, matching the script's default.

sudo ip link set can0 up type can bitrate 500000

Verify the interface. You can check if the interface is up by running ip -details link show can0.

Step 3: Python Environment
It is highly recommended to use a Python virtual environment.

python3 -m venv servo_env
source servo_env/bin/activate

Install the required libraries:

pip install python-can mks-servo-can

4. Script Configuration
Before running the script, open the servo_control_panel.py file and review the Configuration Constants section at the top.

CAN_INTERFACE: Should be "socketcan" for most Raspberry Pi setups. Change if you are using a different backend (e.g., "pcan").

CAN_CHANNEL: Should be "can0" to match the system setup.

SERVO_CAN_ID: Crucial. This must match the ID configured on your servo. The default is 1.

GEAR_RATIO: Crucial. Set this to the exact ratio of your gearbox. For a 17:1 gearbox, the value is 17.0.

CALIBRATION_FEEDBACK_MAP: This is the most important part of the configuration for accurate angle feedback. You must calibrate this for your setup.

5. Calibration Guide
The servo's encoder reports its position in raw units, and the scaling of these units changes with the subdivision (microstepping) setting. To get an accurate angle display, you must calibrate the conversion factor for each subdivision you intend to use.

How to Calibrate:

Run the script: python servo_control_panel.py.

Connect to the servo using the GUI.

Select a Subdivision Code from the dropdown menu that you want to calibrate (e.g., 16).

Press "Set Zero (Logical)". This resets the script's internal position reference.

Command a large, precise move. Enter a large angle in the "Output Angle (°)" box. Using a multiple of 360 is best. For example, enter 3600 (which is 10 full output shaft rotations). Press "Set Angle". Wait for the motor to stop moving.

Check the Console Output. The script will be printing status lines to the terminal. Find the last AngleCalc line. It will look something like this:

AngleCalc (L...): RawLibVal=..., LibOffset=..., ..., Output=RawRel: 621560

When the script is uncalibrated for the current subdivision, the output is shown as RawRel. This is the number you need. In this example, the value is 621560.

Calculate the Factor. The formula is:
factor = total_raw_units / (total_output_degrees * GEAR_RATIO)
Using our example:
factor = 621560 / (3600 * 17.0) = 621560 / 61200 = 10.1562...
This factor is the feedback_units_per_motor_degree.

Update the Script. Open servo_control_panel.py and update the CALIBRATION_FEEDBACK_MAP with your new value.

CALIBRATION_FEEDBACK_MAP = {
    1:   15941.0 / 360.0,
    # ... other values
    16:  10.1562, # Your newly calculated value
    # ...
}

Note: For higher accuracy, you can leave it as a fraction: 621560 / 61200.0.

Repeat for every subdivision code you plan to use.

6. Running the Application
Once your hardware is connected, system is configured, and the script is calibrated, run the application from your terminal:

python servo_control_panel.py

7. Troubleshooting
CAN Connection Error:

Double-check your can0 interface is up (ip -details link show can0).

Verify your wiring (CAN_H to CAN_H, CAN_L to CAN_L).

Ensure the 120 Ohm termination resistor is present.

Make sure the servo is powered on.

Servo Not Responding to Commands:

Verify that SERVO_CAN_ID in the script matches the ID set on the servo.

Check for any error lights on the servo itself.

Inaccurate Angle Display:

The most common cause is an incorrect or missing calibration value in CALIBRATION_FEEDBACK_MAP. Re-run the calibration process for the current subdivision.

Ensure GEAR_RATIO is set
