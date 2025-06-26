# Low-Cost, High-Torque Cycloidal Rotation Stage

This repository contains the complete design files, software, and documentation for a low-cost, 3D-printed, high-precision motorised rotation stage. The project was developed as part of a Master of Engineering Project at NMITE.

[cite_start]The primary motivation for this project is the high cost of commercial rotation stages, which presents a significant barrier to entry for researchers, educators, and enthusiasts in fields like optical automation and volumetric additive manufacturing (VAM), such as Computed Axial Lithography (CAL). This open-source design aims to provide a viable alternative that replicates the core functionality of commercial systems for a fraction of the price.

![Image of the assembled rotation stage](your_image_of_the_stage.jpg)
*(Recommendation: Insert an image of your final prototype here)*

## Key Features & Performance

This design was optimised to balance performance, cost, and ease of fabrication using standard FDM 3D printers.

- [cite_start]**Drive System:** 3D-Printed Cycloidal Drive with a **17:1** reduction ratio, providing high torque in a compact package.
- [cite_start]**Motor Control:** NEMA 17 stepper motor with an integrated **MKS SERVO42D closed-loop controller**, ensuring no steps are lost during operation.
- [cite_start]**High Torque:** The drive system was experimentally measured to produce a peak output torque of **1.47 Nm**.
- [cite_start]**Practical Repeatability:** Achieved an average unidirectional repeatability of **0.024°** across its optimal operating range (half-step and quarter-step modes).
- [cite_start]**Low Cost:** The total bill of materials (BOM) for the prototype is estimated at **under £200**, representing an 85%+ cost saving over commercial alternatives.
- [cite_start]**Control Interface:** Includes a Python-based GUI developed with Tkinter for real-time control, communicating with the motor via a CAN bus interface.

## Repository Contents

This repository is structured as follows:

-   **/CAD:** Contains all `.STL` files required for 3D printing the components, as well as the source CAD files (e.g., `.STEP`, `.f3d`) for modification.
-   **/Software:** Contains the Python control software, including the Tkinter GUI (`display fix, pulses v2.py`) for manual control and any scripts used for automated performance testing.
-   **/Docs:** Includes detailed assembly instructions, an electronics wiring diagram, and a full Bill of Materials (BOM).
-   `README.md`: This file.

## Getting Started

### 1. Mechanical Assembly

All parts can be printed in PETG on a standard FDM 3D printer with minimal supports. For detailed slicer settings and a step-by-step assembly guide, please refer to the documents in the `/Docs` folder.

### 2. Electronics and Wiring

The system uses a Raspberry Pi 4 to run the control software, connected to the MKS SERVO42D via a USB-to-CAN adapter. Please see the wiring diagram in the `/Docs` folder for specific pin connections.

### 3. Software Setup

The control software is written in Python 3.

```bash
# Clone this repository
git clone [your-repository-url]
cd [your-repository-name]

# Install required Python libraries
pip install -r requirements.txt

# Run the GUI
python3 Software/main_gui.py
