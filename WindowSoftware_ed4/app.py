import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import numpy as np
import os

# CRITICAL for macOS PyInstaller bundle:
# Force TkAgg backend BEFORE importing pyplot.
# Without this, matplotlib defaults to the macosx backend on macOS,
# which conflicts with tkinter inside a bundled app and causes a
# silent crash on launch.
import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.mlab as mlab

# ============================================================
#  HELP / DOCUMENTATION TEXT
# ============================================================
HELP_DOCUMENTATION = """\
══════════════════════════════════════════════════════════════════
  ACOUSTIC EMISSION (AE) ANALYZER — COMPLETE DOCUMENTATION
  REPCO Mechatronics
══════════════════════════════════════════════════════════════════

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SECTION 1: HOW TO USE THE SOFTWARE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP-BY-STEP GUIDE
------------------

STEP 1 — LOAD FILES
  Click "1. Load .bin Files"
  -> Select one or more raw binary AE data files (.bin format)
     recorded from your AE sensor acquisition system.
  -> Multiple files can be loaded at once and switched via the
     dropdown menu without reloading.

STEP 2 — SELECT A FILE
  Use the dropdown "2. Select File:" to choose which loaded
  file to analyse. The plot titles update immediately.

STEP 3 — SET PARAMETERS (optional — can be adjusted after)

  Spectrogram Color Range:
    Min dBFS / Max dBFS controls the colour scale.
    Typical range: -90 (noise floor) to -20 (strong signal).
    Click "Apply Colors" to update without recomputing.

  AE Count Threshold (Primary):
    One threshold in dBAE used for the Count at Time and
    Cumulative Count plots.
    Reference: 0 dBAE = 1 uV (microvolt)
    Typical range: 80-110 dBAE depending on sensor setup.
    Click "Apply Ranges & Recalculate Counts" to update.

  Multi-Threshold T1 / T2 / T3:
    Three amplitude threshold levels (all in dBAE) used by
    the two new analysis graphs:

    T1 = Highest threshold (fewest AE counts exceed this)
    T2 = Middle threshold
    T3 = Lowest threshold  (most AE counts exceed this)

    These appear as horizontal lines on the dBAE vs Time
    graph, and as vertical markers on the Amplitude
    Distribution graph.
    Click "Apply Thresholds & Redraw" to update both graphs.

  Time-Domain Y-Axis Ranges:
    Set maximum Y values for RMS, Peak, and Count plots.
    These auto-scale on first compute; adjust manually
    afterwards if needed.

STEP 4 — COMPUTE & PLOT
  Click "3. Compute & Plot".
  The software will:
    - Read raw 16-bit binary data from the selected file
    - Convert ADC counts to Voltage (V = count/4096 x 3.3)
    - Remove DC offset (subtract mean)
    - Compute and display all 7 plots
    - Generate the Automated Diagnostic Report

STEP 5 — INTERPRETING THE 7 PLOTS

  [1] Spectrogram (dBFS)
      Colour map of signal power vs frequency and time.
      Bright/warm = high power at that frequency and time.
      Horizontal colour bands = persistent resonance frequencies.
      Bright vertical streaks = broadband AE events (impacts).

  [2] RMS Trend
      Root Mean Square amplitude per analysis window (Volts).
      Represents the energy content of each window.
      Rising RMS = increasing acoustic emission energy.
      Flat RMS = stable or background-only signal.

  [3] Peak Amplitude Trend
      Maximum absolute amplitude per window (Volts).
      Sudden spikes indicate crack events, impacts, or
      high-energy burst emissions.
      Compare with RMS to compute Crest Factor.

  [4] Count at Time (Per Window)
      Number of times the signal crosses the primary threshold
      within each analysis window (ring-down count method).
      High bar = intense AE activity at that time.

  [5] Cumulative Count vs Time
      Running total of all threshold crossings.
      A steep slope = high AE activity period.
      A flat section = quiet/inactive period.
      The total at the end = overall AE count for this file.

  [6] AE Level (dBAE) vs Time  [NEW]
      The windowed peak amplitude expressed in dBAE.
      dBAE = 20 x log10(Peak_Volts / 1uV)
      Coloured horizontal lines show your T1, T2, T3 levels.
      When the trace rises above T1 -> very high energy event.
      When between T2 and T1 -> moderate energy event.
      When above T3 -> AE event at minimum threshold detected.
      Below T3 -> background noise only.

  [7] Amplitude Distribution  [NEW]
      Total AE count (Y) vs amplitude threshold in dBAE (X).
      Shows how many events exceeded each threshold level.
      Naturally decreasing: lower threshold = more counts.
      T3, T2, T1 are marked with coloured vertical lines and X
      markers showing the count at each threshold.
      A steep drop-off = mostly low-energy (background) events.
      A shallow slope = energetic AE source is present.

STEP 6 — READ THE DIAGNOSTIC REPORT
  Automatically generated at the bottom of the window after
  each computation. Provides:
    - Signal classification (Burst / Continuous / Background)
    - Energy trend (Increasing / Stable / Decreasing)
    - Total cumulative AE count
    - List of high-energy anomaly windows detected

INPUT DATA FORMAT
-----------------
  File type  : Raw 16-bit unsigned integer binary (.bin)
  ADC scale  : 4096 counts = 3.3 V  (12-bit ADC, 3.3 V range)
  Sample rate: 4000 Hz  (fs = 4000 in source code)
  Window time: 0.1 s -> 400 samples per analysis window


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SECTION 2: THEORETICAL BACKGROUND
  (Physics & Mathematics of Acoustic Emission Analysis)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2.1  PHYSICS OF ACOUSTIC EMISSION
----------------------------------
Acoustic Emission (AE) is the phenomenon of transient elastic
waves generated by the rapid, localised release of strain energy
within a solid material or at its surface.

SOURCES OF ACOUSTIC EMISSION:
  - Crack initiation and propagation in metals / composites
  - Plastic deformation and dislocation movement
  - Fibre breakage and delamination in composite materials
  - Corrosion reactions and hydrogen embrittlement
  - Friction and fretting at mechanical interfaces
  - Fluid leaks, cavitation, and flow turbulence

WAVE TYPES:
  Burst emission      - Discrete, impulse-like waveforms.
                        Associated with crack growth and impacts.
                        High Crest Factor (CF > 4), intermittent.
  Continuous emission - Overlapping, noise-like waveforms.
                        Associated with friction and uniform wear.
                        Low CF (approx 1.4), persistent.

KAISER EFFECT:
  AE is only generated when the applied stress exceeds the
  previously experienced maximum stress level. The material
  retains an "acoustic memory" of past loading.
  Application: used to determine residual stress and to identify
  previous overload history in structures.

FELICITY EFFECT:
  In damaged or fatigued materials, significant AE is detected
  BEFORE reaching the previous maximum stress. Quantified by:
    FR = (Stress at AE onset) / (Previous maximum stress)
  FR < 1 indicates irreversible damage accumulation.
  The smaller FR, the more severe the damage.


2.2  SIGNAL PROCESSING MATHEMATICS
-------------------------------------

A. ADC CONVERSION
   Raw 16-bit ADC counts are converted to physical voltage:
     V(t) = (raw_count / 4096) x 3.3   [Volts]

   DC offset removal (mean subtraction):
     x(t) = V(t) - mean(V)
   This removes static biases and centres the signal at zero.

B. SPECTROGRAM  (Short-Time Fourier Transform)
   Decomposes the signal into time and frequency simultaneously:

     STFT{x}(t,f) = integral of  x(tau) * w(tau-t) * exp(-j2*pi*f*tau) dtau

   where w(t) is a Hann window (suppresses spectral leakage).

   Power Spectral Density:
     P(t,f) = |STFT{x}(t,f)|^2

   In dBFS (decibels relative to full scale):
     dBFS(t,f) = 10 x log10(P(t,f) + epsilon)
   epsilon = 1e-12 prevents log(0) undefined values.

   Implementation: NFFT=256, noverlap=192 (75% overlap), Hann window.

C. RMS (Root Mean Square) — Energy Metric
   For each analysis window of N samples:
     RMS = sqrt( (1/N) x sum(xi^2) )    [Volts]

   Rising RMS trend = increasing acoustic energy in the structure.

D. PEAK AMPLITUDE
   For each window of N samples:
     Peak = max|xi|    for i = 1 to N    [Volts]

   Used for AE hit detection and amplitude distribution analysis.

E. CREST FACTOR (CF)
   CF = Peak / RMS

   High CF (> 4)    -> Burst emission: impulsive events dominate
   Low  CF (~ 1.4)  -> Continuous emission: Gaussian noise-like

F. AE AMPLITUDE SCALE — dBAE STANDARD
   Standard AE amplitude is referenced to 1 microvolt (1 uV):

     A_dBAE = 20 x log10( V_peak / 1e-6 )    [dBAE]

   Examples:
     V = 1 uV   (1e-6 V)  ->  0 dBAE
     V = 10 uV  (1e-5 V)  -> 20 dBAE
     V = 100 uV (1e-4 V)  -> 40 dBAE
     V = 1 mV   (1e-3 V)  -> 60 dBAE

   Reverse — voltage from a given dBAE value:
     V_thresh = 1e-6 x 10^(A_dBAE / 20)    [Volts]

   Standards: ASTM E1106, EN 13554, ISO 12716

G. AE COUNTS (Ring-Down Count Method)
   In each analysis window, the count = number of times the
   absolute signal amplitude crosses the threshold:

     Counts_window = #{i : |x(i)| > V_thresh}

   A single high-energy burst produces MANY counts as the
   waveform rings across the threshold multiple times before
   decaying. Standardised in ASTM E1781.

H. CUMULATIVE COUNT
   N_cum(k) = sum over j=1 to k of Counts_window(j)

   Always monotonically non-decreasing.
   Slope (dN_cum/dt) = AE count rate = real-time activity indicator.

I. AMPLITUDE DISTRIBUTION
   N(A) = total counts at or above amplitude threshold A:

     N(A) = sum over windows where Peak_dBAE >= A of Counts(window)

   For most AE sources, this follows a log-linear relationship:
     log10[N(A)] = C - b x A

   where b = slope, C = intercept.

   Interpretation of slope b:
     Large b (steep)   -> mostly small events (early-stage damage)
     Small b (shallow) -> many high-energy events (active cracking)

   This is the AE analogue of the seismic Gutenberg-Richter law:
     log10(N) = a - b x M   (M = earthquake magnitude)

J. WINDOWED ANALYSIS PARAMETERS
   Window duration   : Tw = 0.1 s
   Samples per window: N  = Tw x fs = 0.1 x 4000 = 400 samples
   Step size (no overlap): step = N = 400 samples
   Number of windows : n_win = floor((N_total - N) / step) + 1
   Time axis         : window index 1, 2, ..., n_win


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SECTION 3: WHY PYINSTALLER IS SECURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PyInstaller packages this Python application into a standalone
macOS .app bundle. Here is a complete security explanation.

3.1  WHAT PYINSTALLER DOES
  PyInstaller bundles:
    - A copy of the CPython interpreter
    - All required packages (NumPy, Matplotlib, Tkinter, etc.)
    - Compiled Python bytecode (.pyc) of your source files
    - Any data files specified in the .spec file

3.2  SOURCE CODE PROTECTION
  PyInstaller compiles .py source files into Python bytecode
  (.pyc) before packaging. The original human-readable .py
  source files are NOT included in the distributed executable.
  Note: bytecode can be decompiled with specialised tools.
  For maximum IP protection, use Nuitka or PyArmor on top.
  For scientific/engineering use, bytecode protection is
  typically more than sufficient.

3.3  NO EXTERNAL PYTHON INSTALLATION REQUIRED
  The .app bundle contains its own private Python interpreter.
  It does NOT depend on, modify, or interact with the macOS
  system Python or any user-installed Python environment.
  This eliminates dependency version conflicts and environmental
  attacks via poisoned system packages.

3.4  ISOLATED RUNTIME ENVIRONMENT
  On launch, PyInstaller extracts to a private temp directory
  (_MEIPASS folder) which:
    - Is created fresh each run with a unique path
    - Has no write access to system directories
    - Cannot be injected into by other processes
    - Is automatically cleaned up on application exit
  Prevents code injection and ensures reproducible behaviour.

3.5  NO INTERNET CONNECTION REQUIRED
  This AE Analyzer is fully offline:
    - Does not connect to any server or API
    - Does not send telemetry or usage data
    - Does not download updates at runtime
  Your raw AE data (.bin files) never leaves your computer.

3.6  CODE SIGNING AND NOTARISATION (macOS)
  PyInstaller apps can be cryptographically signed:

    codesign --deep --force --sign "Developer ID Application: \
      Your Name (TEAMID)" AEAnalyzer.app

  After signing, notarise through Apple:
    xcrun altool --notarize-app --file AEAnalyzer.app ...

  A signed and notarised app:
    - Passes macOS Gatekeeper without warnings
    - Is trusted by macOS as malware-free
    - Can be distributed outside the App Store

3.7  OPEN SOURCE AND AUDITABLE
  PyInstaller is open-source (MIT/GPL) and actively maintained:
    https://github.com/pyinstaller/pyinstaller
  Its bundling mechanism is publicly documented and auditable.

3.8  ANTIVIRUS FALSE POSITIVES
  Some AV tools flag PyInstaller executables. This is a KNOWN
  FALSE POSITIVE caused by the self-extracting compression
  behaviour resembling generic malware patterns.
  To resolve:
    1. Sign with a valid Apple Developer certificate
    2. Notarise through Apple (strongest trust signal)
    3. Add the app to your organisation's AV whitelist
    4. Use --exclude-module in .spec to reduce bundle size

3.9  COMPARISON WITH ALTERNATIVES

  Method                  Src Exposed  Self-Contained  macOS Trust
  ----------------------  -----------  --------------  -----------
  Distributing .py files  YES (full)   No              N/A
  PyInstaller .app        No (bytec.)  YES             Signable
  cx_Freeze               No (bytec.)  YES             Signable
  Nuitka (C-compiled)     No (binary)  YES             Signable
  Apple App Store         No           YES             Maximum

  RECOMMENDATION: PyInstaller is the fastest, simplest secure
  choice for internal or small-team distribution.
  Add code signing + notarisation for wider public release.

SUMMARY
  PyInstaller produces a fully self-contained macOS app that:
    [+] Hides Python source code (compiled to bytecode)
    [+] Requires no external Python installation
    [+] Runs in an isolated, clean environment
    [+] Keeps all measurement data strictly local
    [+] Can be code-signed for Gatekeeper compliance
    [+] Is built on a trusted, open-source, auditable tool

══════════════════════════════════════════════════════════════════
  END OF DOCUMENTATION — AE Analyzer — REPCO Mechatronics
══════════════════════════════════════════════════════════════════
"""


class AEAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ultimate Acoustic Emission (AE) Analyzer")
        self.root.geometry("1100x900")

        # --- Variables ---
        self.fs = 4000
        self.window_time = 0.1
        self.overlap = 0.0
        self.file_paths = []
        self.file_dict = {}

        # Spectrogram dB range
        self.spec_db_min = -90
        self.spec_db_max = -20

        # Primary AE Count Threshold (dBAE)
        self.ae_threshold_dbae = 95.0

        # Multi-threshold T1, T2, T3 (dBAE)
        self.ae_t1 = 100.0   # Highest (fewest counts)
        self.ae_t2 = 90.0    # Middle
        self.ae_t3 = 80.0    # Lowest (most counts)

        # Y-axis ranges for time-domain plots
        self.rms_ymin = 0.0
        self.rms_ymax = 0.05
        self.peak_ymin = 0.0
        self.peak_ymax = 0.30
        self.win_counts_ymax = 100.0
        self.cum_counts_ymax = 1000.0

        # Cached computed data
        self._cached_rms = None
        self._cached_peak = None
        self._cached_window_counts = None
        self._cached_cum_counts = None
        self._cached_time_axis = None
        self._cached_name = None
        self._cached_signal = None
        self._cached_win = None
        self._cached_step = None
        self._cached_Pxx_dB = None
        self._cached_peak_dbae = None        # NEW: windowed peak in dBAE
        self._cached_amp_dist_thresh = None  # NEW: threshold sweep array
        self._cached_amp_dist_counts = None  # NEW: counts at each swept threshold

        # ==========================================
        # --- SCROLLABLE MAIN WINDOW SETUP ---
        # ==========================================
        self.main_canvas = tk.Canvas(self.root, highlightthickness=0)
        self.main_scrollbar = ttk.Scrollbar(self.root, orient="vertical",
                                            command=self.main_canvas.yview)
        self.scrollable_frame = tk.Frame(self.main_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(
                scrollregion=self.main_canvas.bbox("all"))
        )

        self.canvas_window = self.main_canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)

        self.main_scrollbar.pack(side="right", fill="y")
        self.main_canvas.pack(side="left", fill="both", expand=True)

        self.main_canvas.bind(
            "<Configure>",
            lambda e: self.main_canvas.itemconfig(self.canvas_window, width=e.width)
        )

        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self.root.bind_all("<Button-4>",
                           lambda e: self.main_canvas.yview_scroll(-1, "units"))
        self.root.bind_all("<Button-5>",
                           lambda e: self.main_canvas.yview_scroll(1, "units"))

        # ==========================================
        # --- Top Frame: File Controls + Help ---
        # ==========================================
        control_frame = tk.Frame(self.scrollable_frame, pady=10, padx=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        self.btn_browse = tk.Button(control_frame, text="1. Load .bin Files",
                                    command=self.load_files)
        self.btn_browse.pack(side=tk.LEFT, padx=5)

        tk.Label(control_frame, text="2. Select File:").pack(side=tk.LEFT, padx=5)

        self.combo_files = ttk.Combobox(control_frame, state="readonly", width=30)
        self.combo_files.pack(side=tk.LEFT, padx=5)
        self.combo_files.bind("<<ComboboxSelected>>", self.update_titles_pre_compute)

        self.btn_compute = tk.Button(control_frame, text="3. Compute & Plot",
                                     command=self.compute_and_plot)
        self.btn_compute.pack(side=tk.LEFT, padx=5)

        # Help Button (right-aligned)
        self.btn_help = tk.Button(
            control_frame,
            text="?  Help / Documentation",
            command=self.show_help,
            bg="#4a90d9", fg="white",
            activebackground="#2c6fad", activeforeground="white",
            font=("TkDefaultFont", 10, "bold"),
            relief=tk.RAISED, bd=2, padx=8
        )
        self.btn_help.pack(side=tk.RIGHT, padx=10)

        # ==========================================
        # --- Control Panel ---
        # ==========================================
        slider_panel = tk.LabelFrame(self.scrollable_frame, text="Plot Range Controls",
                                     padx=8, pady=6)
        slider_panel.pack(fill=tk.X, padx=10, pady=(0, 4))

        def make_entry_row(parent, label, default_max, entry_width=10):
            row = tk.Frame(parent)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=f"{label}", width=18, anchor="e").pack(
                side=tk.LEFT, padx=(0, 6))
            tk.Label(row, text="Max Y-Axis:", anchor="e").pack(side=tk.LEFT)
            e_max = tk.Entry(row, width=entry_width)
            e_max.insert(0, str(default_max))
            e_max.pack(side=tk.LEFT, padx=4)
            return e_max

        # ---- Spectrogram dB ----
        spec_frame = tk.LabelFrame(slider_panel,
                                   text="Spectrogram Color Range (Negative dBFS)",
                                   padx=6, pady=4)
        spec_frame.pack(fill=tk.X, pady=(0, 4))

        row_spec = tk.Frame(spec_frame)
        row_spec.pack(fill=tk.X, pady=3)
        tk.Label(row_spec, text="dBFS Range:", width=18, anchor="e").pack(
            side=tk.LEFT, padx=(0, 6))
        tk.Label(row_spec, text="Min:").pack(side=tk.LEFT)
        self.entry_spec_min = tk.Entry(row_spec, width=10)
        self.entry_spec_min.insert(0, str(self.spec_db_min))
        self.entry_spec_min.pack(side=tk.LEFT, padx=4)
        tk.Label(row_spec, text="Max:").pack(side=tk.LEFT)
        self.entry_spec_max = tk.Entry(row_spec, width=10)
        self.entry_spec_max.insert(0, str(self.spec_db_max))
        self.entry_spec_max.pack(side=tk.LEFT, padx=4)

        self.btn_apply_spec = tk.Button(spec_frame, text="Apply Colors",
                                        command=self.apply_spec_range)
        self.btn_apply_spec.pack(anchor="w", padx=4, pady=(4, 0))

        # ---- Time-domain ranges & primary AE threshold ----
        td_frame = tk.LabelFrame(slider_panel,
                                 text="Time-Domain Ranges & Primary AE Threshold",
                                 padx=6, pady=4)
        td_frame.pack(fill=tk.X, pady=(0, 4))

        thresh_row = tk.Frame(td_frame)
        thresh_row.pack(fill=tk.X, pady=(3, 10))
        tk.Label(thresh_row, text="Count Threshold (dBAE):",
                 font=("TkDefaultFont", 9, "bold")).pack(side=tk.LEFT, padx=(4, 6))
        self.entry_ae_thresh = tk.Entry(thresh_row, width=10)
        self.entry_ae_thresh.insert(0, str(self.ae_threshold_dbae))
        self.entry_ae_thresh.pack(side=tk.LEFT, padx=4)
        tk.Label(thresh_row, text="(0 dBAE = 1 uV)", fg="#555555").pack(
            side=tk.LEFT, padx=4)

        self.entry_rms_max = make_entry_row(td_frame, "RMS (V):", self.rms_ymax)
        self.entry_peak_max = make_entry_row(td_frame, "Peak (V):", self.peak_ymax)
        self.entry_win_counts_max = make_entry_row(td_frame, "Win. Counts:",
                                                   self.win_counts_ymax)
        self.entry_cum_counts_max = make_entry_row(td_frame, "Cum. Counts:",
                                                   self.cum_counts_ymax)

        self.btn_apply_td = tk.Button(td_frame,
                                      text="Apply Ranges & Recalculate Counts",
                                      command=self.apply_td_ranges)
        self.btn_apply_td.pack(anchor="w", padx=4, pady=(4, 0))

        # ---- NEW: Multi-Threshold T1 / T2 / T3 ----
        mt_frame = tk.LabelFrame(
            slider_panel,
            text="Multi-Threshold Analysis  (T1 / T2 / T3)"
                 "  —  dBAE Graph & Amplitude Distribution",
            padx=6, pady=4
        )
        mt_frame.pack(fill=tk.X)

        def make_thresh_row(parent, label, default_val, color):
            row = tk.Frame(parent)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label, width=26, anchor="e",
                     fg=color, font=("TkDefaultFont", 9, "bold")).pack(
                side=tk.LEFT, padx=(0, 6))
            e = tk.Entry(row, width=10)
            e.insert(0, str(default_val))
            e.pack(side=tk.LEFT, padx=4)
            tk.Label(row, text="dBAE", fg="#555555").pack(side=tk.LEFT)
            return e

        self.entry_t1 = make_thresh_row(mt_frame, "T1  (Highest threshold):",
                                        self.ae_t1, "#d62728")
        self.entry_t2 = make_thresh_row(mt_frame, "T2  (Middle threshold):",
                                        self.ae_t2, "#ff7f0e")
        self.entry_t3 = make_thresh_row(mt_frame, "T3  (Lowest threshold):",
                                        self.ae_t3, "#2ca02c")

        self.btn_apply_thresh = tk.Button(
            mt_frame, text="Apply Thresholds & Redraw",
            command=self.apply_multi_thresholds
        )
        self.btn_apply_thresh.pack(anchor="w", padx=4, pady=(6, 0))

        # ==========================================
        # --- Matplotlib Figure: 7 Subplots ---
        #   5 original (full-width) + 2 new (side-by-side bottom row)
        # ==========================================
        self.canvas_frame = tk.Frame(self.scrollable_frame)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.fig = plt.figure(figsize=(10, 24))
        gs_main = GridSpec(6, 1, figure=self.fig,
                           height_ratios=[2, 1, 1, 1, 1, 2],
                           hspace=0.55)

        # Original 5 subplots (full width)
        self.ax_spec       = self.fig.add_subplot(gs_main[0])
        self.ax_rms        = self.fig.add_subplot(gs_main[1])
        self.ax_peak       = self.fig.add_subplot(gs_main[2])
        self.ax_win_counts = self.fig.add_subplot(gs_main[3])
        self.ax_cum_counts = self.fig.add_subplot(gs_main[4])

        # NEW: 2 side-by-side subplots in the last row
        gs_bottom = GridSpecFromSubplotSpec(1, 2, subplot_spec=gs_main[5],
                                            wspace=0.40)
        self.ax_ae_thresh = self.fig.add_subplot(gs_bottom[0])  # dBAE vs time
        self.ax_amp_dist  = self.fig.add_subplot(gs_bottom[1])  # Amplitude distribution

        self.update_titles_pre_compute()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.get_tk_widget().bind("<MouseWheel>", self._on_mousewheel)

        self.fig.subplots_adjust(left=0.09, right=0.91, top=0.96, bottom=0.03,
                                 wspace=0.15, hspace=0.55)

        # --- Diagnostic Report ---
        interp_frame = tk.LabelFrame(self.scrollable_frame,
                                     text="Automated Diagnostic Report",
                                     padx=10, pady=10)
        interp_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.text_interp = scrolledtext.ScrolledText(
            interp_frame, height=10, wrap=tk.WORD, bg="#f5f5f5", fg="black")
        self.text_interp.pack(fill=tk.BOTH, expand=True)
        self.text_interp.config(state=tk.DISABLED)

        self.root.protocol("WM_DELETE_WINDOW", self.close_prog)
        self.cbar = None

    # ------------------------------------------------------------------
    # Mouse-wheel scroll
    # ------------------------------------------------------------------
    def _on_mousewheel(self, event):
        delta = event.delta
        scroll_amount = (int(-1 * (delta / 120))
                         if abs(delta) >= 120 else int(-1 * delta))
        self.main_canvas.yview_scroll(scroll_amount, "units")

    # ------------------------------------------------------------------
    # AE dBAE Count Calculation
    # ------------------------------------------------------------------
    def _compute_counts_from_dbae(self, signal, win, step, dbae_threshold):
        N = len(signal)
        amp_threshold_volts = 1e-6 * (10.0 ** (dbae_threshold / 20.0))
        counts = []
        for i in range(0, N - win + 1, step):
            segment = signal[i:i + win]
            counts.append(int(np.sum(np.abs(segment) > amp_threshold_volts)))
        return np.array(counts), amp_threshold_volts

    # ------------------------------------------------------------------
    # Spectrogram color range (no recompute needed)
    # ------------------------------------------------------------------
    def apply_spec_range(self):
        try:
            self.spec_db_min = float(self.entry_spec_min.get())
            self.spec_db_max = float(self.entry_spec_max.get())
            if hasattr(self, 'im'):
                self.im.set_clim(self.spec_db_min, self.spec_db_max)
                self.canvas.draw_idle()
        except ValueError:
            messagebox.showwarning("Invalid Input",
                                   "Please enter valid numbers for Spectrogram dB.")

    # ------------------------------------------------------------------
    # Time-domain range + primary threshold apply
    # ------------------------------------------------------------------
    def apply_td_ranges(self):
        try:
            self.rms_ymax        = float(self.entry_rms_max.get())
            self.peak_ymax       = float(self.entry_peak_max.get())
            self.win_counts_ymax = float(self.entry_win_counts_max.get())
            self.cum_counts_ymax = float(self.entry_cum_counts_max.get())
            new_ae_thresh        = float(self.entry_ae_thresh.get())
        except ValueError:
            messagebox.showwarning(
                "Invalid Input",
                "Please ensure all time-domain and threshold inputs are numbers.")
            return

        if self._cached_signal is not None:
            self.ae_threshold_dbae = new_ae_thresh
            new_counts, _ = self._compute_counts_from_dbae(
                self._cached_signal, self._cached_win,
                self._cached_step, self.ae_threshold_dbae
            )
            self._cached_window_counts = new_counts
            self._cached_cum_counts    = np.cumsum(new_counts)
            self.generate_interpretation(
                self._cached_name, self._cached_rms,
                self._cached_peak, new_counts)

        self._redraw_td_plots()

    # ------------------------------------------------------------------
    # NEW: Apply multi-threshold T1 / T2 / T3
    # ------------------------------------------------------------------
    def apply_multi_thresholds(self):
        try:
            self.ae_t1 = float(self.entry_t1.get())
            self.ae_t2 = float(self.entry_t2.get())
            self.ae_t3 = float(self.entry_t3.get())
        except ValueError:
            messagebox.showwarning("Invalid Input",
                                   "Please enter valid numbers for T1, T2, T3.")
            return

        if self._cached_signal is not None:
            self._draw_ae_thresh_plot()
            self._draw_amp_dist_plot()
            self.canvas.draw_idle()

    # ------------------------------------------------------------------
    # NEW: dBAE vs Time plot with T1, T2, T3 threshold lines
    # ------------------------------------------------------------------
    def _draw_ae_thresh_plot(self):
        if self._cached_peak is None or self._cached_time_axis is None:
            return

        name      = self._cached_name or ""
        time_axis = self._cached_time_axis
        peak_volts = self._cached_peak

        # Convert windowed peak (Volts) to dBAE
        peak_dbae = 20.0 * np.log10(np.maximum(peak_volts, 1e-12) / 1e-6)
        self._cached_peak_dbae = peak_dbae

        self.ax_ae_thresh.clear()
        self.ax_ae_thresh.plot(
            time_axis, peak_dbae,
            color='#9467bd', linewidth=1.0, alpha=0.85,
            label='Peak Level (dBAE)'
        )

        # Threshold horizontal lines
        thresholds = [
            (self.ae_t1, '#d62728', 'T1'),
            (self.ae_t2, '#ff7f0e', 'T2'),
            (self.ae_t3, '#2ca02c', 'T3'),
        ]
        for t_val, t_col, t_name in thresholds:
            self.ax_ae_thresh.axhline(
                y=t_val, color=t_col, linewidth=1.8, linestyle='--',
                label=f'{t_name} = {t_val} dBAE'
            )
            if len(time_axis) > 0:
                self.ax_ae_thresh.annotate(
                    t_name,
                    xy=(time_axis[-1], t_val),
                    xytext=(4, 0), textcoords='offset points',
                    color=t_col, fontsize=8, fontweight='bold',
                    va='center', annotation_clip=False
                )

        self.ax_ae_thresh.set_xlabel('Time (Window Number)', fontsize=8)
        self.ax_ae_thresh.set_ylabel('Amplitude (dBAE)', fontsize=8)
        self.ax_ae_thresh.set_title(
            f'AE Level (dBAE) vs Time  —  {name}', fontsize=9)
        self.ax_ae_thresh.legend(loc='upper right', fontsize=7, ncol=2)
        self.ax_ae_thresh.grid(True, alpha=0.35)
        self.ax_ae_thresh.tick_params(labelsize=7)

    # ------------------------------------------------------------------
    # NEW: Amplitude Distribution plot (Count vs Threshold dBAE)
    # ------------------------------------------------------------------
    def _draw_amp_dist_plot(self):
        if self._cached_signal is None:
            return

        name   = self._cached_name or ""
        signal = self._cached_signal
        win    = self._cached_win
        step   = self._cached_step

        # Sweep threshold range: below T3 to above T1
        t_low  = min(self.ae_t1, self.ae_t2, self.ae_t3) - 12.0
        t_high = max(self.ae_t1, self.ae_t2, self.ae_t3) + 18.0
        thresh_values = np.linspace(t_low, t_high, 60)

        dist_counts = []
        for t in thresh_values:
            counts_arr, _ = self._compute_counts_from_dbae(signal, win, step, t)
            dist_counts.append(int(np.sum(counts_arr)))
        dist_counts = np.array(dist_counts, dtype=float)

        self._cached_amp_dist_thresh = thresh_values
        self._cached_amp_dist_counts = dist_counts

        self.ax_amp_dist.clear()

        # Log Y-scale if data spans > 2 orders of magnitude
        nonzero = dist_counts[dist_counts > 0]
        use_log = (len(nonzero) > 1 and
                   (np.max(nonzero) / np.min(nonzero)) > 100)

        self.ax_amp_dist.plot(thresh_values, dist_counts, 'k-', linewidth=2.0,
                              label='N(A) Amplitude Dist.')
        self.ax_amp_dist.fill_between(thresh_values, dist_counts,
                                      alpha=0.12, color='gray')

        # Mark T1, T2, T3 with vertical dashed lines and X markers
        thresholds = [
            (self.ae_t1, '#d62728', 'T1'),
            (self.ae_t2, '#ff7f0e', 'T2'),
            (self.ae_t3, '#2ca02c', 'T3'),
        ]
        for t_val, t_col, t_name in thresholds:
            self.ax_amp_dist.axvline(
                x=t_val, color=t_col, linewidth=1.6, linestyle='--',
                label=f'{t_name}={t_val} dBAE'
            )
            idx = int(np.argmin(np.abs(thresh_values - t_val)))
            self.ax_amp_dist.plot(
                thresh_values[idx], dist_counts[idx],
                'x', color=t_col, markersize=10, markeredgewidth=2.5
            )

        if use_log:
            self.ax_amp_dist.set_yscale('log')

        self.ax_amp_dist.set_xlabel('Amplitude Threshold (dBAE)', fontsize=8)
        self.ax_amp_dist.set_ylabel('Total AE Count', fontsize=8)
        self.ax_amp_dist.set_title(
            f'Amplitude Distribution  —  {name}', fontsize=9)
        self.ax_amp_dist.legend(loc='upper right', fontsize=7)
        self.ax_amp_dist.grid(True, alpha=0.35)
        self.ax_amp_dist.tick_params(labelsize=7)

    # ------------------------------------------------------------------
    # Redraw original 4 time-domain plots
    # ------------------------------------------------------------------
    def _redraw_td_plots(self):
        if self._cached_rms is None:
            return

        rms        = self._cached_rms
        peak       = self._cached_peak
        win_counts = self._cached_window_counts
        cum_counts = self._cached_cum_counts
        time_axis  = self._cached_time_axis
        name       = self._cached_name

        # Dynamic auto-scale
        update_ui = False
        if np.max(rms) > self.rms_ymax:
            self.rms_ymax = float(np.max(rms) * 1.15); update_ui = True
        if np.max(peak) > self.peak_ymax:
            self.peak_ymax = float(np.max(peak) * 1.15); update_ui = True
        if np.max(win_counts) > self.win_counts_ymax:
            self.win_counts_ymax = float(np.max(win_counts) * 1.15); update_ui = True
        if np.max(cum_counts) > self.cum_counts_ymax:
            self.cum_counts_ymax = float(np.max(cum_counts) * 1.15); update_ui = True

        if update_ui:
            self.entry_rms_max.delete(0, tk.END)
            self.entry_rms_max.insert(0, f"{self.rms_ymax:.4f}")
            self.entry_peak_max.delete(0, tk.END)
            self.entry_peak_max.insert(0, f"{self.peak_ymax:.4f}")
            self.entry_win_counts_max.delete(0, tk.END)
            self.entry_win_counts_max.insert(0, f"{self.win_counts_ymax:.0f}")
            self.entry_cum_counts_max.delete(0, tk.END)
            self.entry_cum_counts_max.insert(0, f"{self.cum_counts_ymax:.0f}")

        v_thresh = 1e-6 * (10.0 ** (self.ae_threshold_dbae / 20.0))

        # 1. RMS
        self.ax_rms.clear()
        self.ax_rms.plot(time_axis, rms, 'b-', linewidth=1.2)
        self.ax_rms.set_ylim(0, self.rms_ymax)
        self.ax_rms.set_ylabel('RMS (V)')
        self.ax_rms.set_title(f'RMS Trend  —  {name}')
        self.ax_rms.grid(True)

        # 2. Peak
        self.ax_peak.clear()
        self.ax_peak.plot(time_axis, peak, 'r-', linewidth=1.2)
        self.ax_peak.set_ylim(0, self.peak_ymax)
        self.ax_peak.set_ylabel('Peak (V)')
        self.ax_peak.set_title(f'Peak Amplitude Trend  —  {name}')
        self.ax_peak.grid(True)

        # 3. Window Counts (bar chart)
        self.ax_win_counts.clear()
        self.ax_win_counts.bar(time_axis, win_counts, color='#EDB120', edgecolor='none')
        self.ax_win_counts.set_ylim(0, self.win_counts_ymax)
        self.ax_win_counts.set_ylabel('Counts')
        self.ax_win_counts.set_title(
            f'Count at Time (Per Window)  —  {name}  '
            f'[{self.ae_threshold_dbae} dBAE]')
        self.ax_win_counts.grid(True)

        # 4. Cumulative Counts
        self.ax_cum_counts.clear()
        self.ax_cum_counts.plot(time_axis, cum_counts, color='#009933', linewidth=1.5)
        self.ax_cum_counts.fill_between(time_axis, cum_counts,
                                        alpha=0.3, color='#009933')
        self.ax_cum_counts.set_ylim(0, self.cum_counts_ymax)
        self.ax_cum_counts.set_ylabel('Sum Counts')
        self.ax_cum_counts.set_xlabel('Time (Window Number)')
        self.ax_cum_counts.set_title(
            f'Cumulative Count  —  {name}  '
            f'[{self.ae_threshold_dbae} dBAE = {v_thresh:.6f} V]')
        self.ax_cum_counts.grid(True)

        self.canvas.draw_idle()

    # ------------------------------------------------------------------
    # Update titles before compute (waiting state)
    # ------------------------------------------------------------------
    def update_titles_pre_compute(self, event=None):
        name = (self.combo_files.get() if self.combo_files.get()
                else "Waiting for file...")
        self.ax_spec.set_title(f'Spectrogram (dBFS)  —  {name}')
        self.ax_rms.set_title(f'RMS Trend  —  {name}')
        self.ax_peak.set_title(f'Peak Amplitude Trend  —  {name}')
        self.ax_win_counts.set_title(f'Count at Time (Per Window)  —  {name}')
        self.ax_cum_counts.set_title(f'Cumulative Count  —  {name}')
        self.ax_ae_thresh.set_title(f'AE Level (dBAE) vs Time  —  {name}')
        self.ax_amp_dist.set_title(f'Amplitude Distribution  —  {name}')
        self.fig.suptitle("", color='black', y=0.99)
        if hasattr(self, 'canvas'):
            self.canvas.draw_idle()

    # ------------------------------------------------------------------
    # Load files
    # ------------------------------------------------------------------
    def load_files(self):
        filepaths = filedialog.askopenfilenames(
            title="Select AE Binary Files",
            filetypes=[("Binary Files", "*.bin"), ("All Files", "*.*")]
        )
        if filepaths:
            self.file_dict = {os.path.basename(fp): fp for fp in filepaths}
            filenames = list(self.file_dict.keys())
            self.combo_files['values'] = filenames
            self.combo_files.current(0)
            self.update_titles_pre_compute()
            messagebox.showinfo("Files Loaded",
                                f"Successfully loaded {len(filepaths)} file(s).")

    # ------------------------------------------------------------------
    # Compute & Plot (main processing function)
    # ------------------------------------------------------------------
    def compute_and_plot(self):
        selected_name = self.combo_files.get()
        if not selected_name:
            messagebox.showwarning("Warning", "Please load and select a file first.")
            return

        filepath = self.file_dict[selected_name]
        self.fig.suptitle(f"Processing: {selected_name}...",
                          fontsize=14, fontweight='bold', color='red', y=0.99)
        self.canvas.draw()
        self.root.update()

        try:
            data   = np.fromfile(filepath, dtype=np.uint16)
            signal = data.astype(np.float64) / 4096.0 * 3.3
            signal = signal - np.mean(signal)

            N    = len(signal)
            win  = int(round(self.window_time * self.fs))
            step = int(round(win * (1 - self.overlap)))

            self._cached_signal = signal
            self._cached_win    = win
            self._cached_step   = step

            file_rms  = []
            file_peak = []

            for i in range(0, N - win + 1, step):
                segment = signal[i:i + win]
                file_rms.append(np.sqrt(np.mean(segment ** 2)))
                file_peak.append(np.max(np.abs(segment)))

            file_rms  = np.array(file_rms)
            file_peak = np.array(file_peak)
            time_axis = np.arange(1, len(file_rms) + 1)

            # Primary threshold AE counts
            file_win_counts, _ = self._compute_counts_from_dbae(
                signal, win, step, self.ae_threshold_dbae)
            file_cum_counts = np.cumsum(file_win_counts)

            # Cache results
            self._cached_rms           = file_rms
            self._cached_peak          = file_peak
            self._cached_window_counts = file_win_counts
            self._cached_cum_counts    = file_cum_counts
            self._cached_time_axis     = time_axis
            self._cached_name          = selected_name

            # Auto-set Y-axis limits
            self.rms_ymax        = max(self.rms_ymax,
                                       float(np.max(file_rms) * 1.15))
            self.peak_ymax       = max(self.peak_ymax,
                                       float(np.max(file_peak) * 1.15))
            self.win_counts_ymax = max(100.0,
                                       float(np.max(file_win_counts) * 1.15))
            self.cum_counts_ymax = max(100.0,
                                       float(np.max(file_cum_counts) * 1.15))

            def _set_entry(entry, value, decimals=4):
                entry.delete(0, tk.END)
                entry.insert(0, f"{value:.{decimals}f}")

            _set_entry(self.entry_rms_max,       self.rms_ymax)
            _set_entry(self.entry_peak_max,       self.peak_ymax)
            _set_entry(self.entry_win_counts_max, self.win_counts_ymax, decimals=0)
            _set_entry(self.entry_cum_counts_max, self.cum_counts_ymax, decimals=0)

            # --- Spectrogram ---
            self.ax_spec.clear()
            Pxx, freqs, bins = mlab.specgram(signal, NFFT=256, Fs=self.fs,
                                              noverlap=192)
            Pxx_dB = 10 * np.log10(Pxx + 1e-12)

            self.im = self.ax_spec.pcolormesh(
                bins, freqs, Pxx_dB,
                shading='gouraud', cmap='viridis',
                vmin=self.spec_db_min, vmax=self.spec_db_max
            )
            self.ax_spec.set_ylabel('Frequency (Hz)')
            self.ax_spec.set_xlabel('Time (s)')
            self.ax_spec.set_title(f'Spectrogram (dBFS)  —  {selected_name}')

            divider = make_axes_locatable(self.ax_spec)
            if self.cbar is not None:
                try:
                    self.cbar.remove()
                except Exception:
                    pass
            cax = divider.append_axes("right", size="3%", pad=0.05)
            self.cbar = self.fig.colorbar(self.im, cax=cax)
            self.cbar.set_label('Power (dBFS)')

            # Redraw original time-domain plots
            self._redraw_td_plots()

            # Draw NEW plots
            self._draw_ae_thresh_plot()
            self._draw_amp_dist_plot()

            self.fig.suptitle(f"Analysis Complete:  {selected_name}",
                              fontsize=14, fontweight='bold', color='black', y=0.99)
            self.canvas.draw()

            self.generate_interpretation(selected_name, file_rms,
                                         file_peak, file_win_counts)

            self.main_canvas.update_idletasks()
            self.main_canvas.configure(
                scrollregion=self.main_canvas.bbox("all"))
            self.main_canvas.yview_moveto(0)

        except Exception as e:
            self.fig.suptitle("", color='black')
            self.canvas.draw()
            messagebox.showerror(
                "Error",
                f"An error occurred while processing the file:\n{str(e)}")

    # ------------------------------------------------------------------
    # Automated Diagnostic Report
    # ------------------------------------------------------------------
    def generate_interpretation(self, filename, rms, peak, counts):
        time_windows    = np.arange(1, len(rms) + 1)
        max_peak        = np.max(peak)
        total_counts    = int(np.sum(counts))
        amp_threshold_v = 1e-6 * (10.0 ** (self.ae_threshold_dbae / 20.0))

        slope, _ = np.polyfit(time_windows, rms, 1)
        if slope > 0.0001:
            trend_status = "Increasing energy trend (Possible progressing anomaly/wear)"
        elif slope < -0.0001:
            trend_status = "Decreasing energy trend"
        else:
            trend_status = "Stable energy levels"

        crest_factors = peak / (rms + 1e-9)
        avg_cf        = np.mean(crest_factors)

        if avg_cf > 4.0 and total_counts > 0:
            signal_type = "Burst Emission (Distinct impacts, crack growth, or pitting)"
        elif total_counts > 0:
            signal_type = "Continuous Emission (Steady friction, flow, or uniform wear)"
        else:
            signal_type = "Background Noise Only"

        dynamic_threshold  = np.mean(peak) + (2 * np.std(peak))
        significant_events = np.where(peak > dynamic_threshold)[0]

        interp_text  = f"--- AUTOMATED DIAGNOSTIC REPORT: {filename} ---\n\n"
        interp_text += f"COUNT THRESHOLD (PRIMARY):\n"
        interp_text += f"  Target AE Level : {self.ae_threshold_dbae} dBAE\n"
        interp_text += f"  Required Voltage: {amp_threshold_v:.6f} V\n\n"
        interp_text += f"MULTI-THRESHOLD LEVELS:\n"
        interp_text += f"  T1 (High): {self.ae_t1} dBAE\n"
        interp_text += f"  T2 (Mid) : {self.ae_t2} dBAE\n"
        interp_text += f"  T3 (Low) : {self.ae_t3} dBAE\n\n"
        interp_text += f"OVERALL BEHAVIOR:\n"
        interp_text += f"  Signal Classification : {signal_type}\n"
        interp_text += f"  Avg Crest Factor      : {avg_cf:.2f}\n"
        interp_text += f"  Energy Trend          : {trend_status}\n"
        interp_text += f"  Total Cumulative Count: {total_counts}\n\n"
        interp_text += f"EVENT DETECTION:\n"

        if len(significant_events) > 0:
            event_windows = significant_events + 1
            interp_text += (f"  Detected {len(significant_events)} "
                            f"significant high-energy anomalies.\n")
            if len(event_windows) <= 10:
                interp_text += (f"  Critical Windows: "
                                f"{', '.join(map(str, event_windows))}\n")
            else:
                interp_text += (f"  Critical Windows: "
                                f"{', '.join(map(str, event_windows[:10]))}... "
                                f"(and {len(event_windows)-10} more)\n")
            interp_text += (f"  Max Peak: {max_peak:.4f} V  "
                            f"at window {np.argmax(peak) + 1}\n")
        else:
            interp_text += ("  No distinct high-energy spikes detected "
                            "above normal variance.\n")

        self.text_interp.config(state=tk.NORMAL)
        self.text_interp.delete("1.0", tk.END)
        self.text_interp.insert(tk.END, interp_text)
        self.text_interp.config(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Help / Documentation window
    # ------------------------------------------------------------------
    def show_help(self):
        help_win = tk.Toplevel(self.root)
        help_win.title("AE Analyzer — Help & Documentation")
        help_win.geometry("860x700")
        help_win.resizable(True, True)
        help_win.minsize(600, 400)

        # Header bar
        header_frame = tk.Frame(help_win, bg="#2c6fad", pady=10)
        header_frame.pack(fill=tk.X)
        tk.Label(
            header_frame,
            text="Acoustic Emission Analyzer  —  Complete Documentation",
            font=("TkDefaultFont", 13, "bold"),
            bg="#2c6fad", fg="white"
        ).pack()
        tk.Label(
            header_frame,
            text="REPCO Mechatronics",
            font=("TkDefaultFont", 9),
            bg="#2c6fad", fg="#cce0ff"
        ).pack()

        # Scrollable monospace text area (dark theme)
        text_frame = tk.Frame(help_win)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        help_text_widget = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=("Courier", 10),
            bg="#1e1e2e",
            fg="#cdd6f4",
            selectbackground="#313244",
            insertbackground="white",
            padx=14, pady=12,
            spacing1=2, spacing3=3
        )
        help_text_widget.pack(fill=tk.BOTH, expand=True)
        help_text_widget.insert(tk.END, HELP_DOCUMENTATION)
        help_text_widget.config(state=tk.DISABLED)
        help_text_widget.yview_moveto(0)

        # Footer with close button
        footer_frame = tk.Frame(help_win)
        footer_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Button(
            footer_frame,
            text="Close",
            command=help_win.destroy,
            width=16,
            bg="#d62728", fg="white",
            activebackground="#a01010", activeforeground="white",
            font=("TkDefaultFont", 10, "bold")
        ).pack()

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------
    def close_prog(self):
        plt.close('all')
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AEAnalyzerApp(root)
    root.mainloop()
