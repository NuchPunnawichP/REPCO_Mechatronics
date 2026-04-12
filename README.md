# REPCO Mechatronics: Acoustic Emission (AE) Analyzer

An automated Diagnostic and Decision Logic tool for Microprocessor-based Acoustic Emission (AE) Feature Processing. This project was developed in collaboration with SCGC and REPCO to process, analyze, and interpret mechanical AE signals for predictive maintenance and fault detection.

## 🚀 Overview

The AE Analyzer is a Python-based desktop application designed to process raw acoustic emission data gathered from industrial machinery. Instead of relying purely on manual graph interpretation, the software features an embedded decision logic engine that automatically classifies signal behavior, detects energy trends, and flags high-energy anomalies indicative of localized mechanical defects (such as pitting, spalling, or crack propagation).

## 🎥 Video Demonstration & Tutorial

Watch the video below to see a complete walkthrough of how to operate the AE Analyzer program:

[![AE Analyzer Tutorial](https://img.youtube.com/vi/nKzfzsco3KU/maxresdefault.jpg)](https://youtu.be/nKzfzsco3KU)

*(Click the image above to open the video on YouTube)*

## ✨ Key Features

* **Raw Data Processing:** Reads raw 16-bit binary (`.bin`) integer data, converts it to real voltage (assuming a 12-bit ADC and 3.3V reference), and automatically centers the signal by removing DC offsets.
* **Dynamic Feature Extraction:** Computes Root Mean Square (RMS), Peak Amplitude, and AE Counts across customizable sliding time windows (default 0.1s).
* **Automated Diagnostic Logic:**
  * **Trend Analysis:** Uses linear regression on RMS values to detect progressing wear (increasing energy) or stable operating conditions.
  * **Signal Classification:** Calculates the Crest Factor to classify activity as either *Burst Emissions* (distinct impacts, cracking) or *Continuous Emissions* (steady friction, flow).
  * **Event Detection:** Establishes a dynamic baseline threshold ($+2\sigma$) to automatically isolate and flag specific time windows where abnormal, high-energy spikes occur.
* **Interactive GUI:** A fully scrollable desktop interface built with `Tkinter` and `Matplotlib` for easy batch loading of `.bin` files, real-time plotting, and automated report generation.

## 📂 Project Structure

```text
REPCO_Mechatronics/
│
├── Python/
│   ├── app.py               # Main GUI application and diagnostic logic
│   └── requirements.txt     # Python dependencies 
│
├── AE testing/              # Sample binary data files for testing
│   ├── a0016.bin
│   ├── a0017.bin
│   └── ...
│
└── README.md

## 📥 Download and Installation

**For Windows Users:**
1. Download the `AE_Analyzer.exe` file.
2. Double-click the file to run the application instantly. No installation required.
*(Note: Windows Defender might show a "Windows protected your PC" blue screen because the app is from an unknown publisher. Click "More info" and then "Run anyway").*

**For Mac Users:**
1. Download the `AE_Analyzer.zip` file.
2. Extract the `.zip` to get the `AE_Analyzer.app`.
3. Right-click the `.app` file and select "Open" to bypass Mac's first-time security block.
