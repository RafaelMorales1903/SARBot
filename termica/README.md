# Thermal Imaging System (AMG8833)

This module implements the acquisition and processing of infrared thermal data using the **AMG8833 Grid-EYE** sensor. The system transforms low-resolution raw data into a fluid, human-readable visual heatmap.

##  Technical Specifications

### 1. I2C Communication & Data Acquisition
The script utilizes the `smbus2` library to communicate with the sensor via the I2C protocol (address `0x69`).
- **Block Reading:** Since the sensor provides 128 bytes of data (64 pixels, 2 bytes each), the reading is performed in four 32-byte blocks to ensure data integrity.
- **Data Conversion:** Bytes are combined using bitwise operations (`all_data[i+1] << 8 | all_data[i]`) and multiplied by a **0.25°C** scaling factor as specified in the manufacturer's datasheet.

### 2. Image Processing (Bicubic Interpolation)
The AMG8833 sensor has a limited native resolution of **8x8 pixels**. To avoid a "pixelated" display, the code implements a **Bicubic Interpolation** algorithm using `scipy.interpolate.griddata`:
- **Upscaling:** A high-resolution **32x32 pixel** mesh is generated from the original 64 data points.
- **Smoothing:** The 'cubic' method calculates new pixel values based on the 16 surrounding pixels, creating smooth and realistic temperature gradients.

### 3. Real-Time Visualization
- **'Inferno' Colormap:** Utilizes a perceptually uniform color scale that makes identifying hot spots intuitive.
- **Dynamic Normalization:** The color range (`clim`) automatically adjusts in every frame based on the minimum and maximum detected temperatures, maximizing thermal contrast.

##  File Structure
* `camera_thermal.py`: Main Python script.
* `thermal.mmd`: Mermaid source code for the logic diagram.
* `thermal.svg`: Visual representation of the data flow.

