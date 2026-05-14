import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from matplotlib.gridspec import GridSpec
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.mlab as mlab


class AEAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Acoustic Emission (AE) Analyzer")
        self.root.geometry("1000x900")

        # --- Variables ---
        self.fs = 4000
        self.window_time = 0.1
        self.overlap = 0.0
        self.file_paths = []
        self.file_dict = {}

        # Spectrogram dB range
        self.db_min = -90
        self.db_max = -20

        # Y-axis ranges for time-domain plots (set after compute)
        self.rms_ymin = 0.0
        self.rms_ymax = 1.0
        self.peak_ymin = 0.0
        self.peak_ymax = 1.0
        self.counts_ymin = 0.0
        self.counts_ymax = 100.0

        # Cached computed data
        self._cached_rms = None
        self._cached_peak = None
        self._cached_counts = None
        self._cached_counts_cumsum = None
        self._cached_time_axis = None
        self._cached_name = None
        self._cached_signal = None      # raw signal for recomputing counts
        self._cached_win = None
        self._cached_step = None
        self._cached_Pxx_dB = None      # spectrogram power array (dB)

        # ==========================================
        # --- SCROLLABLE MAIN WINDOW SETUP ---
        # ==========================================
        self.main_canvas = tk.Canvas(self.root, highlightthickness=0)
        self.main_scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = tk.Frame(self.main_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )

        self.canvas_window = self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)

        self.main_scrollbar.pack(side="right", fill="y")
        self.main_canvas.pack(side="left", fill="both", expand=True)

        self.main_canvas.bind(
            "<Configure>",
            lambda e: self.main_canvas.itemconfig(self.canvas_window, width=e.width)
        )

        # Bind mousewheel events across OS
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self.root.bind_all("<Button-4>", lambda e: self.main_canvas.yview_scroll(-1, "units"))
        self.root.bind_all("<Button-5>", lambda e: self.main_canvas.yview_scroll(1, "units"))

        # ==========================================
        # --- Top Frame: File Controls ---
        # ==========================================
        control_frame = tk.Frame(self.scrollable_frame, pady=10, padx=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        self.btn_browse = tk.Button(control_frame, text="1. Load .bin Files", command=self.load_files)
        self.btn_browse.pack(side=tk.LEFT, padx=5)

        tk.Label(control_frame, text="2. Select File:").pack(side=tk.LEFT, padx=5)

        self.combo_files = ttk.Combobox(control_frame, state="readonly", width=30)
        self.combo_files.pack(side=tk.LEFT, padx=5)
        self.combo_files.bind("<<ComboboxSelected>>", self.update_titles_pre_compute)

        self.btn_compute = tk.Button(control_frame, text="3. Compute & Plot", command=self.compute_and_plot)
        self.btn_compute.pack(side=tk.LEFT, padx=5)

        # ==========================================
        # --- Entry Box Panel (all controls) ---
        # ==========================================
        slider_panel = tk.LabelFrame(self.scrollable_frame, text="Plot Range Controls", padx=8, pady=6)
        slider_panel.pack(fill=tk.X, padx=10, pady=(0, 4))

        def make_entry_row(parent, label, default_min, default_max, entry_width=10):
            row = tk.Frame(parent)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=f"{label}", width=16, anchor="e").pack(side=tk.LEFT, padx=(0, 6))
            tk.Label(row, text="Min:", anchor="e").pack(side=tk.LEFT)
            e_min = tk.Entry(row, width=entry_width)
            e_min.insert(0, str(default_min))
            e_min.pack(side=tk.LEFT, padx=4)
            tk.Label(row, text="Max:", anchor="e").pack(side=tk.LEFT)
            e_max = tk.Entry(row, width=entry_width)
            e_max.insert(0, str(default_max))
            e_max.pack(side=tk.LEFT, padx=4)
            return e_min, e_max

        # ---- Spectrogram dB ----
        spec_frame = tk.LabelFrame(slider_panel, text="Spectrogram Color Range (dB)  —  dB Min also sets AE count threshold", padx=6, pady=4)
        spec_frame.pack(fill=tk.X, pady=(0, 4))

        self.entry_db_min, self.entry_db_max = make_entry_row(
            spec_frame, "dB Range:", self.db_min, self.db_max
        )

        # Hint label
        tk.Label(
            spec_frame,
            text="ℹ  Changing dB Min will recompute AE counts (amplitude threshold = 10^(dBmin/20) V)",
            fg="#555555", font=("TkDefaultFont", 8), anchor="w"
        ).pack(anchor="w", padx=4)

        self.btn_apply_db = tk.Button(
            spec_frame, text="Apply dB  (recalculates counts)", command=self.apply_db_range
        )
        self.btn_apply_db.pack(anchor="w", padx=4, pady=(4, 0))

        self.entry_db_min.bind("<Return>", lambda e: self.apply_db_range())
        self.entry_db_max.bind("<Return>", lambda e: self.apply_db_range())

        # ---- Time-domain Y-axis ranges ----
        td_frame = tk.LabelFrame(slider_panel, text="Time-Domain Plot Y-Axis Ranges", padx=6, pady=4)
        td_frame.pack(fill=tk.X)

        self.entry_rms_min, self.entry_rms_max = make_entry_row(
            td_frame, "RMS (V):", self.rms_ymin, self.rms_ymax
        )
        self.entry_peak_min, self.entry_peak_max = make_entry_row(
            td_frame, "Peak (V):", self.peak_ymin, self.peak_ymax
        )
        self.entry_counts_min, self.entry_counts_max = make_entry_row(
            td_frame, "Cum. Counts:", self.counts_ymin, self.counts_ymax
        )

        self.btn_apply_td = tk.Button(
            td_frame, text="Apply Ranges", command=self.apply_td_ranges
        )
        self.btn_apply_td.pack(anchor="w", padx=4, pady=(4, 0))

        for e in (self.entry_rms_min, self.entry_rms_max,
                  self.entry_peak_min, self.entry_peak_max,
                  self.entry_counts_min, self.entry_counts_max):
            e.bind("<Return>", lambda ev: self.apply_td_ranges())

        # ==========================================
        # --- Matplotlib Figure ---
        # ==========================================
        self.canvas_frame = tk.Frame(self.scrollable_frame)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.fig = plt.figure(figsize=(12, 14))
        gs = GridSpec(4, 1, figure=self.fig, height_ratios=[2, 1, 1, 1])

        self.ax_spec   = self.fig.add_subplot(gs[0, 0])
        self.ax_rms    = self.fig.add_subplot(gs[1, 0])
        self.ax_peak   = self.fig.add_subplot(gs[2, 0])
        self.ax_counts = self.fig.add_subplot(gs[3, 0])

        self.ax_spec.set_title('Spectrogram (dB) - Waiting for file...')
        self.ax_rms.set_title('RMS Trend - Waiting for file...')
        self.ax_peak.set_title('Peak Amplitude Trend - Waiting for file...')
        self.ax_counts.set_title('Cumulative AE Counts - Waiting for file...')

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.canvas.get_tk_widget().bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.get_tk_widget().bind("<Button-4>", lambda e: self.main_canvas.yview_scroll(-1, "units"))
        self.canvas.get_tk_widget().bind("<Button-5>", lambda e: self.main_canvas.yview_scroll(1, "units"))

        self.fig.subplots_adjust(left=0.08, right=0.92, top=0.95, bottom=0.05, wspace=0.15, hspace=0.45)

        # --- Diagnostic Report ---
        interp_frame = tk.LabelFrame(self.scrollable_frame, text="Automated Diagnostic Report", padx=10, pady=10)
        interp_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.text_interp = scrolledtext.ScrolledText(interp_frame, height=10, wrap=tk.WORD, bg="#f5f5f5", fg="black")
        self.text_interp.pack(fill=tk.BOTH, expand=True)
        self.text_interp.config(state=tk.DISABLED)

        self.root.protocol("WM_DELETE_WINDOW", self.close_prog)
        self.cbar = None

    # ------------------------------------------------------------------
    # OS Agnostic Mousewheel Scroll
    # ------------------------------------------------------------------
    def _on_mousewheel(self, event):
        delta = event.delta
        # Windows usually fires 120 per click, Mac fires 1 per click.
        scroll_amount = int(-1 * (delta / 120)) if abs(delta) >= 120 else int(-1 * delta)
        self.main_canvas.yview_scroll(scroll_amount, "units")

    # ------------------------------------------------------------------
    # Count recomputation from dB threshold
    # ------------------------------------------------------------------

    def _compute_counts_from_db(self, signal, win, step, db_threshold):
        """
        Recompute per-window AE counts using an amplitude threshold
        derived from the dB Min value.

        Conversion:  amplitude_threshold = 10 ^ (dB_threshold / 20)
        (Based on:   dB = 20 * log10(amplitude)  for voltage/pressure signals)
        """
        N = len(signal)
        amp_threshold = 10.0 ** (db_threshold / 20.0)
        counts = []
        for i in range(0, N - win + 1, step):
            segment = signal[i:i + win]
            counts.append(int(np.sum(np.abs(segment) > amp_threshold)))
        return np.array(counts)

    # ------------------------------------------------------------------
    # dB Entry Apply  →  also recalculates counts
    # ------------------------------------------------------------------

    def apply_db_range(self):
        """
        Read dB min/max and apply to ALL plots:
          1. Spectrogram colormap clim
          2. Recompute AE counts (amplitude threshold = 10^(dBmin/20))
          3. Rescale RMS, Peak, Cumulative Counts Y-axes proportionally
             using the dB range as a unified scaling factor.
        """
        try:
            new_min = float(self.entry_db_min.get())
            new_max = float(self.entry_db_max.get())
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter valid numbers for dB Min and dB Max.")
            return

        if new_min >= new_max:
            messagebox.showwarning("Invalid Range", "dB Min must be less than dB Max.")
            return

        self.db_min = new_min
        self.db_max = new_max

        # 1. Update spectrogram colormap range
        if hasattr(self, 'im'):
            self.im.set_clim(self.db_min, self.db_max)
            self.canvas.draw_idle()

        if self._cached_signal is None or self._cached_rms is None:
            return

        # 2. Recompute counts using dB Min as amplitude threshold
        new_counts        = self._compute_counts_from_db(
            self._cached_signal, self._cached_win, self._cached_step,
            db_threshold=self.db_min
        )
        new_counts_cumsum = np.cumsum(new_counts)

        self._cached_counts        = new_counts
        self._cached_counts_cumsum = new_counts_cumsum

        # 3. Rescale all time-domain Y-axes using the dB range as a
        #    proportional zoom factor relative to the full data range.
        db_span = self.db_max - self.db_min          # always > 0 (validated above)
        ratio   = 10.0 ** (db_span / 20.0)           # linear amplitude ratio

        rms_data_max    = float(np.max(self._cached_rms))
        peak_data_max   = float(np.max(self._cached_peak))
        counts_data_max = float(np.max(new_counts_cumsum)) if np.max(new_counts_cumsum) > 0 else 1.0

        amp_min = 10.0 ** (self.db_min / 20.0)       # amplitude at dB min
        amp_max = 10.0 ** (self.db_max / 20.0)       # amplitude at dB max

        # Normalise to each plot's own data range
        def _scale(data_max, a_min, a_max):
            """Map amp range [a_min, a_max] → Y range for a given data_max."""
            sig_ref = float(np.percentile(np.abs(self._cached_signal), 99)) or 1.0
            y_lo = max(0.0, (a_min / sig_ref) * data_max)
            y_hi = min((a_max / sig_ref) * data_max * 1.15, data_max * ratio * 1.15)
            if y_hi <= y_lo:
                y_hi = y_lo + data_max * 0.1 + 1e-6
            return y_lo, y_hi

        self.rms_ymin,    self.rms_ymax    = _scale(rms_data_max,    amp_min, amp_max)
        self.peak_ymin,   self.peak_ymax   = _scale(peak_data_max,   amp_min, amp_max)

        counts_pad        = max(counts_data_max * 0.15, 1.0)
        self.counts_ymin  = 0.0
        self.counts_ymax  = counts_data_max + counts_pad

        # Update all entry boxes
        def _set(entry, val, dec=4):
            entry.delete(0, tk.END)
            entry.insert(0, f"{val:.{dec}f}")

        _set(self.entry_rms_min,    self.rms_ymin)
        _set(self.entry_rms_max,    self.rms_ymax)
        _set(self.entry_peak_min,   self.peak_ymin)
        _set(self.entry_peak_max,   self.peak_ymax)
        _set(self.entry_counts_min, self.counts_ymin, dec=0)
        _set(self.entry_counts_max, self.counts_ymax, dec=0)

        # Redraw all time-domain plots
        self._redraw_td_plots()

        # Refresh diagnostic report
        db_mean    = float(np.mean(self._cached_Pxx_dB)) if self._cached_Pxx_dB is not None else 0.0
        db_std     = float(np.std(self._cached_Pxx_dB))  if self._cached_Pxx_dB is not None else 0.0
        db_max_val = float(np.max(self._cached_Pxx_dB))  if self._cached_Pxx_dB is not None else self.db_max

        self.generate_interpretation(
            self._cached_name, self._cached_rms, self._cached_peak,
            new_counts, db_max=db_max_val, db_mean=db_mean, db_std=db_std
        )

    # ------------------------------------------------------------------
    # Time-domain Entry Apply
    # ------------------------------------------------------------------

    def apply_td_ranges(self):
        errors = []
        try:
            rms_min = float(self.entry_rms_min.get())
            rms_max = float(self.entry_rms_max.get())
            if rms_min >= rms_max:
                errors.append("RMS Min must be less than RMS Max.")
        except ValueError:
            errors.append("Invalid RMS range values.")

        try:
            peak_min = float(self.entry_peak_min.get())
            peak_max = float(self.entry_peak_max.get())
            if peak_min >= peak_max:
                errors.append("Peak Min must be less than Peak Max.")
        except ValueError:
            errors.append("Invalid Peak range values.")

        try:
            counts_min = float(self.entry_counts_min.get())
            counts_max = float(self.entry_counts_max.get())
            if counts_min >= counts_max:
                errors.append("Counts Min must be less than Counts Max.")
        except ValueError:
            errors.append("Invalid Counts range values.")

        if errors:
            messagebox.showwarning("Invalid Input", "\n".join(errors))
            return

        self.rms_ymin    = rms_min
        self.rms_ymax    = rms_max
        self.peak_ymin   = peak_min
        self.peak_ymax   = peak_max
        self.counts_ymin = counts_min
        self.counts_ymax = counts_max
        self._redraw_td_plots()

    def _redraw_td_plots(self):
        if self._cached_rms is None:
            return

        rms       = self._cached_rms
        peak      = self._cached_peak
        counts_cs = self._cached_counts_cumsum
        time_axis = self._cached_time_axis
        name      = self._cached_name

        self.ax_rms.clear()
        self.ax_rms.plot(time_axis, rms, 'b-', linewidth=1.2)
        self.ax_rms.set_ylim(self.rms_ymin, self.rms_ymax)
        self.ax_rms.set_ylabel('RMS (V)')
        self.ax_rms.set_title(f'RMS Trend - {name}')
        self.ax_rms.grid(True)

        self.ax_peak.clear()
        self.ax_peak.plot(time_axis, peak, 'r-', linewidth=1.2)
        self.ax_peak.set_ylim(self.peak_ymin, self.peak_ymax)
        self.ax_peak.set_ylabel('Peak (V)')
        self.ax_peak.set_title(f'Peak Amplitude Trend - {name}')
        self.ax_peak.grid(True)

        self.ax_counts.clear()
        self.ax_counts.plot(time_axis, counts_cs, color='#EDB120', linewidth=1.5)
        self.ax_counts.fill_between(time_axis, counts_cs, alpha=0.3, color='#EDB120')
        self.ax_counts.set_ylim(self.counts_ymin, self.counts_ymax)
        self.ax_counts.set_ylabel('Cumulative Counts')
        self.ax_counts.set_xlabel('Time (Window Number)')
        self.ax_counts.set_title(
            f'Cumulative AE Counts - {name}  '
            f'[threshold = 10^({self.db_min:.1f}/20) = {10**(self.db_min/20):.5f} V]'
        )
        self.ax_counts.grid(True)

        self.canvas.draw_idle()

    # ------------------------------------------------------------------
    # File Handling
    # ------------------------------------------------------------------

    def update_titles_pre_compute(self, event=None):
        selected_name = self.combo_files.get()
        if not selected_name:
            return
        self.ax_spec.set_title(f'Spectrogram (dB) - {selected_name}')
        self.ax_rms.set_title(f'RMS Trend - {selected_name}')
        self.ax_peak.set_title(f'Peak Amplitude Trend - {selected_name}')
        self.ax_counts.set_title(f'Cumulative AE Counts - {selected_name}')
        self.fig.suptitle("", color='black')
        self.canvas.draw_idle()

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
            messagebox.showinfo("Files Loaded", f"Successfully loaded {len(filepaths)} file(s).")

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    def compute_and_plot(self):
        selected_name = self.combo_files.get()
        if not selected_name:
            messagebox.showwarning("Warning", "Please load and select a file first.")
            return

        filepath = self.file_dict[selected_name]
        self.fig.suptitle(f"Processing: {selected_name}...", fontsize=14, fontweight='bold', color='red')
        self.canvas.draw()
        self.root.update()

        try:
            data   = np.fromfile(filepath, dtype=np.uint16)
            signal = data.astype(np.float64) / 4096.0 * 3.3
            signal = signal - np.mean(signal)

            N    = len(signal)
            win  = int(round(self.window_time * self.fs))
            step = int(round(win * (1 - self.overlap)))

            # Cache signal params for recomputation on dB change
            self._cached_signal = signal
            self._cached_win    = win
            self._cached_step   = step

            # Initial counts use auto dB min (set below after spectrogram)
            # We compute RMS and Peak first (independent of threshold)
            file_rms  = []
            file_peak = []

            for i in range(0, N - win + 1, step):
                segment = signal[i:i + win]
                file_rms.append(np.sqrt(np.mean(segment ** 2)))
                file_peak.append(np.max(np.abs(segment)))

            file_rms  = np.array(file_rms)
            file_peak = np.array(file_peak)
            time_axis = np.arange(1, len(file_rms) + 1)

            # --- Spectrogram (Calculate without hijacking ax drawing) ---
            self.ax_spec.clear()
            
            # Using matplotlib.mlab safely calculates the array data 
            # without triggering matplotlib to auto-draw a second time.
            Pxx, freqs, bins = mlab.specgram(signal, NFFT=256, Fs=self.fs, noverlap=192)

            Pxx_dB     = 10 * np.log10(Pxx + 1e-12)
            db_max_val = float(np.max(Pxx_dB))
            db_mean    = float(np.mean(Pxx_dB))
            db_std     = float(np.std(Pxx_dB))

            # Cache Pxx_dB for later report refreshes
            self._cached_Pxx_dB = Pxx_dB

            # Auto-set dB range from data percentiles
            auto_db_min = float(np.percentile(Pxx_dB, 5))
            auto_db_max = float(np.percentile(Pxx_dB, 95))
            self.db_min = auto_db_min
            self.db_max = auto_db_max
            self.entry_db_min.delete(0, tk.END)
            self.entry_db_min.insert(0, f"{auto_db_min:.1f}")
            self.entry_db_max.delete(0, tk.END)
            self.entry_db_max.insert(0, f"{auto_db_max:.1f}")

            # --- Compute counts using auto dB Min as initial threshold ---
            file_counts        = self._compute_counts_from_db(signal, win, step, db_threshold=self.db_min)
            file_counts_cumsum = np.cumsum(file_counts)

            # --- Cache all computed data ---
            self._cached_rms           = file_rms
            self._cached_peak          = file_peak
            self._cached_counts        = file_counts
            self._cached_counts_cumsum = file_counts_cumsum
            self._cached_time_axis     = time_axis
            self._cached_name          = selected_name

            # --- Auto-set Y-axis range entries ---
            rms_pad    = max(np.max(file_rms) * 0.15, 0.001)
            peak_pad   = max(np.max(file_peak) * 0.15, 0.001)
            counts_pad = max(np.max(file_counts_cumsum) * 0.15, 1) if np.max(file_counts_cumsum) > 0 else 10.0

            self.rms_ymin    = 0.0
            self.rms_ymax    = float(np.max(file_rms) + rms_pad)
            self.peak_ymin   = 0.0
            self.peak_ymax   = float(np.max(file_peak) + peak_pad)
            self.counts_ymin = 0.0
            self.counts_ymax = float(np.max(file_counts_cumsum) + counts_pad)

            def _set_entry(entry, value, decimals=4):
                entry.delete(0, tk.END)
                entry.insert(0, f"{value:.{decimals}f}")

            _set_entry(self.entry_rms_min,    self.rms_ymin)
            _set_entry(self.entry_rms_max,    self.rms_ymax)
            _set_entry(self.entry_peak_min,   self.peak_ymin)
            _set_entry(self.entry_peak_max,   self.peak_ymax)
            _set_entry(self.entry_counts_min, self.counts_ymin, decimals=0)
            _set_entry(self.entry_counts_max, self.counts_ymax, decimals=0)

            # --- Draw spectrogram (Cleanly via pcolormesh) ---
            self.im = self.ax_spec.pcolormesh(
                bins, freqs, Pxx_dB,
                shading='gouraud', cmap='viridis',
                vmin=self.db_min, vmax=self.db_max
            )
            self.ax_spec.set_ylabel('Frequency (Hz)')
            self.ax_spec.set_xlabel('Time (s)')
            self.ax_spec.set_title(f'Spectrogram (dB) - {selected_name}')

            divider = make_axes_locatable(self.ax_spec)
            if self.cbar is not None:
                try:
                    self.cbar.remove()
                except Exception:
                    pass
            cax = divider.append_axes("right", size="3%", pad=0.05)
            self.cbar = self.fig.colorbar(self.im, cax=cax)
            self.cbar.set_label('Power (dB)')

            # --- Draw time-domain plots ---
            self._redraw_td_plots()

            self.fig.suptitle(f"Analysis Complete: {selected_name}", fontsize=14, fontweight='bold', color='black')
            self.canvas.draw()

            self.generate_interpretation(
                selected_name, file_rms, file_peak, file_counts,
                db_max_val, db_mean, db_std
            )

            self.main_canvas.update_idletasks()
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
            self.main_canvas.yview_moveto(0)

        except Exception as e:
            self.fig.suptitle("", color='black')
            self.canvas.draw()
            messagebox.showerror("Error", f"An error occurred while processing the file:\n{str(e)}")

    # ------------------------------------------------------------------
    # Diagnostic Report
    # ------------------------------------------------------------------

    def generate_interpretation(self, filename, rms, peak, counts, db_max, db_mean, db_std):
        time_windows = np.arange(1, len(rms) + 1)
        max_peak     = np.max(peak)
        total_counts = int(np.sum(counts))

        amp_threshold = 10.0 ** (self.db_min / 20.0)

        slope, _ = np.polyfit(time_windows, rms, 1)
        if slope > 0.0001:
            trend_status = "Increasing energy trend (Possible progressing anomaly/wear)"
        elif slope < -0.0001:
            trend_status = "Decreasing energy trend"
        else:
            trend_status = "Stable energy levels"

        crest_factors = peak / (rms + 1e-9)
        avg_cf = np.mean(crest_factors)

        if avg_cf > 4.0 and total_counts > 0:
            signal_type = "Burst Emission (Distinct impacts, crack growth, or pitting)"
        elif total_counts > 0:
            signal_type = "Continuous Emission (Steady friction, flow, or uniform wear)"
        else:
            signal_type = "Background Noise Only"

        dynamic_threshold  = np.mean(peak) + (2 * np.std(peak))
        significant_events = np.where(peak > dynamic_threshold)[0]

        interp_text  = f"--- AUTOMATED DIAGNOSTIC REPORT: {filename} ---\n"
        interp_text += f"🔧 COUNT THRESHOLD:\n"
        interp_text += f"  • dB Min setting : {self.db_min:.1f} dB\n"
        interp_text += f"  • Amplitude threshold : {amp_threshold:.6f} V  (= 10^({self.db_min:.1f}/20))\n\n"
        interp_text += f"📊 OVERALL BEHAVIOR:\n"
        interp_text += f"  • Signal Classification: {signal_type}\n"
        interp_text += f"  • Energy Trend: {trend_status}\n"
        interp_text += f"  • Total Cumulative AE Counts (at current threshold): {total_counts}\n\n"
        interp_text += f"📈 SPECTROGRAM STATS:\n"
        interp_text += f"  • dB Max: {db_max:.2f}\n"
        interp_text += f"  • dB Mean: {db_mean:.2f}\n"
        interp_text += f"  • dB Std: {db_std:.2f}\n\n"
        interp_text += f"⚠️ EVENT DETECTION:\n"

        if len(significant_events) > 0:
            event_windows = significant_events + 1
            interp_text += f"  • Detected {len(significant_events)} significant high-energy anomalies.\n"
            if len(event_windows) <= 10:
                interp_text += f"  • Critical Windows: {', '.join(map(str, event_windows))}\n"
            else:
                interp_text += f"  • Critical Windows: {', '.join(map(str, event_windows[:10]))}... (and {len(event_windows)-10} more)\n"
            interp_text += f"  • Max Peak: {max_peak:.4f} V at window {np.argmax(peak) + 1}\n"
        else:
            interp_text += "  • No distinct high-energy spikes detected above normal operating variance.\n"

        self.text_interp.config(state=tk.NORMAL)
        self.text_interp.delete("1.0", tk.END)
        self.text_interp.insert(tk.END, interp_text)
        self.text_interp.config(state=tk.DISABLED)

    # ------------------------------------------------------------------

    def close_prog(self):
        plt.close('all')
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AEAnalyzerApp(root)
    root.mainloop()