# Low-Cost Precision Rotation Stage for Computed Axial Lithography (CAL)

This repository contains the hardware, firmware, and software for a low-cost, high-precision rotation stage designed for Computed Axial Lithography (CAL). The system uses an MKS SERVO42D smart stepper motor and is controlled via a Python-based GUI over a CAN bus interface.

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

## Hardware Requirements

- MKS SERVO42D stepper motor with CAN bus interface
- CAN-to-USB adapter (e.g., MCP2515, CANable, USBtin)
- Raspberry Pi or Linux PC with SocketCAN support
- Properly terminated CAN bus wiring
- Power supply (12–24V depending on motor specs)
- 3D-printed mechanical components from `CAD/`

---

## Software Requirements

- Linux-based OS with CAN bus support
- Python 3.7 or later
- Python packages:
  ```bash
  pip install python-can
  ```

- Clone and install the `mks_servo_can` library:
  ```bash
  git clone https://github.com/Gacp45/mks-servo-can.git
  cd mks-servo-can
  pip install .
  ```

---

## CAN Bus Setup

To enable the CAN interface on a Linux device:

```bash
sudo ip link set can0 up type can bitrate 500000
sudo ifconfig can0 up
```

Verify with:

```bash
ifconfig can0
```

To monitor CAN messages (optional):

```bash
candump can0
```

---

## Running the GUI

1. Clone this repository:
   ```bash
   git clone https://github.com/Gacp45/Low-cost-Precision-rotation-Stage-for-CAL-Project.git
   ```

2. Navigate to the firmware directory:
   ```bash
   cd Low-cost-Precision-rotation-Stage-for-CAL-Project/Firmware
   ```

3. Run the control interface:
   ```bash
   python3 "Rotation Stage control V1.py"
   ```

The GUI will open. Use the interface to connect, home, rotate, and configure the motor.

---

## Calibration

The script includes a predefined `CALIBRATION_FEEDBACK_MAP` used to convert raw encoder data into meaningful angle values. If using different subdivision settings or hardware, run a manual calibration routine and update the dictionary accordingly.

---

## Troubleshooting

**Problem:** Cannot connect to CAN bus  
**Solution:** Ensure correct wiring, termination, and that `can0` is up. Use `candump can0` for debugging.

**Problem:** Motor doesn’t move  
**Solution:** Check if E-STOP is active, verify speed/acceleration, confirm the motor is powered.

**Problem:** Library errors  
**Solution:** Make sure `mks_servo_can` is installed correctly and matches the expected API version.

---

## Contributing

Contributions are welcome. Please open an issue or submit a pull request for bug fixes or improvements.

---

## License

This project is released under the MIT License. See `LICENSE` for details.

---

## Contact

For questions, support, or collaboration, please contact [Gabriel Pierce](https://github.com/Gacp45) or open a GitHub issue.
