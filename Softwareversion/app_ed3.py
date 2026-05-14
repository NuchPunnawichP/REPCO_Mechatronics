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
        self.root.title("Ultimate Acoustic Emission (AE) Analyzer")
        self.root.geometry("1100x900")

        # --- Variables ---
        self.fs = 4000
        self.window_time = 0.1
        self.overlap = 0.0
        self.file_paths = []
        self.file_dict = {}

        # Spectrogram dB range (Negative dBFS)
        self.spec_db_min = -90
        self.spec_db_max = -20
        
        # AE Count Threshold (Positive dBAE, where 0 dB = 1 microVolt)
        self.ae_threshold_dbae = 95.0 

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

        def make_entry_row(parent, label, default_max, entry_width=10):
            row = tk.Frame(parent)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=f"{label}", width=18, anchor="e").pack(side=tk.LEFT, padx=(0, 6))
            tk.Label(row, text="Max Y-Axis:", anchor="e").pack(side=tk.LEFT)
            e_max = tk.Entry(row, width=entry_width)
            e_max.insert(0, str(default_max))
            e_max.pack(side=tk.LEFT, padx=4)
            return e_max

        # ---- Spectrogram dB ----
        spec_frame = tk.LabelFrame(slider_panel, text="Spectrogram Color Range (Negative dBFS)", padx=6, pady=4)
        spec_frame.pack(fill=tk.X, pady=(0, 4))

        row_spec = tk.Frame(spec_frame)
        row_spec.pack(fill=tk.X, pady=3)
        tk.Label(row_spec, text="dBFS Range:", width=18, anchor="e").pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(row_spec, text="Min:").pack(side=tk.LEFT)
        self.entry_spec_min = tk.Entry(row_spec, width=10)
        self.entry_spec_min.insert(0, str(self.spec_db_min))
        self.entry_spec_min.pack(side=tk.LEFT, padx=4)
        tk.Label(row_spec, text="Max:").pack(side=tk.LEFT)
        self.entry_spec_max = tk.Entry(row_spec, width=10)
        self.entry_spec_max.insert(0, str(self.spec_db_max))
        self.entry_spec_max.pack(side=tk.LEFT, padx=4)
        
        self.btn_apply_spec = tk.Button(spec_frame, text="Apply Colors", command=self.apply_spec_range)
        self.btn_apply_spec.pack(anchor="w", padx=4, pady=(4, 0))

        # ---- Time-domain Y-axis ranges & AE Count Threshold ----
        td_frame = tk.LabelFrame(slider_panel, text="Time-Domain Ranges & AE Threshold", padx=6, pady=4)
        td_frame.pack(fill=tk.X)
        
        # AE Threshold Input
        thresh_row = tk.Frame(td_frame)
        thresh_row.pack(fill=tk.X, pady=(3, 10))
        tk.Label(thresh_row, text="Target Threshold (Positive dBAE):", font=("TkDefaultFont", 9, "bold")).pack(side=tk.LEFT, padx=(4, 6))
        self.entry_ae_thresh = tk.Entry(thresh_row, width=10)
        self.entry_ae_thresh.insert(0, str(self.ae_threshold_dbae))
        self.entry_ae_thresh.pack(side=tk.LEFT, padx=4)
        tk.Label(thresh_row, text="(0 dB = 1 µV)", fg="#555555").pack(side=tk.LEFT, padx=4)

        # Plot Maximums
        self.entry_rms_max = make_entry_row(td_frame, "RMS (V):", self.rms_ymax)
        self.entry_peak_max = make_entry_row(td_frame, "Peak (V):", self.peak_ymax)
        self.entry_win_counts_max = make_entry_row(td_frame, "Win. Counts:", self.win_counts_ymax)
        self.entry_cum_counts_max = make_entry_row(td_frame, "Cum. Counts:", self.cum_counts_ymax)

        self.btn_apply_td = tk.Button(td_frame, text="Apply Ranges & Recalculate Counts", command=self.apply_td_ranges)
        self.btn_apply_td.pack(anchor="w", padx=4, pady=(4, 0))

        # ==========================================
        # --- Matplotlib Figure (5 Subplots) ---
        # ==========================================
        self.canvas_frame = tk.Frame(self.scrollable_frame)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.fig = plt.figure(figsize=(10, 16)) 
        gs = GridSpec(5, 1, figure=self.fig, height_ratios=[2, 1, 1, 1, 1])

        self.ax_spec = self.fig.add_subplot(gs[0, 0])
        self.ax_rms = self.fig.add_subplot(gs[1, 0])
        self.ax_peak = self.fig.add_subplot(gs[2, 0])
        self.ax_win_counts = self.fig.add_subplot(gs[3, 0])
        self.ax_cum_counts = self.fig.add_subplot(gs[4, 0])

        self.update_titles_pre_compute()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.get_tk_widget().bind("<MouseWheel>", self._on_mousewheel)

        # FIX: Changed 'top' from 0.96 to 0.92 to give the main title room to breathe
        self.fig.subplots_adjust(left=0.08, right=0.92, top=0.92, bottom=0.04, wspace=0.15, hspace=0.55)

        # --- Diagnostic Report ---
        interp_frame = tk.LabelFrame(self.scrollable_frame, text="Automated Diagnostic Report", padx=10, pady=10)
        interp_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.text_interp = scrolledtext.ScrolledText(interp_frame, height=10, wrap=tk.WORD, bg="#f5f5f5", fg="black")
        self.text_interp.pack(fill=tk.BOTH, expand=True)
        self.text_interp.config(state=tk.DISABLED)

        self.root.protocol("WM_DELETE_WINDOW", self.close_prog)
        self.cbar = None

    def _on_mousewheel(self, event):
        delta = event.delta
        scroll_amount = int(-1 * (delta / 120)) if abs(delta) >= 120 else int(-1 * delta)
        self.main_canvas.yview_scroll(scroll_amount, "units")

    # ------------------------------------------------------------------
    # Standardized AE dBAE Calculation
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
    # UI Application Functions
    # ------------------------------------------------------------------
    def apply_spec_range(self):
        try:
            self.spec_db_min = float(self.entry_spec_min.get())
            self.spec_db_max = float(self.entry_spec_max.get())
            if hasattr(self, 'im'):
                self.im.set_clim(self.spec_db_min, self.spec_db_max)
                self.canvas.draw_idle()
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter valid numbers for Spectrogram dB.")

    def apply_td_ranges(self):
        try:
            self.rms_ymax = float(self.entry_rms_max.get())
            self.peak_ymax = float(self.entry_peak_max.get())
            self.win_counts_ymax = float(self.entry_win_counts_max.get())
            self.cum_counts_ymax = float(self.entry_cum_counts_max.get())
            new_ae_thresh = float(self.entry_ae_thresh.get())
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please ensure all time-domain and threshold inputs are numbers.")
            return

        if self._cached_signal is not None:
            self.ae_threshold_dbae = new_ae_thresh
            
            # Recalculate based on new standard dBAE threshold
            new_counts, _ = self._compute_counts_from_dbae(
                self._cached_signal, self._cached_win, self._cached_step, self.ae_threshold_dbae
            )
            self._cached_window_counts = new_counts
            self._cached_cum_counts = np.cumsum(new_counts)
            
            self.generate_interpretation(self._cached_name, self._cached_rms, self._cached_peak, new_counts)

        self._redraw_td_plots()

    def _redraw_td_plots(self):
        if self._cached_rms is None:
            return

        rms = self._cached_rms
        peak = self._cached_peak
        win_counts = self._cached_window_counts
        cum_counts = self._cached_cum_counts
        time_axis = self._cached_time_axis
        name = self._cached_name
        v_thresh = 1e-6 * (10.0 ** (self.ae_threshold_dbae / 20.0))

        # --- Dynamic Auto-Scaling Check ---
        update_ui = False
        
        if np.max(rms) > self.rms_ymax:
            self.rms_ymax = float(np.max(rms) * 1.15)
            update_ui = True
        if np.max(peak) > self.peak_ymax:
            self.peak_ymax = float(np.max(peak) * 1.15)
            update_ui = True
        if np.max(win_counts) > self.win_counts_ymax:
            self.win_counts_ymax = float(np.max(win_counts) * 1.15)
            update_ui = True
        if np.max(cum_counts) > self.cum_counts_ymax:
            self.cum_counts_ymax = float(np.max(cum_counts) * 1.15)
            update_ui = True

        if update_ui:
            self.entry_rms_max.delete(0, tk.END)
            self.entry_rms_max.insert(0, f"{self.rms_ymax:.4f}")
            self.entry_peak_max.delete(0, tk.END)
            self.entry_peak_max.insert(0, f"{self.peak_ymax:.4f}")
            self.entry_win_counts_max.delete(0, tk.END)
            self.entry_win_counts_max.insert(0, f"{self.win_counts_ymax:.0f}")
            self.entry_cum_counts_max.delete(0, tk.END)
            self.entry_cum_counts_max.insert(0, f"{self.cum_counts_ymax:.0f}")

        # 1. RMS
        self.ax_rms.clear()
        self.ax_rms.plot(time_axis, rms, 'b-', linewidth=1.2)
        self.ax_rms.set_ylim(0, self.rms_ymax)
        self.ax_rms.set_ylabel('RMS (V)')
        self.ax_rms.set_title(f'RMS Trend - {name}')
        self.ax_rms.grid(True)

        # 2. Peak
        self.ax_peak.clear()
        self.ax_peak.plot(time_axis, peak, 'r-', linewidth=1.2)
        self.ax_peak.set_ylim(0, self.peak_ymax)
        self.ax_peak.set_ylabel('Peak (V)')
        self.ax_peak.set_title(f'Peak Amplitude Trend - {name}')
        self.ax_peak.grid(True)

        # 3. Counts at Time (Per Window Bar)
        self.ax_win_counts.clear()
        self.ax_win_counts.bar(time_axis, win_counts, color='#EDB120', edgecolor='none')
        self.ax_win_counts.set_ylim(0, self.win_counts_ymax)
        self.ax_win_counts.set_ylabel('Counts')
        self.ax_win_counts.set_title(f'Count at Time (Per Window) - {name} [{self.ae_threshold_dbae} dBAE]')
        self.ax_win_counts.grid(True)

        # 4. Sum Count at Time (Cumulative Fill)
        self.ax_cum_counts.clear()
        self.ax_cum_counts.plot(time_axis, cum_counts, color='#009933', linewidth=1.5)
        self.ax_cum_counts.fill_between(time_axis, cum_counts, alpha=0.3, color='#009933')
        self.ax_cum_counts.set_ylim(0, self.cum_counts_ymax)
        self.ax_cum_counts.set_ylabel('Sum Counts')
        self.ax_cum_counts.set_xlabel('Time (Window Number)')
        self.ax_cum_counts.set_title(f'Sum Count at Time (Cumulative) - {name} [{self.ae_threshold_dbae} dBAE = {v_thresh:.6f} V]')
        self.ax_cum_counts.grid(True)

        self.canvas.draw_idle()

    def update_titles_pre_compute(self, event=None):
        name = self.combo_files.get() if self.combo_files.get() else "Waiting for file..."
        self.ax_spec.set_title(f'Spectrogram (dBFS) - {name}')
        self.ax_rms.set_title(f'RMS Trend - {name}')
        self.ax_peak.set_title(f'Peak Amplitude Trend - {name}')
        self.ax_win_counts.set_title(f'Count at Time (Per Window) - {name}')
        self.ax_cum_counts.set_title(f'Sum Count at Time (Cumulative) - {name}')
        # FIX: Added y=0.98 to pin the empty title securely to the top
        self.fig.suptitle("", color='black', y=0.98)
        if hasattr(self, 'canvas'):
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

    def compute_and_plot(self):
        selected_name = self.combo_files.get()
        if not selected_name:
            messagebox.showwarning("Warning", "Please load and select a file first.")
            return

        filepath = self.file_dict[selected_name]
        # FIX: Added y=0.98 to pin the loading text to the top
        self.fig.suptitle(f"Processing: {selected_name}...", fontsize=14, fontweight='bold', color='red', y=0.98)
        self.canvas.draw()
        self.root.update()

        try:
            data = np.fromfile(filepath, dtype=np.uint16)
            signal = data.astype(np.float64) / 4096.0 * 3.3
            signal = signal - np.mean(signal)

            N = len(signal)
            win = int(round(self.window_time * self.fs))
            step = int(round(win * (1 - self.overlap)))

            self._cached_signal = signal
            self._cached_win = win
            self._cached_step = step

            file_rms = []
            file_peak = []

            for i in range(0, N - win + 1, step):
                segment = signal[i:i + win]
                file_rms.append(np.sqrt(np.mean(segment ** 2)))
                file_peak.append(np.max(np.abs(segment)))

            file_rms = np.array(file_rms)
            file_peak = np.array(file_peak)
            time_axis = np.arange(1, len(file_rms) + 1)

            # --- Spectrogram ---
            self.ax_spec.clear()
            Pxx, freqs, bins = mlab.specgram(signal, NFFT=256, Fs=self.fs, noverlap=192)
            Pxx_dB = 10 * np.log10(Pxx + 1e-12)

            # --- Compute counts ---
            file_win_counts, _ = self._compute_counts_from_dbae(signal, win, step, self.ae_threshold_dbae)
            file_cum_counts = np.cumsum(file_win_counts)

            self._cached_rms = file_rms
            self._cached_peak = file_peak
            self._cached_window_counts = file_win_counts
            self._cached_cum_counts = file_cum_counts
            self._cached_time_axis = time_axis
            self._cached_name = selected_name

            # Auto-set Y-axis limits securely based on data if the default is too low
            self.rms_ymax = max(self.rms_ymax, float(np.max(file_rms) * 1.15))
            self.peak_ymax = max(self.peak_ymax, float(np.max(file_peak) * 1.15))
            self.win_counts_ymax = max(100.0, float(np.max(file_win_counts) * 1.15))
            self.cum_counts_ymax = max(100.0, float(np.max(file_cum_counts) * 1.15))

            def _set_entry(entry, value, decimals=4):
                entry.delete(0, tk.END)
                entry.insert(0, f"{value:.{decimals}f}")

            _set_entry(self.entry_rms_max, self.rms_ymax)
            _set_entry(self.entry_peak_max, self.peak_ymax)
            _set_entry(self.entry_win_counts_max, self.win_counts_ymax, decimals=0)
            _set_entry(self.entry_cum_counts_max, self.cum_counts_ymax, decimals=0)

            # Draw spectrogram 
            self.im = self.ax_spec.pcolormesh(
                bins, freqs, Pxx_dB,
                shading='gouraud', cmap='viridis',
                vmin=self.spec_db_min, vmax=self.spec_db_max
            )
            self.ax_spec.set_ylabel('Frequency (Hz)')
            self.ax_spec.set_xlabel('Time (s)')
            self.ax_spec.set_title(f'Spectrogram (dBFS) - {selected_name}')

            divider = make_axes_locatable(self.ax_spec)
            if self.cbar is not None:
                try:
                    self.cbar.remove()
                except Exception:
                    pass
            cax = divider.append_axes("right", size="3%", pad=0.05)
            self.cbar = self.fig.colorbar(self.im, cax=cax)
            self.cbar.set_label('Power (dBFS)')

            self._redraw_td_plots()

            # FIX: Added y=0.98 to pin the main title to the top
            self.fig.suptitle(f"Analysis Complete: {selected_name}", fontsize=14, fontweight='bold', color='black', y=0.98)
            self.canvas.draw()

            self.generate_interpretation(selected_name, file_rms, file_peak, file_win_counts)

            self.main_canvas.update_idletasks()
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
            self.main_canvas.yview_moveto(0)

        except Exception as e:
            self.fig.suptitle("", color='black')
            self.canvas.draw()
            messagebox.showerror("Error", f"An error occurred while processing the file:\n{str(e)}")

    def generate_interpretation(self, filename, rms, peak, counts):
        time_windows = np.arange(1, len(rms) + 1)
        max_peak = np.max(peak)
        total_counts = int(np.sum(counts))
        amp_threshold_v = 1e-6 * (10.0 ** (self.ae_threshold_dbae / 20.0))

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

        dynamic_threshold = np.mean(peak) + (2 * np.std(peak))
        significant_events = np.where(peak > dynamic_threshold)[0]

        interp_text  = f"--- AUTOMATED DIAGNOSTIC REPORT: {filename} ---\n"
        interp_text += f"🔧 COUNT THRESHOLD:\n"
        interp_text += f"  • Target AE Level : {self.ae_threshold_dbae} dBAE\n"
        interp_text += f"  • Required Voltage: {amp_threshold_v:.6f} V\n\n"
        interp_text += f"📊 OVERALL BEHAVIOR:\n"
        interp_text += f"  • Signal Classification: {signal_type}\n"
        interp_text += f"  • Energy Trend: {trend_status}\n"
        interp_text += f"  • Total Cumulative AE Counts: {total_counts}\n\n"
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

    def close_prog(self):
        plt.close('all')
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AEAnalyzerApp(root)
    root.mainloop()