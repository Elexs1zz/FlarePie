import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import matplotlib

matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
import numpy as np
import csv
from datetime import datetime
import time
import os
from Engine import rocket_simulation, nozzle_performance, get_atmospheric_pressure


class FlarePieApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FlarePie 5.5")
        self.root.geometry("1200x700")
        self.root.configure(bg="#0D1B2A")

        self.animation = None
        self.simulation_data = None

        self.create_custom_style()

        self.create_header()

        self.create_main_layout()

        self.create_status_bar()

    def create_header(self):
        header_frame = tk.Frame(self.root, bg="#1B263B")
        header_frame.pack(fill=tk.X, pady=2)

        self.timestamp_label = tk.Label(
            header_frame,
            text="Current Date and Time (UTC - YYYY-MM-DD HH:MM:SS formatted): " + datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'),
            fg="#E0E1DD", bg="#1B263B",
            font=("Helvetica", 8)
        )
        self.timestamp_label.pack(side=tk.LEFT, padx=10)

        user_name = os.environ.get('USER', os.environ.get('USERNAME', 'Elexs1zz'))
        user_label = tk.Label(
            header_frame,
            text="Current User's Login: " + user_name,
            fg="#E0E1DD", bg="#1B263B",
            font=("Helvetica", 8)
        )
        user_label.pack(side=tk.RIGHT, padx=10)

        self.update_timestamp()

    def update_timestamp(self):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.timestamp_label.config(text=f"Current Date and Time (UTC - YYYY-MM-DD HH:MM:SS formatted): {current_time}")
        self.root.after(1000, self.update_timestamp)

    def create_custom_style(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("TFrame", background="#0D1B2A")

        style.configure(
            "TLabel",
            font=("Helvetica", 10),
            foreground="#E0E1DD",
            background="#0D1B2A"
        )

        style.configure(
            "TButton",
            font=("Helvetica", 10, "bold"),
            foreground="#E0E1DD",
            background="#1B263B",
            padding=6
        )
        style.map("TButton", background=[('active', '#415A77')])

        style.configure(
            "TNotebook",
            background="#1B263B",
            tabmargins=[2, 5, 0, 0]
        )
        style.configure(
            "TNotebook.Tab",
            font=("Helvetica", 10),
            foreground="#E0E1DD",
            padding=[10, 2]
        )
        style.map("TNotebook.Tab", background=[("selected", "#415A77"), ("active", "#778DA9")])

    def create_main_layout(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.create_input_panel(main_frame)

        self.create_output_panel(main_frame)

    def create_input_panel(self, parent):
        input_frame = ttk.Frame(parent, width=300)
        input_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        input_frame.pack_propagate(False)

        rocket_frame = ttk.LabelFrame(input_frame, text="Rocket Parameters")
        rocket_frame.pack(fill=tk.X, padx=5, pady=5)

        rocket_fields = [
            ("Fuel Type:", "fuel_type", "RP1"),
            ("Chamber Pressure (Pa):", "cocp", "7000000"),
            ("Combustion Temp (K):", "ct", "3500"),
            ("Initial Altitude (m):", "altitude", "0"),
            ("Total Mass (kg):", "intmass", "10000"),
            ("Propellant Mass (kg):", "propmass", "8000"),
            ("Mass Flow Rate (kg/s):", "mfr", "250"),
            ("Time Step (s):", "dt", "0.1"),
            ("Reference Area (m²):", "reference_area", "1.0")
        ]

        self.rocket_vars = {}

        for i, (label_text, var_name, default) in enumerate(rocket_fields):
            ttk.Label(rocket_frame, text=label_text).grid(row=i, column=0, sticky='w', padx=5, pady=2)
            var = tk.StringVar(value=default)
            entry = ttk.Entry(rocket_frame, textvariable=var, width=15)
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.rocket_vars[var_name] = var

        nozzle_frame = ttk.LabelFrame(input_frame, text="Nozzle Parameters")
        nozzle_frame.pack(fill=tk.X, padx=5, pady=5)

        nozzle_fields = [
            ("Mass Flow (kg/s):", "mfr", "250"),
            ("Exhaust Velocity (m/s):", "ve", "3000"),
            ("Exit Pressure (Pa):", "expa", "101325"),
            ("Ambient Pressure (Pa):", "amp", "101325"),
            ("Exit Area (m²):", "ea", "1.0")
        ]

        self.nozzle_vars = {}

        for i, (label_text, var_name, default) in enumerate(nozzle_fields):
            ttk.Label(nozzle_frame, text=label_text).grid(row=i, column=0, sticky='w', padx=5, pady=2)
            var = tk.StringVar(value=default)
            entry = ttk.Entry(nozzle_frame, textvariable=var, width=15)
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.nozzle_vars[var_name] = var

        options_frame = ttk.LabelFrame(input_frame, text="Options")
        options_frame.pack(fill=tk.X, padx=5, pady=5)

        self.save_var = tk.BooleanVar(value=True)
        save_check = ttk.Checkbutton(
            options_frame,
            text="Save Results to File",
            variable=self.save_var
        )
        save_check.pack(anchor='w', padx=5, pady=2)

        self.animate_var = tk.BooleanVar(value=True)
        animate_check = ttk.Checkbutton(
            options_frame,
            text="Enable Real-time Animation",
            variable=self.animate_var
        )
        animate_check.pack(anchor='w', padx=5, pady=2)

        buttons_frame = ttk.Frame(input_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=10)

        ttk.Button(
            buttons_frame,
            text="Run Rocket Simulation",
            command=self.run_rocket_simulation
        ).pack(fill=tk.X, pady=2)

        ttk.Button(
            buttons_frame,
            text="Run Nozzle Analysis",
            command=self.run_nozzle_analysis
        ).pack(fill=tk.X, pady=2)

        ttk.Button(
            buttons_frame,
            text="Stop Animation",
            command=self.stop_animation
        ).pack(fill=tk.X, pady=2)

    def create_output_panel(self, parent):
        output_frame = ttk.Frame(parent)
        output_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tab_control = ttk.Notebook(output_frame)
        self.tab_control.pack(fill=tk.BOTH, expand=True)

        self.realtime_tab = ttk.Frame(self.tab_control)
        self.charts_tab = ttk.Frame(self.tab_control)
        self.data_tab = ttk.Frame(self.tab_control)

        self.tab_control.add(self.realtime_tab, text="Real-Time View")
        self.tab_control.add(self.charts_tab, text="Static Charts")
        self.tab_control.add(self.data_tab, text="Data & Results")

        self.setup_realtime_view()

        self.setup_static_charts()

        self.setup_data_view()

    def setup_realtime_view(self):
        plt_style = {'figure.facecolor': '#232931',
                     'axes.facecolor': '#232931',
                     'axes.edgecolor': 'white',
                     'axes.labelcolor': 'white',
                     'axes.titlecolor': 'white',
                     'xtick.color': 'white',
                     'ytick.color': 'white',
                     'text.color': 'white',
                     'grid.color': 'gray',
                     'grid.linestyle': '--',
                     'grid.alpha': 0.6}

        matplotlib.rcParams.update(plt_style)

        self.rt_fig = Figure(figsize=(8, 6))

        self.rt_ax1 = self.rt_fig.add_subplot(221)
        self.rt_ax2 = self.rt_fig.add_subplot(222)
        self.rt_ax3 = self.rt_fig.add_subplot(223)
        self.rt_ax4 = self.rt_fig.add_subplot(224)

        self.velocity_line, = self.rt_ax1.plot([], [], 'c-', linewidth=2)
        self.altitude_line, = self.rt_ax2.plot([], [], 'g-', linewidth=2)
        self.fuel_line, = self.rt_ax3.plot([], [], 'y-', linewidth=2)
        self.thrust_line, = self.rt_ax4.plot([], [], 'r-', linewidth=2)

        self.rt_ax1.set_title("Velocity (m/s)")
        self.rt_ax2.set_title("Altitude (m)")
        self.rt_ax3.set_title("Fuel Remaining (kg)")
        self.rt_ax4.set_title("Thrust (N)")

        for ax in [self.rt_ax1, self.rt_ax2, self.rt_ax3, self.rt_ax4]:
            ax.set_xlabel("Time (s)")
            ax.grid(True)

        self.rt_fig.tight_layout()

        self.rt_canvas = FigureCanvasTkAgg(self.rt_fig, master=self.realtime_tab)
        self.rt_canvas.draw()
        self.rt_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        metrics_frame = tk.Frame(self.realtime_tab, bg="#1B263B")
        metrics_frame.pack(fill=tk.X, pady=5)

        self.metrics = {}
        metric_names = ["Time", "Velocity", "Altitude", "Fuel", "Thrust"]
        metric_units = ["s", "m/s", "m", "kg", "N"]

        for i, (name, unit) in enumerate(zip(metric_names, metric_units)):
            lbl = tk.Label(
                metrics_frame,
                text=f"{name}:",
                bg="#1B263B",
                fg="white",
                font=("Helvetica", 10, "bold")
            )
            lbl.grid(row=0, column=i * 2, padx=5, pady=3, sticky='e')

            value = tk.Label(
                metrics_frame,
                text=f"0.0 {unit}",
                bg="#1B263B",
                fg="cyan",
                font=("Helvetica", 10)
            )
            value.grid(row=0, column=i * 2 + 1, padx=5, pady=3, sticky='w')

            self.metrics[name.lower()] = value

    def setup_static_charts(self):
        charts_notebook = ttk.Notebook(self.charts_tab)
        charts_notebook.pack(fill=tk.BOTH, expand=True)

        perf_tab = ttk.Frame(charts_notebook)
        charts_notebook.add(perf_tab, text="Performance")

        traj_tab = ttk.Frame(charts_notebook)
        charts_notebook.add(traj_tab, text="Trajectory")

        self.perf_fig = Figure(figsize=(8, 6))

        self.perf_ax1 = self.perf_fig.add_subplot(221)
        self.perf_ax2 = self.perf_fig.add_subplot(222)
        self.perf_ax3 = self.perf_fig.add_subplot(223)
        self.perf_ax4 = self.perf_fig.add_subplot(224)

        self.perf_ax1.set_title("Thrust vs Time")
        self.perf_ax2.set_title("Specific Impulse")
        self.perf_ax3.set_title("Mass Flow Rate")
        self.perf_ax4.set_title("Fuel Remaining")

        for ax in [self.perf_ax1, self.perf_ax2, self.perf_ax3, self.perf_ax4]:
            ax.set_xlabel("Time (s)")
            ax.grid(True)

        self.perf_fig.tight_layout()

        self.perf_canvas = FigureCanvasTkAgg(self.perf_fig, master=perf_tab)
        self.perf_canvas.draw()
        self.perf_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.traj_fig = Figure(figsize=(8, 6))

        self.traj_ax1 = self.traj_fig.add_subplot(221)
        self.traj_ax2 = self.traj_fig.add_subplot(222)
        self.traj_ax3 = self.traj_fig.add_subplot(223)
        self.traj_ax4 = self.traj_fig.add_subplot(224)

        self.traj_ax1.set_title("Altitude vs Time")
        self.traj_ax2.set_title("Velocity vs Time")
        self.traj_ax3.set_title("Altitude vs Velocity")
        self.traj_ax4.set_title("Thrust/Weight Ratio")

        for ax in [self.traj_ax1, self.traj_ax2, self.traj_ax3, self.traj_ax4]:
            ax.grid(True)

        self.traj_ax1.set_xlabel("Time (s)")
        self.traj_ax2.set_xlabel("Time (s)")
        self.traj_ax3.set_xlabel("Velocity (m/s)")
        self.traj_ax4.set_xlabel("Time (s)")

        self.traj_fig.tight_layout()

        self.traj_canvas = FigureCanvasTkAgg(self.traj_fig, master=traj_tab)
        self.traj_canvas.draw()
        self.traj_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def setup_data_view(self):
        results_frame = ttk.Frame(self.data_tab)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.result_text = scrolledtext.ScrolledText(
            results_frame,
            width=80,
            height=15,
            font=("Consolas", 10),
            bg="#1E1E1E",
            fg="#E0E1DD"
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)

        summary_frame = ttk.Frame(self.data_tab)
        summary_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.summary_fig = Figure(figsize=(8, 3))
        self.summary_ax = self.summary_fig.add_subplot(111)

        self.summary_ax.set_title("Key Performance Metrics")
        self.summary_ax.grid(True, axis='y')

        self.summary_fig.tight_layout()

        self.summary_canvas = FigureCanvasTkAgg(self.summary_fig, master=summary_frame)
        self.summary_canvas.draw()
        self.summary_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        button_frame = ttk.Frame(self.data_tab)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(
            button_frame,
            text="Export Data as CSV",
            command=self.export_data
        ).pack(side=tk.RIGHT)

    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")

        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bd=1, relief=tk.SUNKEN, anchor=tk.W,
            bg="#1B263B", fg="#E0E1DD"
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def run_rocket_simulation(self):
        try:
            fuel_type = self.rocket_vars["fuel_type"].get()
            cocp = float(self.rocket_vars["cocp"].get())
            ct = float(self.rocket_vars["ct"].get())
            altitude = float(self.rocket_vars["altitude"].get())
            intmass = float(self.rocket_vars["intmass"].get())
            propmass = float(self.rocket_vars["propmass"].get())
            mfr = float(self.rocket_vars["mfr"].get())
            dt = float(self.rocket_vars["dt"].get())
            reference_area = float(self.rocket_vars["reference_area"].get())

            if fuel_type not in ["RP1", "LH2", "SRF", "N2O4"]:
                messagebox.showerror("Input Error", "Invalid fuel type")
                return

            self.status_var.set("Running simulation...")

            results = rocket_simulation(
                fuel_type, cocp, ct, altitude, intmass, propmass, mfr, dt
            )

            self.simulation_data = results

            self.update_static_charts(results)

            self.update_data_view(results)

            if self.animate_var.get():
                self.start_animation(results)

            if self.save_var.get():
                self.save_results(results)

            self.status_var.set("Simulation complete")

        except ValueError as e:
            messagebox.showerror("Input Error", f"Please enter valid numeric values: {str(e)}")
            self.status_var.set("Simulation failed")

    def run_nozzle_analysis(self):
        try:
            mfr = float(self.nozzle_vars["mfr"].get())
            ve = float(self.nozzle_vars["ve"].get())
            expa = float(self.nozzle_vars["expa"].get())
            amp = float(self.nozzle_vars["amp"].get())
            ea = float(self.nozzle_vars["ea"].get())

            self.status_var.set("Calculating nozzle performance...")

            results = nozzle_performance(mfr, ve, expa, amp, ea)

            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "=== NOZZLE PERFORMANCE RESULTS ===\n\n")
            self.result_text.insert(tk.END, f"Total Thrust: {results['thrust']:.2f} N\n")
            self.result_text.insert(tk.END, f"Specific Impulse: {results['isp']:.2f} s\n")
            self.result_text.insert(tk.END, f"Pressure Thrust: {results['pressure_thrust']:.2f} N\n")
            self.result_text.insert(tk.END, f"Momentum Thrust: {results['momentum_thrust']:.2f} N\n")

            self.update_nozzle_summary(results)

            if self.save_var.get():
                self.save_nozzle_results(results)

            self.tab_control.select(2)

            self.status_var.set("Nozzle analysis complete")

        except ValueError as e:
            messagebox.showerror("Input Error", f"Please enter valid numeric values: {str(e)}")
            self.status_var.set("Nozzle analysis failed")

    def start_animation(self, results):
        self.stop_animation()

        time_data = results['time']
        velocity_data = results['velocity']
        altitude_data = results['altitude']
        fuel_data = results['fuel_remaining']
        thrust_data = results['thrust']

        max_time = max(time_data) if time_data else 1
        max_velocity = max(velocity_data) if velocity_data else 1
        max_altitude = max(altitude_data) if altitude_data else 1
        max_fuel = max(fuel_data) if fuel_data else 1
        max_thrust = max(thrust_data) if thrust_data else 1

        self.rt_ax1.set_xlim(0, max_time * 1.1)
        self.rt_ax1.set_ylim(0, max_velocity * 1.1)

        self.rt_ax2.set_xlim(0, max_time * 1.1)
        self.rt_ax2.set_ylim(0, max_altitude * 1.1)

        self.rt_ax3.set_xlim(0, max_time * 1.1)
        self.rt_ax3.set_ylim(0, max_fuel * 1.1)

        self.rt_ax4.set_xlim(0, max_time * 1.1)
        self.rt_ax4.set_ylim(0, max_thrust * 1.1)

        def animate(i):
            progress = min(1.0, i / 100)
            end_idx = max(1, int(len(time_data) * progress))

            self.velocity_line.set_data(time_data[:end_idx], velocity_data[:end_idx])
            self.altitude_line.set_data(time_data[:end_idx], altitude_data[:end_idx])
            self.fuel_line.set_data(time_data[:end_idx], fuel_data[:end_idx])
            self.thrust_line.set_data(time_data[:end_idx], thrust_data[:end_idx])

            if end_idx > 0:
                idx = end_idx - 1
                self.metrics["time"].config(text=f"{time_data[idx]:.2f} s")
                self.metrics["velocity"].config(text=f"{velocity_data[idx]:.2f} m/s")
                self.metrics["altitude"].config(text=f"{altitude_data[idx]:.2f} m")
                self.metrics["fuel"].config(text=f"{fuel_data[idx]:.2f} kg")
                self.metrics["thrust"].config(text=f"{thrust_data[idx]:.2f} N")

            return self.velocity_line, self.altitude_line, self.fuel_line, self.thrust_line

        self.animation = FuncAnimation(
            self.rt_fig,
            animate,
            frames=120,
            interval=50,
            blit=True,
            repeat=False
        )

        self.tab_control.select(0)

        self.rt_canvas.draw()

    def stop_animation(self):
        if self.animation is not None:
            try:
                self.animation.event_source.stop()
            except:
                pass
            self.animation = None

    def update_static_charts(self, results):
        time_data = results['time']
        thrust_data = results['thrust']
        isp_data = results['isp_values']
        mass_flow_data = results['mass_flow']
        fuel_data = results['fuel_remaining']
        velocity_data = results['velocity']
        altitude_data = results['altitude']

        self.perf_ax1.clear()
        self.perf_ax2.clear()
        self.perf_ax3.clear()
        self.perf_ax4.clear()

        self.traj_ax1.clear()
        self.traj_ax2.clear()
        self.traj_ax3.clear()
        self.traj_ax4.clear()

        self.perf_ax1.plot(time_data, thrust_data, 'c-', linewidth=2)
        self.perf_ax1.set_title("Thrust vs Time")
        self.perf_ax1.set_xlabel("Time (s)")
        self.perf_ax1.set_ylabel("Thrust (N)")
        self.perf_ax1.grid(True)

        self.perf_ax2.plot(time_data, isp_data, 'r-', linewidth=2)
        self.perf_ax2.set_title("Specific Impulse")
        self.perf_ax2.set_xlabel("Time (s)")
        self.perf_ax2.set_ylabel("Isp (s)")
        self.perf_ax2.grid(True)

        self.perf_ax3.plot(time_data, mass_flow_data, 'g-', linewidth=2)
        self.perf_ax3.set_title("Mass Flow Rate")
        self.perf_ax3.set_xlabel("Time (s)")
        self.perf_ax3.set_ylabel("Mass Flow (kg/s)")
        self.perf_ax3.grid(True)

        self.perf_ax4.plot(time_data, fuel_data, 'y-', linewidth=2)
        self.perf_ax4.set_title("Fuel Remaining")
        self.perf_ax4.set_xlabel("Time (s)")
        self.perf_ax4.set_ylabel("Fuel (kg)")
        self.perf_ax4.grid(True)

        self.perf_ax2.set_yscale('log')

        self.traj_ax1.plot(time_data, altitude_data, 'c-', linewidth=2)
        self.traj_ax1.set_title("Altitude vs Time")
        self.traj_ax1.set_xlabel("Time (s)")
        self.traj_ax1.set_ylabel("Altitude (m)")
        self.traj_ax1.grid(True)

        self.traj_ax2.plot(time_data, velocity_data, 'r-', linewidth=2)
        self.traj_ax2.set_title("Velocity vs Time")
        self.traj_ax2.set_xlabel("Time (s)")
        self.traj_ax2.set_ylabel("Velocity (m/s)")
        self.traj_ax2.grid(True)

        self.traj_ax3.plot(velocity_data, altitude_data, 'g-', linewidth=2)
        self.traj_ax3.set_title("Altitude vs Velocity")
        self.traj_ax3.set_xlabel("Velocity (m/s)")
        self.traj_ax3.set_ylabel("Altitude (m)")
        self.traj_ax3.grid(True)

        tw_ratio = []
        for t, f in zip(thrust_data, fuel_data):
            try:
                mass = float(self.rocket_vars["intmass"].get()) - float(self.rocket_vars["propmass"].get()) + f
                weight = mass * 9.81
                ratio = t / weight if weight > 0 else 0
                tw_ratio.append(ratio)
            except:
                tw_ratio.append(0)

        self.traj_ax4.plot(time_data, tw_ratio, 'y-', linewidth=2)
        self.traj_ax4.set_title("Thrust/Weight Ratio")
        self.traj_ax4.set_xlabel("Time (s)")
        self.traj_ax4.set_ylabel("T/W Ratio")
        self.traj_ax4.grid(True)

        self.perf_fig.tight_layout()
        self.perf_canvas.draw()

        self.traj_fig.tight_layout()
        self.traj_canvas.draw()

    def update_data_view(self, results):
        self.result_text.delete(1.0, tk.END)

        self.result_text.insert(tk.END, "┌─────────────────────────────────────────────┐\n")
        self.result_text.insert(tk.END, "│          ROCKET SIMULATION RESULTS          │\n")
        self.result_text.insert(tk.END, "└─────────────────────────────────────────────┘\n\n")

        self.result_text.insert(tk.END, f"Total Simulation Time: {results['final_time']:.2f} s\n")
        self.result_text.insert(tk.END, f"Initial Thrust: {results['initial_thrust']:.2f} N\n")
        self.result_text.insert(tk.END, f"Delta-V: {results['delta_v']:.2f} m/s\n\n")

        max_velocity = max(results['velocity']) if results['velocity'] else 0
        max_altitude = max(results['altitude']) if results['altitude'] else 0
        avg_isp = sum(results['isp_values']) / len(results['isp_values']) if results['isp_values'] else 0

        self.result_text.insert(tk.END, "─── KEY METRICS ───\n\n")
        self.result_text.insert(tk.END, f"Maximum Velocity: {max_velocity:.2f} m/s\n")
        self.result_text.insert(tk.END, f"Maximum Altitude: {max_altitude:.2f} m\n")
        self.result_text.insert(tk.END, f"Average ISP: {avg_isp:.2f} s\n\n")

        self.result_text.insert(tk.END, "─── DATA SAMPLES ───\n\n")
        self.result_text.insert(tk.END,
                                f"{'Time (s)':<10} {'Thrust (N)':<12} {'Velocity (m/s)':<15} {'Altitude (m)':<12} {'Fuel (kg)':<10} {'ISP (s)':<8}\n")
        self.result_text.insert(tk.END, "─" * 70 + "\n")

        num_points = len(results['time'])
        step = max(1, num_points // 20)

        for i in range(0, num_points, step):
            t = results['time'][i]
            thrust = results['thrust'][i]
            velocity = results['velocity'][i]
            altitude = results['altitude'][i]
            fuel = results['fuel_remaining'][i]
            isp = results['isp_values'][i]

            row = f"{t:<10.2f} {thrust:<12.2f} {velocity:<15.2f} {altitude:<12.2f} {fuel:<10.2f} {isp:<8.2f}\n"
            self.result_text.insert(tk.END, row)

        self.update_summary_chart(results)

    def update_summary_chart(self, results):
        self.summary_ax.clear()

        max_velocity = max(results['velocity']) if results['velocity'] else 0
        max_altitude = max(results['altitude']) if results['altitude'] else 0
        delta_v = results['delta_v']
        burn_time = results['final_time']

        metrics = ['Max Velocity', 'Max Altitude', 'Delta-V', 'Burn Time']
        values = [max_velocity, max_altitude, delta_v, burn_time]
        colors = ['cyan', 'green', 'orange', 'red']

        bars = self.summary_ax.bar(metrics, values, color=colors)

        for bar in bars:
            height = bar.get_height()
            self.summary_ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height + 0.1,
                f'{height:.2f}',
                ha='center',
                va='bottom',
                color='white',
                fontweight='bold'
            )

        self.summary_ax.set_title("Key Performance Metrics")
        self.summary_ax.grid(axis='y', linestyle='--', alpha=0.6)

        self.summary_fig.tight_layout()
        self.summary_canvas.draw()

    def update_nozzle_summary(self, results):
        self.summary_ax.clear()

        metrics = ['Total Thrust', 'Pressure Thrust', 'Momentum Thrust', 'ISP']
        values = [
            results['thrust'],
            results['pressure_thrust'],
            results['momentum_thrust'],
            results['isp']
        ]
        colors = ['cyan', 'green', 'orange', 'red']

        bars = self.summary_ax.bar(metrics, values, color=colors)

        for bar in bars:
            height = bar.get_height()
            self.summary_ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height + 0.1,
                f'{height:.2f}',
                ha='center',
                va='bottom',
                color='white',
                fontweight='bold'
            )

        self.summary_ax.set_title("Nozzle Performance Metrics")
        self.summary_ax.grid(axis='y', linestyle='--', alpha=0.6)

        self.summary_fig.tight_layout()
        self.summary_canvas.draw()

    def save_results(self, results):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rocket_simulation_{timestamp}.csv"

            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                writer.writerow(['Time (s)', 'Thrust (N)', 'Velocity (m/s)', 'Altitude (m)',
                                 'Fuel (kg)', 'ISP (s)', 'Mass Flow (kg/s)'])

                for i in range(len(results['time'])):
                    writer.writerow([
                        results['time'][i],
                        results['thrust'][i],
                        results['velocity'][i],
                        results['altitude'][i],
                        results['fuel_remaining'][i],
                        results['isp_values'][i],
                        results['mass_flow'][i]
                    ])

            messagebox.showinfo("File Saved", f"Results saved to {filename}")

        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save file: {str(e)}")

    def save_nozzle_results(self, results):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nozzle_analysis_{timestamp}.csv"

            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                writer.writerow(['Parameter', 'Value'])
                writer.writerow(['Total Thrust (N)', results['thrust']])
                writer.writerow(['ISP (s)', results['isp']])
                writer.writerow(['Pressure Thrust (N)', results['pressure_thrust']])
                writer.writerow(['Momentum Thrust (N)', results['momentum_thrust']])

            messagebox.showinfo("File Saved", f"Results saved to {filename}")

        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save file: {str(e)}")

    def export_data(self):
        if self.simulation_data:
            self.save_results(self.simulation_data)
        else:
            messagebox.showinfo("No Data", "No simulation data available to export")


def main():
    root = tk.Tk()
    app = FlarePieApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()