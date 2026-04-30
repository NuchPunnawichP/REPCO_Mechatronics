# Acoustic Emission (AE) Analyzer

A powerful, automated diagnostic tool for analyzing acoustic emission signals and detecting mechanical anomalies through predictive maintenance. Built in collaboration with SCGC and REPCO for microprocessor-based signal processing and fault detection.

![Status](https://img.shields.io/badge/status-stable-brightgreen) ![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows-blue) ![License](https://img.shields.io/badge/license-REPCO-blue)

---

## 📺 Quick Start: Video Tutorials

Get up and running in minutes with platform-specific guides:

| Platform | Tutorial |
|----------|----------|
| **macOS** | [![Watch Tutorial](https://img.youtube.com/vi/nZWQwkJuh4c/hqdefault.jpg)](https://youtu.be/nZWQwkJuh4c) |
| **Windows** | [![Watch Tutorial](https://img.youtube.com/vi/ny41qq3ACQI/hqdefault.jpg)](https://youtu.be/ny41qq3ACQI) |

*Click either image above to watch the complete installation and usage walkthrough.*

---

## 🚀 Installation

### macOS Users

1. **Download** the latest `AE_Analyzer.zip` from the repository
2. **Extract** by double-clicking the `.zip` file
3. **Move** `AE_Analyzer.app` to your `Applications` folder (or Desktop)
4. **First Launch Only:**
   - Right-click (or Control-click) `AE_Analyzer.app`
   - Select **Open** from the context menu
   - Click **Open** on the security prompt that appears
   - This only needs to be done once—macOS will remember your choice

### Windows Users

1. **Download** the latest `AE_Analyzer.exe` from the repository
2. **Run** the installer and follow the on-screen prompts
3. **Launch** from your Start Menu or Desktop shortcut
4. No administrator privileges required

---

## 📖 How to Use

1. **Launch** the application
2. **Load Files** → Click "1. Load .bin Files" and select your binary data files
3. **Select** → Use the dropdown menu to pick a specific file to analyze
4. **Analyze** → Click "3. Compute & Plot"
5. **Review** → Scroll down to read the **Automated Diagnostic Report**

The app automatically:
- Converts 16-bit binary data from your 12-bit ADC
- Computes acoustic emission features (RMS, Peak, Counts)
- Generates spectrogram and time-domain plots
- Detects anomalies and equipment wear
- Produces a human-readable diagnostic summary

---

## 🔧 Features & Controls

### Plot Range Adjustments

Fine-tune visualization to match your equipment and signal characteristics:

| Control | Purpose |
|---------|---------|
| **Spectrogram dB Range** | Adjust min/max color scale (dBFS) for spectrogram detail |
| **RMS Max** | Set Y-axis ceiling for RMS trend plot |
| **Peak Max** | Set Y-axis ceiling for peak amplitude plot |
| **Window Counts Max** | Set Y-axis ceiling for per-window event counts |
| **Cumulative Counts Max** | Set Y-axis ceiling for total event history |
| **AE Threshold (dBAE)** | Define sensitivity for acoustic event detection |

Click **"Apply Colors"** or **"Apply Ranges & Recalculate Counts"** to update plots.

---

## 📊 Understanding the Output

### Five Diagnostic Plots

1. **Spectrogram (dBFS)**
   - Time-frequency visualization of signal energy
   - Color intensity = signal strength at each frequency
   - Identifies dominant frequency bands and transient events

2. **RMS Trend**
   - Continuous energy level over time
   - Flat line = stable operation
   - Rising trend = progressing wear or anomaly

3. **Peak Amplitude Trend**
   - Maximum transient impacts in each time window
   - Sudden spikes = potential equipment failure indicators
   - Used to compute Crest Factor for signal classification

4. **Count at Time (Per Window)**
   - Bar chart of acoustic events per analysis window
   - Height = number of events exceeding threshold
   - Clustered bars = burst emissions; sparse bars = continuous emissions

5. **Sum Count at Time (Cumulative)**
   - Running total of all detected acoustic events
   - Steep rise = increasing fault activity
   - Plateau = stable equipment condition

### Automated Diagnostic Report

The report includes:
- **Signal Classification** → Burst vs. Continuous emission detection
- **Energy Trend** → Increasing, decreasing, or stable wear patterns
- **Total Counts** → Cumulative acoustic events detected
- **Anomaly Detection** → Windows with significant high-energy spikes
- **Maximum Peak** → Highest transient energy and when it occurred

---

## 🧮 Technical Foundation

### Signal Processing Pipeline

The application processes 16-bit binary data from a 12-bit ADC (3.3V reference):

**Step 1: Convert to Voltage**
```
V_real = (Data_ADC / 4096) × 3.3V
V_centered = V_real - mean(V_real)
```

**Step 2: Extract Time-Window Features**
- **RMS:** Represents continuous energy/friction
- **Peak:** Represents maximum transient impact energy
- **AE Counts:** Number of threshold-crossings per window

**Step 3: Automated Diagnostics**
- **Crest Factor (CF = Peak / RMS)**
  - High CF (>4.0) → Burst emissions (cracks, pitting)
  - Low CF (<4.0) → Continuous emissions (friction, wear)
- **Trend Analysis**
  - Rising RMS slope → Increasing equipment wear
  - Stable slope → Normal operation
- **Anomaly Detection**
  - Dynamic thresholding identifies critical high-energy events

### Threshold Configuration

The **AE Threshold** controls detection sensitivity:
- **0 dBAE** = 1 µV (very sensitive; detects light friction)
- **40 dBAE** = 100 µV (moderate; standard bearing monitoring)
- **80 dBAE** = 10 mV (coarse; severe damage detection)

Adjust based on your equipment's baseline noise characteristics.

---

## 🔐 Security & Architecture

### Why This App is Safe

**PyInstaller "Freezer" Design**
- The executable bundles the official CPython interpreter + required libraries
- No compilation, no obfuscation, no hidden code
- Your exact `app.py` script runs transparently inside the bundle

**Complete Open-Source Transparency**
- Review the `app.py` source code in this repository
- Mathematically certain the executable performs only the stated operations
- No network requests, no telemetry, no malware

**User-Space Execution**
- Runs entirely in user space (no admin/root required)
- Does not modify system registries or install services
- Leaves no permanent footprint; temp files are cleaned on exit

**Institutional Review Ready**
- IT administrators and security teams can inspect the source code
- Suitable for academic, research, and industrial environments
- REPCO, SCGC, and institutional deployments approved

---

## ⚙️ System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **macOS** | 10.14+ | 12.0+ |
| **Windows** | Windows 10 (21H2) | Windows 11 |
| **RAM** | 2 GB | 4 GB+ |
| **Disk Space** | 100 MB | 500 MB |
| **Python** | Not needed (bundled) | N/A |

---

## 🐛 Troubleshooting

### macOS: "Cannot open application" Error
**Solution:** Right-click → Open, then click "Open" on the security prompt. This must be done once per app update.

### Windows: "File not found" or "Access Denied"
**Solution:** Ensure binary files are in an unprotected folder (Desktop, Documents). Avoid Program Files or OneDrive directories.

### Plots not updating or showing "Waiting for file..."
**Solution:** 
1. Load files via "1. Load .bin Files"
2. Select a file from the dropdown
3. Click "3. Compute & Plot"
4. Wait for the processing message to complete

### Application crashes on large files
**Solution:** Reduce overlap parameter or increase time window size in settings (advanced mode).

---

## 📝 File Format

The analyzer expects 16-bit unsigned integer binary files (`.bin`):
- **Data Type:** uint16 (unsigned 16-bit integer)
- **Sample Rate:** 4000 Hz (default; user adjustable)
- **ADC Bits:** 12-bit (4096 levels)
- **Reference Voltage:** 3.3V

Example file creation in Python:
```python
import numpy as np

# Generate 1 second of sample data at 4000 Hz
data = np.random.randint(0, 4096, 4000, dtype=np.uint16)
data.tofile('sample_signal.bin')
```

---

## 🤝 Support & Collaboration

Developed in collaboration with:
- **SCG REPCO** – Automotive diagnostics and predictive maintenance and Signal processing and sensor integration

For technical support, feature requests, or bug reports, contact the development team.

---

## 📚 Learn More

- Review the source code at `app.py` for detailed algorithm implementation
- Watch the video tutorials (links at top) for step-by-step guidance
- Consult the automated diagnostic reports for equipment-specific insights
- Experiment with threshold settings to tune sensitivity for your machinery

---

**Ready to analyze?** Download, install, and launch the AE Analyzer. Your equipment's health metrics are just a few clicks away.
