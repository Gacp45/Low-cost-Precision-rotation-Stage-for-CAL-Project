# Low-Cost Precision Rotation Stage for Computed Axial Lithography (CAL)

This repository contains the complete design files, software, and documentation for a low-cost, 3D-printed, high-precision motorised rotation stage. The project was developed as part of a Master of Engineering Project at NMITE.

The primary motivation for this project is the high cost of commercial rotation stages, which presents a significant barrier to entry for researchers, educators, and enthusiasts in fields like optical automation and volumetric additive manufacturing (VAM), such as Computed Axial Lithography (CAL). This open-source design aims to provide a viable alternative that replicates the core functionality of commercial systems for a fraction of the price.

## Table of Contents

- [Features](#features)
- [Hardware Requirements](#1-hardware-requirements)
- [Software Requirements](#2-software-requirements)
- [Installation and Setup](#3-installation-and-setup)
- [Script Configuration](#4-script-configuration)
- [Calibration Guide](#5-calibration-guide)
- [Running the Application](#6-running-the-application)
- [Troubleshooting](#7-troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Features

- Precision rotation stage using a geared stepper motor (MKS SERVO42D)
- GUI-based control panel using Tkinter
- Real-time angle feedback display (in degrees)
- Customisable speed, acceleration, and microstepping settings
- Logical zero setting and stall-based homing
- Emergency stop functionality
- Modular and open-source design

---

### 1. Hardware Requirements

- **MKS SERVO42D** stepper motor with CAN bus interface.
- **A host computer with a CAN interface.** Common options include:
  - A CAN-to-USB adapter (e.g., CANable, USBtin, PCAN-USB).
  - A Raspberry Pi with a CAN bus HAT or CAN-to-USB Adapter.
- **A stable Power Supply** for the servo (typically 12V to 24V DC).
- **CAN Bus Wiring:**
  - A twisted pair of wires for `CAN_H` and `CAN_L`.
  - A **120 Ohm termination resistor** at the end of the bus. This is crucial for bus stability.
- **3D-printed mechanical components** from the `/CAD` directory in this repository.

### 2. Software Requirements

- **Operating System:** A Linux-based OS is required for `socketcan` support (e.g., Raspberry Pi OS, Ubuntu, Debian).
- **Python:** Python 3.7 or newer.
- **Python Libraries:**
  - `python-can`
  - `mks-servo-can` (via custom repository)
  - `tkinter` (usually included with Python standard installations).

### 3. Installation and Setup

#### Step 1: Hardware Connection

1. **Connect the Servo:** Wire the `CAN_H` and `CAN_L` pins from your servo to the corresponding pins on your CAN interface.
2. **Power the Servo:** Connect the servo's power input (`V+`, `GND`) to your power supply. **Do not** power the servo from your host computer's logic pins.
3. **Terminate the Bus:** Place a 120 Ohm resistor across the `CAN_H` and `CAN_L` terminals. This is typically only needed at the two physical ends of the CAN bus.

#### Step 2: System CAN Configuration

For Linux systems using `socketcan` (which is the most common way to use CAN-to-USB adapters):

1. **Connect the Adapter:** Plug your CAN-to-USB adapter into your computer.

2. **Identify the Adapter's Device Name:** The system should automatically recognize the adapter. You can find its name by listing serial devices. It will often appear as `ttyACM0` or `ttyUSB0`.
   ```bash
   ls /dev/ | grep -E 'ttyACM|ttyUSB'
   ```

3. **Bring up the CAN interface.** Use the `slcand` utility to attach a network interface to your serial device. Replace `ttyACM0` with your device name and `can0` with your desired interface name.
   ```bash
   sudo slcand -o -c -s8 /dev/ttyACM0 can0
   ```
   Then, set the bitrate (bus speed) for the new interface. The script is configured for 500000.
   ```bash
   sudo ip link set can0 up type can bitrate 500000
   ```

4. **Verify the interface.** You can check if the interface is up by running `ifconfig can0` or `ip -details link show can0`.

#### Step 3: Python Environment & Libraries

1. It is highly recommended to use a Python virtual environment.
   ```bash
   python3 -m venv servo_env
   source servo_env/bin/activate
   ```

2. Install `python-can`:
   ```bash
   pip install python-can
   ```

3. Clone and install the required `mks-servo-can` library from your repository:
   ```bash
   git clone [https://github.com/Gacp45/mks-servo-can.git](https://github.com/Gacp45/mks-servo-can.git)
   cd mks-servo-can
   pip install .
   cd ..
   ```

### 4. Script Configuration

Before running the control software, open the Python script (e.g., `servo_control_panel.py`) and review the **Configuration Constants** section at the top.

- `CAN_INTERFACE`: Should be `"socketcan"` for most Linux setups.
- `CAN_CHANNEL`: Should be `"can0"` (or whatever name you assigned in Step 2.3).
- `SERVO_CAN_ID`: **Crucial.** This must match the ID configured on your servo. The default is `1`.
- `GEAR_RATIO`: **Crucial.** Set this to the exact ratio of your gearbox (e.g., `17.0` for a 17:1 ratio).
- `CALIBRATION_FEEDBACK_MAP`: This is the most important part of the configuration for accurate angle feedback. **You must calibrate this for your setup.**

### 5. Calibration Guide

The servo's encoder reports its position in raw units, and the scaling of these units changes with the subdivision (microstepping) setting. To get an accurate angle display, you must calibrate the conversion factor for each subdivision you intend to use.

**How to Calibrate:**

1. **Run the script:** `python3 servo_control_panel.py`.
2. **Connect** to the servo using the GUI.
3. **Select a Subdivision Code** from the dropdown menu that you want to calibrate (e.g., `16`).
4. **Press "Set Zero (Logical)".** This resets the script's internal position reference.
5. **Command a large, precise move.** Enter a large angle in the "Output Angle (°)" box. Using a multiple of 360 is best. For example, enter `3600` (which is 10 full output shaft rotations). Press **"Set Angle"**. Wait for the motor to stop moving.
6. **Check the Console Output.** The script will be printing status lines to the terminal. Find the last `AngleCalc` line. It will look something like this:
   ```
   AngleCalc (L...): RawLibVal=..., LibOffset=..., ..., Output=RawRel: 621560
   ```
   When the script is uncalibrated for the current subdivision, the output is shown as `RawRel`. This is the number you need. In this example, the value is `621560`.
7. **Calculate the Factor.** The formula is:
   `factor = total_raw_units / (total_output_degrees * GEAR_RATIO)`
   Using our example:
   `factor = 621560 / (3600 * 17.0) = 621560 / 61200 = 10.1562...`
   This factor is the `feedback_units_per_motor_degree`.
8. **Update the Script.** Open `servo_control_panel.py` and update the `CALIBRATION_FEEDBACK_MAP` with your new value.
   ```python
   CALIBRATION_FEEDBACK_MAP = {
       1:   15941.0 / 360.0,
       # ... other values
       16:  10.1562, # Your newly calculated value
       # ...
   }
   ```
   *Note: For higher accuracy, you can leave it as a fraction: `621560 / 61200.0`.*
9. **Repeat** for every subdivision code you plan to use.

### 6. Running the Application

1. Clone this repository (if you haven't already):
   ```bash
   git clone [https://github.com/Gacp45/Low-cost-Precision-rotation-Stage-for-CAL-Project.git](https://github.com/Gacp45/Low-cost-Precision-rotation-Stage-for-CAL-Project.git)
   ```
2. Navigate to the directory containing the control script:
   ```bash
   cd Low-cost-Precision-rotation-Stage-for-CAL-Project/Firmware
   ```
3. Run the control interface:
   ```bash
   python3 "Rotation Stage control V1.py"
   ```
The GUI will open. Use the interface to connect, home, rotate, and configure the motor.

### 7. Troubleshooting

- **Problem:** Cannot connect to CAN bus
  - **Solution:** Ensure correct wiring, termination, and that `can0` is up. Use `candump can0` for debugging.
- **Problem:** Motor doesn’t move
  - **Solution:** Check if E-STOP is active, verify speed/acceleration, confirm the motor is powered.
- **Problem:** Inaccurate Angle Display
  - **Solution:** The most common cause is an incorrect or missing calibration value in `CALIBRATION_FEEDBACK_MAP`. Re-run the calibration process for the current subdivision. Ensure `GEAR_RATIO` is set correctly.
- **Problem:** Library errors
  - **Solution:** Make sure `mks-servo-can` is installed correctly from the specified repository.

---

## Contributing

Contributions are welcome. Please open an issue or submit a pull request for bug fixes or improvements.

---

## License

This project is released under the MIT License. See `LICENSE` for details.

---

## Contact

For questions, support, or collaboration, please contact [Gabriel Pierce](https://github.com/Gacp45) or open a GitHub issue.
