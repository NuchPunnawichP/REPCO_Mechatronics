import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

class AEAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Acoustic Emission (AE) Analyzer")
        self.root.geometry("1000x750") 
        
        # --- Variables ---
        self.fs = 4000
        self.window_time = 0.1
        self.overlap = 0.0
        self.file_paths = []
        self.file_dict = {}
        
        # ==========================================
        # --- SROLLABLE MAIN WINDOW SETUP ---
        # ==========================================
        self.main_canvas = tk.Canvas(self.root, highlightthickness=0)
        self.main_scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = tk.Frame(self.main_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(
                scrollregion=self.main_canvas.bbox("all")
            )
        )

        self.canvas_window = self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)

        self.main_scrollbar.pack(side="right", fill="y")
        self.main_canvas.pack(side="left", fill="both", expand=True)

        # Allow the internal frame to expand horizontally with the window
        self.main_canvas.bind(
            "<Configure>", 
            lambda e: self.main_canvas.itemconfig(self.canvas_window, width=e.width)
        )

        # Enable Mac Trackpad / Mouse scrolling for the whole page
        def _on_mousewheel(event):
            self.main_canvas.yview_scroll(int(-1*(event.delta)), "units")
        self.root.bind_all("<MouseWheel>", _on_mousewheel)
        # ==========================================

        # --- Top Frame: Controls ---
        # Notice we are now attaching everything to self.scrollable_frame instead of self.root
        control_frame = tk.Frame(self.scrollable_frame, pady=10, padx=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.btn_browse = tk.Button(control_frame, text="1. Load .bin Files", command=self.load_files)
        self.btn_browse.pack(side=tk.LEFT, padx=5)
        
        tk.Label(control_frame, text="2. Select File:").pack(side=tk.LEFT, padx=5)
        
        self.combo_files = ttk.Combobox(control_frame, state="readonly", width=30)
        self.combo_files.pack(side=tk.LEFT, padx=5)
        
        self.btn_compute = tk.Button(control_frame, text="3. Compute & Plot", command=self.compute_and_plot)
        self.btn_compute.pack(side=tk.LEFT, padx=5)
        
        # --- Middle Frame: Matplotlib Canvas ---
        self.canvas_frame = tk.Frame(self.scrollable_frame)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Increased graph height back to 5.5 since we can scroll the page now
        self.fig, (self.ax_rms, self.ax_peak, self.ax_counts) = plt.subplots(3, 1, figsize=(8, 5.5))
        self.fig.tight_layout(pad=3.0)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # --- Bottom Frame: Interpretation ---
        interp_frame = tk.LabelFrame(self.scrollable_frame, text="Automated Diagnostic Report", padx=10, pady=10)
        interp_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        # ADDED fg="black" to force the text to be visible regardless of Mac Dark Mode
        self.text_interp = scrolledtext.ScrolledText(interp_frame, height=10, wrap=tk.WORD, bg="#f5f5f5", fg="black")
        self.text_interp.pack(fill=tk.BOTH, expand=True)
        self.text_interp.config(state=tk.DISABLED)

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
            messagebox.showinfo("Files Loaded", f"Successfully loaded {len(filepaths)} file(s).")

    def compute_and_plot(self):
        selected_name = self.combo_files.get()
        if not selected_name:
            messagebox.showwarning("Warning", "Please load and select a file first.")
            return
            
        filepath = self.file_dict[selected_name]
        
        try:
            data = np.fromfile(filepath, dtype=np.uint16)
            signal = data.astype(np.float64) / 4096.0 * 3.3
            signal = signal - np.mean(signal)
            
            N = len(signal)
            win = int(round(self.window_time * self.fs))
            step = int(round(win * (1 - self.overlap)))
            
            threshold = 3.0 * np.std(signal)
            
            file_rms = []
            file_peak = []
            file_counts = []
            
            for i in range(0, N - win + 1, step):
                segment = signal[i:i+win]
                val_rms = np.sqrt(np.mean(segment**2))
                val_peak = np.max(np.abs(segment))
                val_counts = np.sum(np.abs(segment) > threshold)
                
                file_rms.append(val_rms)
                file_peak.append(val_peak)
                file_counts.append(val_counts)
                
            file_rms = np.array(file_rms)
            file_peak = np.array(file_peak)
            file_counts = np.array(file_counts)
            time_axis = np.arange(1, len(file_rms) + 1)
            
            self.ax_rms.clear()
            self.ax_rms.plot(time_axis, file_rms, 'b-', linewidth=1.2)
            self.ax_rms.set_ylabel('RMS (V)')
            self.ax_rms.set_title(f'RMS Trend - {selected_name}')
            self.ax_rms.grid(True)
            
            self.ax_peak.clear()
            self.ax_peak.plot(time_axis, file_peak, 'r-', linewidth=1.2)
            self.ax_peak.set_ylabel('Peak (V)')
            self.ax_peak.set_title(f'Peak Amplitude Trend - {selected_name}')
            self.ax_peak.grid(True)
            
            self.ax_counts.clear()
            self.ax_counts.bar(time_axis, file_counts, color='#EDB120', edgecolor='none')
            self.ax_counts.set_ylabel('Counts')
            self.ax_counts.set_xlabel('Time (Window Number)')
            self.ax_counts.set_title(f'AE Counts Trend - {selected_name}')
            self.ax_counts.grid(True)
            
            self.fig.tight_layout(pad=3.0)
            self.canvas.draw()
            
            self.generate_interpretation(selected_name, file_rms, file_peak, file_counts)
            
            # Auto-scroll to the top whenever a new plot is generated
            self.main_canvas.yview_moveto(0)
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while processing the file:\n{str(e)}")

    def generate_interpretation(self, filename, rms, peak, counts):
        time_windows = np.arange(1, len(rms) + 1)
        
        max_rms = np.max(rms)
        max_peak = np.max(peak)
        total_counts = np.sum(counts)
        
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
        
        interp_text = f"--- AUTOMATED DIAGNOSTIC REPORT: {filename} ---\n"
        interp_text += f"📊 OVERALL BEHAVIOR:\n"
        interp_text += f"  • Signal Classification: {signal_type}\n"
        interp_text += f"  • Energy Trend: {trend_status}\n"
        interp_text += f"  • Total AE Counts: {total_counts}\n\n"
        
        interp_text += f"⚠️ EVENT DETECTION:\n"
        if len(significant_events) > 0:
            event_windows = significant_events + 1
            interp_text += f"  • Detected {len(significant_events)} significant high-energy anomalies.\n"
            
            if len(event_windows) <= 10:
                interp_text += f"  • Critical Windows: {', '.join(map(str, event_windows))}\n"
            else:
                interp_text += f"  • Critical Windows: {', '.join(map(str, event_windows[:10]))}... (and {len(event_windows)-10} more)\n"
                
            interp_text += f"  • Max Peak: {max_peak:.4f} V occurred at window {np.argmax(peak) + 1}\n"
        else:
             interp_text += "  • No distinct high-energy spikes detected above normal operating variance.\n"

        self.text_interp.config(state=tk.NORMAL)
        self.text_interp.delete("1.0", tk.END)
        self.text_interp.insert(tk.END, interp_text)
        self.text_interp.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = AEAnalyzerApp(root)
    root.mainloop()