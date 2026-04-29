# Image-2-G-Code

Image to G-Code  - Technical Documentation

Image to G-Codeis a high-performance Image-to-G-code converter designed for GRBL-based laser engraving systems. The application provides a bridge between digital imagery and precision CNC machining, focusing on toolpath optimization, material-specific contrast handling, and machine safety.

Core Capabilities
Image Processing Engine
The software utilizes a sophisticated processing pipeline to prepare images for laser interaction. Key components include:

Luma-Based Gamma Correction: Adjusts mid-tone intensity to compensate for the non-linear burning characteristics of organic materials like wood and leather.

Dynamic Edge Sharpening: Applies localized contrast enhancement to ensure text and complex geometries remain defined during high-speed engraving.

Smart Background Sensing: Analyzes corner pixel data to detect dark frames, automatically inverting the image to preserve the workpiece background.

Automated Alpha Channel Management: Converts transparency data into absolute white (S0) to prevent unintended laser activation in PNG and layered assets.

Advanced G-Code Logic
LaserPro is engineered to produce efficient, safe, and compact G-code (NC files):

Safety Boundary Logic: The engine calculates a "Safety Origin" by offsetting the image on the X-axis by the user-defined Overscan value. This ensures all acceleration and deceleration maneuvers occur within the positive coordinate space (X >= 0), eliminating "Alarm: Hard Limit" errors.

Overscan Optimization: Moves the laser head beyond the image boundaries to allow the gantry to reach target velocity before the laser is triggered, preventing over-burned edges.

Serpentine Toolpaths: Implements bi-directional engraving (zigzag) to reduce non-productive travel time by approximately 50%.

S-Code Compression: The generator only outputs power changes, significantly reducing file size and serial buffer overhead on 8-bit and 32-bit controllers.

Technical Specifications
Architecture: Python 3.x

GUI Framework: PySide6 (Qt for Python)

Math Engine: NumPy

Imaging Library: Pillow (PIL)

G-Code Flavor: GRBL Compatible (M4 Dynamic Laser Power)

Coordinate System: Metric (G21) / Absolute (G90)

Operational Guide
1. Image Adjustments
Width (mm): Defines the physical horizontal scale. The vertical scale is calculated automatically to maintain the original aspect ratio.

Gamma: Fine-tunes the grayscale mapping. Higher values increase the "dwell time" equivalent for mid-tones.

Sharpness: Increases the transition gradient between light and dark pixels to combat the natural focal spot bleeding of the laser.

2. Machine Parameters
Max S: Defines the 100% power ceiling (typically 1000 for GRBL firmware).

Burn Speed (G1): The feed rate during active engraving. This directly affects the burn depth and darkness.

White Cutoff: A trimmable threshold that forces near-white pixels to S0, ensuring clean backgrounds and reducing mechanical wear.

Installation and Deployment
Development Environment
To run the source code, ensure the following dependencies are installed:
pip install PySide6 numpy pillow

License
This project is licensed under the MIT License - providing full freedom for personal and commercial use while requiring the preservation of the original copyright notice.
