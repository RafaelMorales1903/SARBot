# SARBot
This project transforms a standard LAFVIN Raspberry Pi car into an autonomous search and rescue robot. Key enhancements over the base model include the integration of a local AI-powered object detection system that operates without internet connectivity, enabling the identification of people, cats, and dogs, Telegram notification system, a two-way audio system for real-time communication with survivors, and a thermal camera to assess their condition.

**Key Features:**

- AI Object Detection: Uses computer vision to identify people, cats, and dogs.
- Telegram Alerts: When the robot detects a person, dog, or cat
- Two-Way Audio: Enables real-time communication between a remote operator and a survivor, acting as a mobile walkie-talkie.
- Thermal Camera: Detects body heat signatures to help determine if a victim is alive.
- Base Platform: Built upon the 4WD LAFVIN Raspberry Pi car

## AI-Powered Control Core (`mainv3.py`)

The core control script (`mainv3.py`) has been significantly enhanced beyond the original LAFVIN car implementation. It now orchestrates both the robot's hardware and an on-device AI server.

### Key Enhancements

- **Autonomous AI Server Management**: The script automatically starts the [CodeProject.AI Server](https://github.com/codeproject/CodeProject.AI-Server) using `podman` containers. It intelligently checks if the container exists, starts it if stopped, and restarts it if needed—all with retry logic for robustness.

- **AI Readiness Probing**: Before the robot is considered operational, the script actively pings the AI server's status endpoint (`http://localhost:32168/v1/status`) to ensure it's fully loaded and ready to process inference requests. This prevents race conditions where detection commands might fail.

- **Audible Status Feedback**: The buzzer has been upgraded from a simple "startup" beep to a full status communication system. Different beep patterns now indicate:
  - AI container startup attempts
  - Successful AI server readiness
  - AI server failure (server continues without AI)
  - Server shutdown

- **Graceful Container Management**: Uses `podman` (rootless container engine) to manage the AI server, keeping the host system clean and avoiding dependency hell. The container runs alongside the car's main processes without interference.

### How It Works

1. **Initialization**:
   - The script starts with a single beep to indicate startup.
   - It then attempts to start the CodeProject.AI container (retries up to 3 times with increasing delays).
   - While the container starts, it polls the status API every 2 seconds for up to 90 seconds.

2. **Fallback Behavior**:
   - If the AI server fails to start after all retries, the script emits three rapid beeps and continues running without AI.
   - The TCP server and camera streaming still function, but AI detection features will be unavailable.

3. **TCP Server Integration**:
   - After AI handling completes, the original LAFVIN TCP server starts normally (`StartTcpServer()`).
   - The three main threads (`readdata`, `sendvideo`, `Power`) run alongside the AI container.

4. **Shutdown**:
   - When stopped (via `SIGTERM`, `SIGINT`, or `SIGUSR1`), the script emits two long beeps and cleans up resources.
   - The CodeProject.AI container is *not* stopped automatically—it remains available for future sessions (improves startup time).

### CodeProject.AI Server Integration

This project uses [CodeProject.AI Server](https://github.com/codeproject/CodeProject.AI-Server) as the inference engine for object detection (people, cats, dogs). The server is:

- **Self-hosted**: Runs entirely on the Raspberry Pi—no cloud dependency.
- **Containerized**: Managed via `podman` for easy installation and updates.
- **Accessed via REST API**: The car sends images to `http://localhost:32168/v1/vision/detection` and receives JSON results.

The AI server must be installed separately (see [Installation](https://github.com/codeproject/CodeProject.AI-Server)). The control script only manages its container lifecycle.

## Real‑Time Object Detection (`server.py`)

The video streaming server (`server.py`) now runs **asynchronous object detection** on every frame using [CodeProject.AI Server](https://github.com/codeproject/CodeProject.AI-Server). It identifies **people, dogs, and cats** without blocking the video stream or car controls.

**Key features:**
- **Non‑blocking pipeline** – Detection runs in a separate thread with a single‑frame queue (drops stale frames to keep latency low).
- **Smart frame skipping** – Only the latest frame is processed; old results are discarded if they arrive after 3 seconds.
- **Automatic actions** – When a person is detected, the LED flashes red and the buzzer beeps. For dogs/cats, the LED flashes green.
- **Evidence saving** – Detected objects are saved as JPEG images in `/tmp/` with bounding boxes and confidence scores.
- **Cooldown** – Prevents repeated alerts for the same object within 5 seconds.
- **Low‑latency optimisation** – Frames are resized to 320×240 and JPEG quality is reduced to 60% before sending to the AI server.

**How it works:**
1. The `StreamingOutput` class (extended with a second condition) provides both the main video stream and a separate copy for AI processing.
2. A dedicated thread (`ai_detection_loop`) calls `detect_objects()` every 50 ms.
3. Each frame is converted to OpenCV format, resized, and posted to `http://localhost:32168/v1/vision/detection`.
4. Responses are processed asynchronously; detected objects trigger the configured actions and save images.

This integration adds **autonomous visual intelligence** to the robot, allowing it to react to survivors or pets without manual intervention.

## Telegram Alerts

When the robot detects a person, dog, or cat, it saves an image with a bounding box to `/tmp/`.  
A separate Bash script (`telegram/send_detections.sh`) can be run periodically (e.g., via `cron`) to forward these images to a Telegram group.

- **Instant notifications** – Get visual confirmation of what the robot sees.
- **Non‑intrusive** – Moves processed images to `/tmp/processed/` to avoid duplicate sends.
- **Easy to set up** – Just add your bot token and chat ID.

See [`telegram/README.md`](telegram/README.md) for setup and automation instructions.

## Two‑Way Audio - Hermes

Hermes is a real‑time, full‑duplex audio communication system that turns your rescue robot into a mobile walkie‑talkie.  
It allows a remote operator to speak with a survivor (and hear them back) without any third‑party services.

- **Server (on the robot)**
 Captures audio from a USB microphone, streams it to the operator, and plays back incoming audio through a speaker.  
  It also monitors sound levels and prints an alert when a loud noise (e.g., a cry for help) is detected.

- **Client (on your laptop / controller)**
Connects to the robot, sends your voice to the robot’s speaker, and plays back any sound the robot’s microphone picks up.

Both components use **TCP sockets** and **PyAudio** for low‑latency audio streaming.  
The system is completely self‑contained and no internet required, works on a local network.

Full code, setup instructions, and usage examples are available in the [`hermes/`](hermes/) folder.

## Thermal Imaging & Victim Assessment (AMG8833)
The thermal camera module provides the SARBot with the ability to "see" heat signatures, which is critical for locating survivors in low-visibility environments or determining if a detected person has a vital heat signature.

### Key Features
- **Thermal Heat Mapping:** Uses an AMG8833 Grid-EYE sensor to detect infrared radiation and convert it into a temperature-based visual matrix.
- **Enhanced Resolution:** Implements **Bicubic Interpolation** to upscale the raw 8x8 sensor data into a smooth 32x32 heatmap, providing a much clearer image for the operator.
- **Real-Time Visualization:** Uses the 'Inferno' colormap for high-contrast thermal imaging, allowing for quick identification of body heat against colder backgrounds.
- **Dynamic Range Scaling:** Automatically adjusts the color scale's sensitivity based on the environment's minimum and maximum temperatures to ensure the survivor is always visible.

### How It Works
1. **I2C Data Acquisition:** The system polls the AMG8833 sensor via I2C, reading 128 bytes of raw data per frame.
2. **Processing Pipeline:**
   - Raw bytes are converted into Celsius values with 0.25°C precision.
   - The data is reshaped into an 8x8 matrix.
   - `scipy.interpolate` is used to generate a high-resolution grid, filling in the gaps between the physical sensor pixels.
3. **Continuous Monitoring:** The script runs in a dedicated loop, refreshing the thermal display in real-time alongside the robot's main AI and video streams.

This module adds a layer of **life-detection capability**, allowing rescuers to differentiate between a static object and a living survivor based on thermal radiation.