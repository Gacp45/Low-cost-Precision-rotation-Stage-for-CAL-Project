# Low-Cost Precision Rotation Stage for CAL

<div align="center">
  <h3 align="center">Low-Cost Precision Rotation Stage</h3>
  <p align="center">
    An open-source, 3D-printed, high-precision motorised rotation stage for Computed Axial Lithography (CAL) and other optical automation tasks.
    <br />
    <a href="https://github.com/Gacp45/Low-cost-Precision-rotation-Stage-for-CAL-Project/issues">Report Bug</a>
    ·
    <a href="https://github.com/Gacp45/Low-cost-Precision-rotation-Stage-for-CAL-Project/issues">Request Feature</a>
  </p>
</div>

<!-- BADGES -->
<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#about-the-project">About The Project</a></li>
    <li><a href="#bill-of-materials">Bill of Materials</a></li>
    <li><a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a>
        <ul>
        <li><a href="#script-configuration">Script Configuration</a></li>
        <li><a href="#calibration-guide">Calibration Guide</a></li>
        <li><a href="#running-the-application">Running the Application</a></li>
      </ul></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#troubleshooting">Troubleshooting</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

---

## About The Project

![Project Screenshot](https://raw.githubusercontent.com/Gacp45/Low-cost-Precision-rotation-Stage-for-CAL-Project/main/Images/render.png)

This repository contains the complete design files, software, and documentation for a low-cost, 3D-printed, high-precision motorised rotation stage. The project was developed as part of a Master of Engineering Project at NMITE.

### Why This Project?

The primary motivation for this project is the high cost of commercial rotation stages, which presents a significant barrier to entry for researchers, educators, and enthusiasts in fields like optical automation and volumetric additive manufacturing (VAM), such as Computed Axial Lithography (CAL). This open-source design aims to provide a viable alternative that replicates the core functionality of commercial systems for a fraction of the price.

This project provides a complete, end-to-end solution, from the 3D-printable mechanical parts to the control software, enabling users to build and operate their own precision rotation stage.

### Key Features:
* **Precision Rotation Stage:** Uses a geared stepper motor (MKS SERVO42D) for high-precision control.
* **GUI Control Panel:** An intuitive interface built with Tkinter for easy operation.
* **Real-time Feedback:** Displays the current output angle in degrees, calculated from live encoder data.
* **Dynamic Configuration:** Adjust speed, acceleration, and microstepping settings on the fly.
* **Stall-Based Homing:** Initiate the servo's built-in sensorless homing sequence.
* **Emergency Stop:** Immediately halt all motor activity for safety.

---

## Bill of Materials

### 3D-Printed Parts

All parts can be printed in PETG. The estimated print times and material usage are based on standard print settings. All `.stl` files can be found in the `/CAD` directory.

| Part ID | Part Name | Quantity | Est. Print Time (hrs) | Est. Material (g) |
|---|---|:---:|:---:|:---:|
| A | Outer Housing | 1 | 6 | 100 |
| B | Bottom Output Flange | 1 | 1.5 | 20 |
| C | Input Shaft | 1 | 0.5 | 5 |
| D | Eccentric Shaft | 2 | 0.25 (Each) | 4.30 (Each) |
| D-Spacer | Eccentric Shaft Spacer | 1 | 0.1 | 1.11 |
| E | Motor Shaft Coupler | 1 | 0.5 | 4.27 |
| F | Top Output Flange | 1 | 2.2 | 26 |
| G | Motor Mount | 1 | 3.1 | 38 |
| H-1 | Output Bearing Shaft | 6 | 1.5 | 4.2 |
| H-2 | Output Bearing Spacer | 12 | 0.6 | 1.68 |
| I | Cycloidal Disk | 2 | 4.25 | 57.9 |
| I-2 | Bearing Cage (Cycloidal) | 2 | 0.14 | 1.34 |
| J-1 | Outer Housing (Top) | 1 | 5.5 | 66.44 |
| J-2 | Bearing Cage (Top) | 1 | 0.06 | 0.64 |
| Roller-A | Roller Shaft | 18 | 1.08 | 2.34 |
| Roller-B | Roller Shaft Spacer S | 18 | 0.54 | 1.08 |
| Roller-C | Roller Shaft Spacer M | 18 | 0.9 | 1.44 |
| Roller-D | Roller Shaft Spacer B | 18 | 1.8 | 3.42 |
| A-B Cage | Bearing Cage (A-B) | 1 | 0.15 | 0.95 |
| B-C Cage | Bearing Cage (B-C) | 1 | 0.18 | 1 |
| **Total** | | | **~30.85** | **~336.81** |

### Off-the-Shelf Parts

**(This section is ready for you to add your list of non-printed components, such as screws, bearings, the motor, and the CAN adapter.)**

---

## Getting Started

This section will guide you through setting up the project from scratch.

### Prerequisites

Before you begin, ensure you have all the necessary hardware and software.

#### Hardware Requirements
* **MKS SERVO42D** stepper motor with CAN bus interface.
* **A host computer with a CAN interface.** Common options include:
  * A CAN-to-USB adapter (e.g., CANable, USBtin, PCAN-USB).
  * A Raspberry Pi with a CAN bus HAT.
* **A stable Power Supply** for the servo (typically 12V to 24V DC).
* **CAN Bus Wiring:**
  * A twisted pair of wires for `CAN_H` and `CAN_L`.
  * A **120 Ohm termination resistor** at the end of the bus.
* **3D-printed mechanical components** from the `/CAD` directory.

#### Software & Library Requirements
* **Operating System:** A Linux-based OS with `socketcan` support (e.g., Raspberry Pi OS, Ubuntu, Debian).
* **Python:** Python 3.7 or newer.
* **Python Libraries:** You will need `python-can` and a specific version of `mks-servo-can`. These will be installed in the next step.

### Installation

1. **Download Project Files**
   There are two ways to get the project files:
   - **(Recommended) From Releases:** Download a stable, packaged `.zip` version from the [**Releases Page**](https://github.com/Gacp45/Low-cost-Precision-rotation-Stage-for-CAL-Project/releases).
   - **(For Developers) Clone the Repo:**
     ```bash
     git clone [https://github.com/Gacp45/Low-cost-Precision-rotation-Stage-for-CAL-Project.git](https://github.com/Gacp45/Low-cost-Precision-rotation-Stage-for-CAL-Project.git)
     ```

2. **Set up Python Environment**
   It's highly recommended to use a Python virtual environment.
   ```bash
   python3 -m venv servo_env
   source servo_env/bin/activate
   ```

3. **Install Required Libraries**
   Install `python-can` and the custom `mks-servo-can` library.
   ```bash
   pip install python-can
   git clone [https://github.com/Gacp45/mks-servo-can.git](https://github.com/Gacp45/mks-servo-can.git)
   cd mks-servo-can
   pip install .
   cd ..
   ```

4. **Hardware Connection & System Setup**
   - **Connect Hardware:** Wire the `CAN_H` and `CAN_L` pins from your servo to your CAN interface, and connect the servo to its power supply.
   - **Configure CAN Interface (for CAN-to-USB):**
     1. Identify your adapter's device name (e.g., `ttyACM0`):
        ```bash
        ls /dev/ | grep -E 'ttyACM|ttyUSB'
        ```
     2. Attach a network interface and set the bitrate to 500000:
        ```bash
        sudo slcand -o -c -s8 /dev/ttyACM0 can0
        sudo ip link set can0 up type can bitrate 500000
        ```
     3. Verify with `ifconfig can0`.

---

## Usage

Once the setup is complete, you need to configure the script for your specific hardware and calibrate it for accurate readings.

### Script Configuration

Before running the control software, open the Python script (`Firmware/Rotation Stage control V1.py`) and review the **Configuration Constants** section at the top.

- `CAN_INTERFACE`: Should be `"socketcan"` for most Linux setups.
- `CAN_CHANNEL`: Should be `"can0"` (or whatever name you assigned during setup).
- `SERVO_CAN_ID`: **Crucial.** This must match the ID configured on your servo (default is `1`).
- `GEAR_RATIO`: **Crucial.** Set this to the exact ratio of your gearbox (e.g., `17.0` for a 17:1 ratio).
- `CALIBRATION_FEEDBACK_MAP`: This map is essential for accurate angle feedback. **You must calibrate this for your setup.**

### Calibration Guide

To get an accurate angle display, you must calibrate the conversion factor for each subdivision setting you intend to use.

1. **Run the script** and **connect** to the servo via the GUI.
2. **Select a Subdivision Code** you want to calibrate (e.g., `16`).
3. **Press "Set Zero (Logical)"**.
4. **Command a large, precise move.** Enter a large angle like `3600` (10 full output rotations) and press **"Set Angle"**.
5. **Check the Console Output** for the `AngleCalc` line. When uncalibrated, it will show `Output=RawRel: <number>`. You need this number.
   ```
   AngleCalc (L...): RawLibVal=..., LibOffset=..., ..., Output=RawRel: 621560
   ```
6. **Calculate the Factor** using the formula: `factor = total_raw_units / (total_output_degrees * GEAR_RATIO)`.
   - Example: `621560 / (3600 * 17.0) = 10.1562...`
7. **Update the Script.** Open the Python script and add your new factor to the `CALIBRATION_FEEDBACK_MAP`.
   ```python
   CALIBRATION_FEEDBACK_MAP = {
       16:  10.1562, # Your newly calculated value
       # ... other values
   }
   ```
8. **Repeat** for every subdivision code you plan to use.

### Running the Application

Navigate to the `Firmware` directory and run the control interface:
```bash
cd Low-cost-Precision-rotation-Stage-for-CAL-Project/Firmware
python3 "Rotation Stage control V1.py"
```
The GUI will open, allowing you to connect, home, and control the motor.

---

## Roadmap

This is the first iteration of this project, laying the groundwork for future enhancements.
- [ ] Refine the calibration process to be more automated.
- [ ] Add support for saving and loading different configuration profiles.
- [ ] Improve error handling and provide more descriptive feedback in the GUI.
- [ ] Develop a more comprehensive test suite for validating performance.
- [ ] Developing a image sequence complete with motor synchronisation.

See the [open issues](https://github.com/Gacp45/Low-cost-Precision-rotation-Stage-for-CAL-Project/issues) for a full list of proposed features (and known issues).

---

## Troubleshooting

- **Problem:** Cannot connect to CAN bus
  - **Solution:** Ensure correct wiring, termination, and that `can0` is up. Use `candump can0` for debugging.
- **Problem:** Motor doesn’t move
  - **Solution:** Confirm the motor is powered. Refer to the Motors Datasheet and the MKS SERVO42D User Manual to verify the wiring is correct.
- **Problem:** Inaccurate Angle Display
  - **Solution:** The most common cause is an incorrect or missing calibration value in `CALIBRATION_FEEDBACK_MAP`. Re-run the calibration process.

---

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

This project is released under the MIT License. See `LICENSE` for details.

---

## Contact

Gabriel Pierce - [GitHub Profile](https://github.com/Gacp45)

Project Link: [https://github.com/Gacp45/Low-cost-Precision-rotation-Stage-for-CAL-Project](https://github.com/Gacp45/Low-cost-Precision-rotation-Stage-for-CAL-Project)
