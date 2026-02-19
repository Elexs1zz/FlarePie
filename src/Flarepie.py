import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, filedialog, simpledialog
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
from config import config
from project_manager import ProjectManager, SimulationConfig
from advanced_engine import AdvancedRocketEngine, Stage, OrbitalMechanics, ThermalAnalysis
from report_generator import ReportGenerator
from mpl_toolkits.mplot3d import Axes3D  # For 3D plotting
import math
import urllib.request
import sys


class FlarePieApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FlarePie 6.0 - Professional Rocket Simulation")
        self.root.geometry("1400x800")
        self.root.configure(bg=config.get("theme.primary_color", "#0D1B2A"))
        try:
            import sys, os
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, 'logo.ico')
            else:
                icon_path = 'logo.ico'
            self.root.iconbitmap(icon_path)
        except Exception as e:
            print("Icon not set:", e)

        self.project_manager = ProjectManager()
        self.advanced_engine = AdvancedRocketEngine()
        self.report_generator = ReportGenerator()
        self.thermal_analysis = ThermalAnalysis()
        
        self.animation = None
        self.simulation_data = None
        self.current_project = None
        self.current_simulation = None
        self.undo_stack = []
        self.redo_stack = []
        self._tooltip = None

        self.create_custom_style()
        self.create_menu_bar()
        self.create_header()
        self.create_main_layout()
        self.create_status_bar()
        self.create_toolbar()
        
        self.load_default_config()

    def create_menu_bar(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Report", command=self.export_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Preferences", command=self.show_preferences)
        
        sim_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Simulation", menu=sim_menu)
        sim_menu.add_command(label="Run Basic Simulation", command=self.run_rocket_simulation)
        sim_menu.add_command(label="Orbital Analysis", command=self.run_orbital_analysis)
        sim_menu.add_command(label="Thermal Analysis", command=self.run_thermal_analysis)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="3D Trajectory", command=self.show_3d_trajectory)
        view_menu.add_command(label="Performance Dashboard", command=self.show_performance_dashboard)
        view_menu.add_command(label="Mission Timeline", command=self.show_mission_timeline)

        
        self.root.bind('<Control-z>', lambda e: self.undo())
        self.root.bind('<Control-y>', lambda e: self.redo())

    def create_toolbar(self):
        toolbar = tk.Frame(self.root, bg=config.get("theme.secondary_color", "#1B263B"))
        toolbar.pack(fill=tk.X, pady=2)
        
        tk.Button(toolbar, text="Run Simulation", command=self.run_rocket_simulation,
                 bg=config.get("theme.success_color", "#4CAF50"), fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Stop", command=self.stop_animation,
                 bg=config.get("theme.error_color", "#F44336"), fg="white").pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        tk.Button(toolbar, text="Generate Report", command=self.export_report,
                 bg=config.get("theme.accent_color", "#415A77"), fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="3D View", command=self.show_3d_trajectory,
                 bg=config.get("theme.accent_color", "#415A77"), fg="white").pack(side=tk.LEFT, padx=2)

    def load_default_config(self):
        default_values = {
            "fuel_type": config.get("simulation.default_fuel_type", "RP1"),
            "cocp": config.get("simulation.default_chamber_pressure", 7000000),
            "ct": config.get("simulation.default_combustion_temp", 3500),
            "altitude": config.get("simulation.default_initial_altitude", 0),
            "intmass": config.get("simulation.default_total_mass", 10000),
            "propmass": config.get("simulation.default_propellant_mass", 8000),
            "mfr": config.get("simulation.default_mass_flow_rate", 250),
            "dt": config.get("simulation.default_time_step", 0.1),
            "reference_area": config.get("simulation.default_reference_area", 1.0)
        }
        
        for var_name, value in default_values.items():
            if var_name in self.rocket_vars:
                self.rocket_vars[var_name].set(str(value))

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
        from tkinter import font
        input_frame = ttk.Frame(parent, width=360)
        input_frame.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
        input_frame.pack_propagate(False)

        banner = ttk.Label(input_frame, text="FlarePie", font=("Helvetica", 16, "bold"))
        banner.pack(fill=tk.X, pady=(0, 8))

        preset_frame = ttk.Frame(input_frame)
        preset_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(preset_frame, text="Presets:").pack(side=tk.LEFT, padx=(0, 4))
        presets = {
            "Default": {"fuel_type": "RP1", "cocp": 7000000, "ct": 3500, "altitude": 0, "intmass": 10000, "propmass": 8000, "mfr": 250, "dt": 0.1, "reference_area": 1.0},
            "Suborbital Hop": {"fuel_type": "RP1", "cocp": 5000000, "ct": 3200, "altitude": 0, "intmass": 2000, "propmass": 1500, "mfr": 100, "dt": 0.1, "reference_area": 0.8},
            "LEO Launch": {"fuel_type": "LH2", "cocp": 9000000, "ct": 3700, "altitude": 0, "intmass": 20000, "propmass": 16000, "mfr": 400, "dt": 0.1, "reference_area": 1.2},
            "Sounding Rocket": {"fuel_type": "SRF", "cocp": 4000000, "ct": 3000, "altitude": 0, "intmass": 500, "propmass": 400, "mfr": 50, "dt": 0.05, "reference_area": 0.3}
        }
        preset_var = tk.StringVar(value="Default")
        preset_menu = ttk.Combobox(preset_frame, textvariable=preset_var, values=list(presets.keys()), state="readonly", width=18)
        preset_menu.pack(side=tk.LEFT, padx=(0, 4))
        def apply_preset(*args):
            preset = presets.get(preset_var.get(), presets["Default"])
            for k, v in preset.items():
                if k in self.rocket_vars:
                    self.rocket_vars[k].set(str(v))
        preset_var.trace_add('write', apply_preset)

        notebook = ttk.Notebook(input_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        rocket_tab = ttk.Frame(notebook)
        notebook.add(rocket_tab, text="Rocket")
        rocket_fields = [
            ("Fuel Type:", "fuel_type", "RP1", "Type of propellant used (RP1, LH2, SRF, N2O4)"),
            ("Chamber Pressure (Pa):", "cocp", "7000000", "Pressure in combustion chamber"),
            ("Combustion Temp (K):", "ct", "3500", "Combustion temperature in Kelvin"),
            ("Initial Altitude (m):", "altitude", "0", "Launch altitude above sea level"),
            ("Total Mass (kg):", "intmass", "10000", "Total mass at launch"),
            ("Propellant Mass (kg):", "propmass", "8000", "Mass of propellant"),
            ("Mass Flow Rate (kg/s):", "mfr", "250", "Propellant mass flow rate"),
            ("Time Step (s):", "dt", "0.1", "Simulation time step"),
            ("Reference Area (m²):", "reference_area", "1.0", "Reference area for drag calculation")
        ]
        self.rocket_vars = {}
        for i, (label_text, var_name, default, tooltip) in enumerate(rocket_fields):
            lbl = ttk.Label(rocket_tab, text=label_text)
            lbl.grid(row=i, column=0, sticky='w', padx=6, pady=3)
            var = tk.StringVar(value=default)
            entry = ttk.Entry(rocket_tab, textvariable=var, width=16)
            entry.grid(row=i, column=1, padx=6, pady=3)
            self.rocket_vars[var_name] = var
            self._add_tooltip(lbl, tooltip)
            self._add_tooltip(entry, tooltip)

        nozzle_tab = ttk.Frame(notebook)
        notebook.add(nozzle_tab, text="Nozzle/Engine")
        nozzle_fields = [
            ("Mass Flow (kg/s):", "mfr", "250", "Nozzle mass flow rate"),
            ("Exhaust Velocity (m/s):", "ve", "3000", "Exhaust velocity at nozzle exit"),
            ("Exit Pressure (Pa):", "expa", "101325", "Pressure at nozzle exit"),
            ("Ambient Pressure (Pa):", "amp", "101325", "Ambient pressure"),
            ("Exit Area (m²):", "ea", "1.0", "Nozzle exit area")
        ]
        self.nozzle_vars = {}
        for i, (label_text, var_name, default, tooltip) in enumerate(nozzle_fields):
            lbl = ttk.Label(nozzle_tab, text=label_text)
            lbl.grid(row=i, column=0, sticky='w', padx=6, pady=3)
            var = tk.StringVar(value=default)
            entry = ttk.Entry(nozzle_tab, textvariable=var, width=16)
            entry.grid(row=i, column=1, padx=6, pady=3)
            self.nozzle_vars[var_name] = var
            self._add_tooltip(lbl, tooltip)
            self._add_tooltip(entry, tooltip)

        failure_tab = ttk.Frame(notebook)
        notebook.add(failure_tab, text="Failure/Abort")
        self.enable_failure_var = tk.BooleanVar(value=False)
        self.enable_abort_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(failure_tab, text="Enable Engine Failure", variable=self.enable_failure_var).grid(row=0, column=0, sticky='w', padx=6, pady=3)
        ttk.Checkbutton(failure_tab, text="Enable Abort Sequence", variable=self.enable_abort_var).grid(row=1, column=0, sticky='w', padx=6, pady=3)
        ttk.Label(failure_tab, text="Failure Time (s):").grid(row=2, column=0, sticky='w', padx=6, pady=3)
        self.failure_time_var = tk.StringVar(value="10.0")
        ttk.Entry(failure_tab, textvariable=self.failure_time_var, width=12).grid(row=2, column=1, padx=6, pady=3)
        ttk.Label(failure_tab, text="Abort Time (s):").grid(row=3, column=0, sticky='w', padx=6, pady=3)
        self.abort_time_var = tk.StringVar(value="15.0")
        ttk.Entry(failure_tab, textvariable=self.abort_time_var, width=12).grid(row=3, column=1, padx=6, pady=3)
        ttk.Label(failure_tab, text="Parachute Area (m²):").grid(row=4, column=0, sticky='w', padx=6, pady=3)
        self.parachute_area_var = tk.StringVar(value="10.0")
        ttk.Entry(failure_tab, textvariable=self.parachute_area_var, width=12).grid(row=4, column=1, padx=6, pady=3)
        ttk.Label(failure_tab, text="Parachute Drag Coeff.: ").grid(row=5, column=0, sticky='w', padx=6, pady=3)
        self.parachute_cd_var = tk.StringVar(value="1.5")
        ttk.Entry(failure_tab, textvariable=self.parachute_cd_var, width=12).grid(row=5, column=1, padx=6, pady=3)
        self._add_tooltip(failure_tab, "Configure failure and abort scenarios for the simulation.")

        options_tab = ttk.Frame(notebook)
        notebook.add(options_tab, text="Options")
        self.save_var = tk.BooleanVar(value=True)
        save_check = ttk.Checkbutton(
            options_tab,
            text="Save Results to File",
            variable=self.save_var
        )
        save_check.grid(row=0, column=0, sticky='w', padx=6, pady=3)
        self.animate_var = tk.BooleanVar(value=True)
        animate_check = ttk.Checkbutton(
            options_tab,
            text="Enable Real-time Animation",
            variable=self.animate_var
        )
        animate_check.grid(row=1, column=0, sticky='w', padx=6, pady=3)
        ttk.Label(options_tab, text="Wind Speed at Ground (m/s):").grid(row=7, column=0, sticky='w', padx=6, pady=3)
        self.wind_ground_var = tk.StringVar(value="0.0")
        ttk.Entry(options_tab, textvariable=self.wind_ground_var, width=10).grid(row=7, column=1, padx=6, pady=3)
        ttk.Label(options_tab, text="Wind Speed at Altitude (m/s):").grid(row=8, column=0, sticky='w', padx=6, pady=3)
        self.wind_alt_var = tk.StringVar(value="0.0")
        ttk.Entry(options_tab, textvariable=self.wind_alt_var, width=10).grid(row=8, column=1, padx=6, pady=3)
        ttk.Label(options_tab, text="Wind Direction (deg from N):").grid(row=9, column=0, sticky='w', padx=6, pady=3)
        self.wind_dir_var = tk.StringVar(value="0.0")
        ttk.Entry(options_tab, textvariable=self.wind_dir_var, width=10).grid(row=9, column=1, padx=6, pady=3)
        ttk.Button(options_tab, text="Open Engine/Nozzle Designer", command=self.open_nozzle_designer).grid(row=2, column=0, columnspan=2, sticky='ew', padx=6, pady=8)
        ttk.Button(options_tab, text="Reset to Defaults", command=self.load_default_config).grid(row=3, column=0, columnspan=2, sticky='ew', padx=6, pady=8)
        ttk.Button(options_tab, text="Run Rocket Simulation", command=self.run_rocket_simulation, style="Accent.TButton").grid(row=4, column=0, columnspan=2, sticky='ew', padx=6, pady=8)
        ttk.Button(options_tab, text="Run Nozzle Analysis", command=self.run_nozzle_analysis).grid(row=5, column=0, columnspan=2, sticky='ew', padx=6, pady=2)
        ttk.Button(options_tab, text="Stop Animation", command=self.stop_animation).grid(row=6, column=0, columnspan=2, sticky='ew', padx=6, pady=2)
        stability_tab = ttk.Frame(notebook)
        notebook.add(stability_tab, text="Stability Analysis")
        ttk.Label(stability_tab, text="Body Length (m):").grid(row=0, column=0, sticky='w', padx=6, pady=3)
        self.body_length_var = tk.StringVar(value="5.0")
        ttk.Entry(stability_tab, textvariable=self.body_length_var, width=10).grid(row=0, column=1, padx=6, pady=3)
        ttk.Label(stability_tab, text="Body Diameter (m):").grid(row=1, column=0, sticky='w', padx=6, pady=3)
        self.body_diam_var = tk.StringVar(value="0.4")
        ttk.Entry(stability_tab, textvariable=self.body_diam_var, width=10).grid(row=1, column=1, padx=6, pady=3)
        ttk.Label(stability_tab, text="Nose Length (m):").grid(row=2, column=0, sticky='w', padx=6, pady=3)
        self.nose_length_var = tk.StringVar(value="1.0")
        ttk.Entry(stability_tab, textvariable=self.nose_length_var, width=10).grid(row=2, column=1, padx=6, pady=3)
        ttk.Label(stability_tab, text="Fin Root Chord (m):").grid(row=3, column=0, sticky='w', padx=6, pady=3)
        self.fin_root_var = tk.StringVar(value="0.5")
        ttk.Entry(stability_tab, textvariable=self.fin_root_var, width=10).grid(row=3, column=1, padx=6, pady=3)
        ttk.Label(stability_tab, text="Fin Tip Chord (m):").grid(row=4, column=0, sticky='w', padx=6, pady=3)
        self.fin_tip_var = tk.StringVar(value="0.2")
        ttk.Entry(stability_tab, textvariable=self.fin_tip_var, width=10).grid(row=4, column=1, padx=6, pady=3)
        ttk.Label(stability_tab, text="Fin Span (m):").grid(row=5, column=0, sticky='w', padx=6, pady=3)
        self.fin_span_var = tk.StringVar(value="0.3")
        ttk.Entry(stability_tab, textvariable=self.fin_span_var, width=10).grid(row=5, column=1, padx=6, pady=3)
        ttk.Label(stability_tab, text="Number of Fins:").grid(row=6, column=0, sticky='w', padx=6, pady=3)
        self.fin_num_var = tk.StringVar(value="4")
        ttk.Entry(stability_tab, textvariable=self.fin_num_var, width=10).grid(row=6, column=1, padx=6, pady=3)
        ttk.Button(stability_tab, text="Calculate CG/CP", command=self.calculate_cg_cp).grid(row=7, column=0, columnspan=2, pady=8)
        self.cgcp_result_var = tk.StringVar(value="")
        ttk.Label(stability_tab, textvariable=self.cgcp_result_var, font=("Helvetica", 10, "bold")).grid(row=8, column=0, columnspan=2, pady=4)
        self.cgcp_canvas = None
        def draw_schematic():
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            if self.cgcp_canvas:
                self.cgcp_canvas.get_tk_widget().destroy()
            fig, ax = plt.subplots(figsize=(3, 1.2))
            L = float(self.body_length_var.get())
            D = float(self.body_diam_var.get())
            cg = getattr(self, 'last_cg', L/2)
            cp = getattr(self, 'last_cp', L*0.7)
            ax.plot([0, L], [0, 0], color='black', lw=8)
            ax.plot([0, L], [D/2, D/2], color='gray', lw=1)
            ax.plot([0, L], [-D/2, -D/2], color='gray', lw=1)
            ax.scatter([cg], [0], color='blue', s=80, label='CG')
            ax.scatter([cp], [0], color='red', s=80, label='CP')
            ax.legend(loc='upper right')
            ax.set_xlim(-0.1*L, 1.1*L)
            ax.set_ylim(-D, D)
            ax.axis('off')
            fig.tight_layout()
            self.cgcp_canvas = FigureCanvasTkAgg(fig, master=stability_tab)
            self.cgcp_canvas.draw()
            self.cgcp_canvas.get_tk_widget().grid(row=9, column=0, columnspan=2, pady=4)
        self.draw_cgcp_schematic = draw_schematic

    def _add_tooltip(self, widget, text):
        def on_enter(event):
            self._tooltip = tk.Toplevel(widget)
            self._tooltip.wm_overrideredirect(True)
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + 20
            self._tooltip.wm_geometry(f"+{x}+{y}")
            label = tk.Label(self._tooltip, text=text, background="#333", foreground="#fff", relief="solid", borderwidth=1, font=("Helvetica", 9))
            label.pack(ipadx=4, ipady=2)
        def on_leave(event):
            if hasattr(self, '_tooltip') and self._tooltip:
                self._tooltip.destroy()
                self._tooltip = None
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

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

        self.velocity_line, = self.rt_ax1.plot([], [], 'c-', linewidth=2, label='Velocity')
        self.altitude_line, = self.rt_ax2.plot([], [], 'g-', linewidth=2, label='Altitude')
        self.fuel_line, = self.rt_ax3.plot([], [], 'y-', linewidth=2, label='Fuel Remaining')
        self.thrust_line, = self.rt_ax4.plot([], [], 'r-', linewidth=2, label='Thrust')

        self.rt_ax1.set_title("Velocity (m/s)", fontsize=12, fontweight='bold')
        self.rt_ax2.set_title("Altitude (m)", fontsize=12, fontweight='bold')
        self.rt_ax3.set_title("Fuel Remaining (kg)", fontsize=12, fontweight='bold')
        self.rt_ax4.set_title("Thrust (N)", fontsize=12, fontweight='bold')

        for ax in [self.rt_ax1, self.rt_ax2, self.rt_ax3, self.rt_ax4]:
            ax.set_xlabel("Time (s)", fontsize=10)
            ax.set_ylabel(ax.get_title().split()[0], fontsize=10)
            ax.grid(True, which='both', linestyle='--', alpha=0.6)
            ax.minorticks_on()
            ax.tick_params(axis='both', which='major', labelsize=9)
            ax.legend(loc='upper right', fontsize=8, frameon=False)

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
            mfr = float(self.nozzle_vars["mfr"].get()) if "mfr" in self.nozzle_vars else float(self.rocket_vars["mfr"].get())
            dt = float(self.rocket_vars["dt"].get())
            reference_area = float(self.rocket_vars["reference_area"].get())

            enable_failure = self.enable_failure_var.get()
            enable_abort = self.enable_abort_var.get()
            failure_time = float(self.failure_time_var.get()) if enable_failure else None
            abort_time = float(self.abort_time_var.get()) if enable_abort else None
            parachute_area = float(self.parachute_area_var.get()) if enable_abort else 0.0
            parachute_cd = float(self.parachute_cd_var.get()) if enable_abort else 0.0

            if fuel_type not in ["RP1", "LH2", "SRF", "N2O4"]:
                messagebox.showerror("Input Error", "Invalid fuel type")
                return

            self.status_var.set("Running simulation...")

            from Engine import get_atmospheric_pressure, calculate_drag
            k, R = {"RP1": (1.2, 287.0), "LH2": (1.4, 4124.0), "SRF": (1.2, 191.0), "N2O4": (1.26, 320.0)}[fuel_type]
            current_mass = intmass
            time_elapsed = 0.0
            velocity = 0.0
            current_altitude = altitude
            delta_v = 0.0
            energy_values = []
            drag_values = []
            acceleration_values = []
            time_steps = []
            thrust_values = []
            fuel_remaining = []
            mass_flow_values = []
            velocity_values = []
            altitude_values = []
            isp_values = []
            failure_event_idx = None
            abort_event_idx = None
            abort_triggered = False
            max_time = 10000.0
            max_iterations = 200000
            iterations = 0
            while (propmass > 0 or (abort_triggered and current_altitude > 0.5 and abs(velocity) > 0.5)) and time_elapsed < max_time and iterations < max_iterations:
                ap = get_atmospheric_pressure(current_altitude)
                pressure_ratio = (ap / cocp) ** ((k - 1) / k) if cocp > 0 else 0.0
                ve = (2.0 * k) / (k - 1.0) * R * ct * (1.0 - pressure_ratio)
                ve = max(0.0, ve) ** 0.5
                thrust = mfr * ve
                if enable_failure and failure_time is not None and time_elapsed >= failure_time:
                    if failure_event_idx is None:
                        failure_event_idx = len(time_steps)
                    thrust = 0.0
                    mfr = 0.0
                if enable_abort and abort_time is not None and time_elapsed >= abort_time:
                    if abort_event_idx is None:
                        abort_event_idx = len(time_steps)
                        abort_triggered = True
                    thrust = 0.0
                    mfr = 0.0
                mass_used = min(mfr * dt, propmass)
                propmass -= mass_used
                current_mass -= mass_used
                if abort_triggered:
                    p0 = 1.225
                    h0 = 8500
                    density = p0 * math.exp(-current_altitude / h0)
                    drag = 0.5 * density * velocity ** 2 * parachute_area * parachute_cd * (-1 if velocity > 0 else 1)
                else:
                    drag = calculate_drag(velocity, current_altitude, reference_area)
                acceleration = (thrust / current_mass) - 9.81 - (drag / current_mass)
                velocity_mid = velocity + 0.5 * acceleration * dt
                altitude_mid = current_altitude + 0.5 * velocity * dt
                if abort_triggered:
                    density_mid = p0 * math.exp(-altitude_mid / h0)
                    drag_mid = 0.5 * density_mid * velocity_mid ** 2 * parachute_area * parachute_cd * (-1 if velocity_mid > 0 else 1)
                else:
                    drag_mid = calculate_drag(velocity_mid, altitude_mid, reference_area)
                acceleration_mid = (thrust / current_mass) - 9.81 - (drag_mid / current_mass)
                velocity_new = velocity + acceleration_mid * dt
                altitude_new = current_altitude + velocity_mid * dt
                delta_v_step = max(0.0, velocity_new - velocity)
                delta_v += delta_v_step
                kinetic_energy = 0.5 * current_mass * velocity ** 2
                potential_energy = current_mass * 9.81 * current_altitude
                energy_values.append(kinetic_energy + potential_energy)
                isp = thrust / (mfr * 9.81) if mfr > 0 else 0.0
                time_steps.append(time_elapsed)
                thrust_values.append(thrust)
                fuel_remaining.append(propmass)
                mass_flow_values.append(mfr)
                velocity_values.append(velocity)
                altitude_values.append(current_altitude)
                isp_values.append(isp)
                drag_values.append(drag)
                acceleration_values.append(acceleration)
                velocity = velocity_new
                current_altitude = altitude_new
                time_elapsed += dt
                iterations += 1
                # Ensure after abort, rocket lands
                if abort_triggered and current_altitude <= 0:
                    break
                if thrust == 0.0 and propmass <= 0 and not abort_triggered:
                    break
            results = {
                "time": time_steps,
                "thrust": thrust_values,
                "fuel_remaining": fuel_remaining,
                "mass_flow": mass_flow_values,
                "velocity": velocity_values,
                "altitude": altitude_values,
                "isp_values": isp_values,
                "energy": energy_values,
                "drag": drag_values,
                "acceleration": acceleration_values,
                "final_time": time_elapsed,
                "initial_thrust": thrust_values[0] if thrust_values else 0,
                "delta_v": delta_v,
                "simulation_complete": True,
                "failure_event_idx": failure_event_idx,
                "abort_event_idx": abort_event_idx
            }
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
        failure_idx = results.get('failure_event_idx')
        abort_idx = results.get('abort_event_idx')

        self.perf_ax1.clear()
        self.perf_ax2.clear()
        self.perf_ax3.clear()
        self.perf_ax4.clear()

        self.traj_ax1.clear()
        self.traj_ax2.clear()
        self.traj_ax3.clear()
        self.traj_ax4.clear()

        self.perf_ax1.plot(time_data, thrust_data, 'c-', linewidth=2, label='Thrust')
        self.perf_ax1.set_title("Thrust vs Time", fontsize=12, fontweight='bold')
        self.perf_ax1.set_xlabel("Time (s)", fontsize=10)
        self.perf_ax1.set_ylabel("Thrust (N)", fontsize=10)
        self.perf_ax1.grid(True, which='both', linestyle='--', alpha=0.6)
        self.perf_ax1.minorticks_on()
        self.perf_ax1.legend(loc='upper right', fontsize=8, frameon=False)
        if failure_idx is not None:
            self.perf_ax1.axvline(time_data[failure_idx], color='red', linestyle=':', linewidth=2, label='Engine Failure')
        if abort_idx is not None:
            self.perf_ax1.axvline(time_data[abort_idx], color='orange', linestyle=':', linewidth=2, label='Abort')
        max_thrust = max(thrust_data) if thrust_data else 0
        self.perf_ax1.annotate(f"Max: {max_thrust:.0f}", xy=(time_data[thrust_data.index(max_thrust)], max_thrust),
                               xytext=(10, 10), textcoords='offset points', color='cyan', fontsize=8,
                               arrowprops=dict(arrowstyle='->', color='cyan'))

        self.perf_ax2.plot(time_data, isp_data, 'r-', linewidth=2, label='Isp')
        self.perf_ax2.set_title("Specific Impulse", fontsize=12, fontweight='bold')
        self.perf_ax2.set_xlabel("Time (s)", fontsize=10)
        self.perf_ax2.set_ylabel("Isp (s)", fontsize=10)
        self.perf_ax2.grid(True, which='both', linestyle='--', alpha=0.6)
        self.perf_ax2.set_yscale('log')
        self.perf_ax2.minorticks_on()
        self.perf_ax2.legend(loc='upper right', fontsize=8, frameon=False)

        self.perf_ax3.plot(time_data, mass_flow_data, 'g-', linewidth=2, label='Mass Flow')
        self.perf_ax3.set_title("Mass Flow Rate", fontsize=12, fontweight='bold')
        self.perf_ax3.set_xlabel("Time (s)", fontsize=10)
        self.perf_ax3.set_ylabel("Mass Flow (kg/s)", fontsize=10)
        self.perf_ax3.grid(True, which='both', linestyle='--', alpha=0.6)
        self.perf_ax3.minorticks_on()
        self.perf_ax3.legend(loc='upper right', fontsize=8, frameon=False)

        self.perf_ax4.plot(time_data, fuel_data, 'y-', linewidth=2, label='Fuel Remaining')
        self.perf_ax4.set_title("Fuel Remaining", fontsize=12, fontweight='bold')
        self.perf_ax4.set_xlabel("Time (s)", fontsize=10)
        self.perf_ax4.set_ylabel("Fuel (kg)", fontsize=10)
        self.perf_ax4.grid(True, which='both', linestyle='--', alpha=0.6)
        self.perf_ax4.minorticks_on()
        self.perf_ax4.legend(loc='upper right', fontsize=8, frameon=False)
        min_fuel = min(fuel_data) if fuel_data else 0
        self.perf_ax4.annotate(f"Min: {min_fuel:.0f}", xy=(time_data[fuel_data.index(min_fuel)], min_fuel),
                               xytext=(10, -15), textcoords='offset points', color='yellow', fontsize=8,
                               arrowprops=dict(arrowstyle='->', color='yellow'))

        self.traj_ax1.plot(time_data, altitude_data, 'c-', linewidth=2, label='Altitude')
        self.traj_ax1.set_title("Altitude vs Time", fontsize=12, fontweight='bold')
        self.traj_ax1.set_xlabel("Time (s)", fontsize=10)
        self.traj_ax1.set_ylabel("Altitude (m)", fontsize=10)
        self.traj_ax1.grid(True, which='both', linestyle='--', alpha=0.6)
        self.traj_ax1.minorticks_on()
        self.traj_ax1.legend(loc='upper right', fontsize=8, frameon=False)
        max_alt = max(altitude_data) if altitude_data else 0
        self.traj_ax1.annotate(f"Max: {max_alt:.0f}", xy=(time_data[altitude_data.index(max_alt)], max_alt),
                               xytext=(10, 10), textcoords='offset points', color='cyan', fontsize=8,
                               arrowprops=dict(arrowstyle='->', color='cyan'))
        if failure_idx is not None:
            self.traj_ax1.axvline(time_data[failure_idx], color='red', linestyle=':', linewidth=2, label='Engine Failure')
        if abort_idx is not None:
            self.traj_ax1.axvline(time_data[abort_idx], color='orange', linestyle=':', linewidth=2, label='Abort')

        self.traj_ax2.plot(time_data, velocity_data, 'r-', linewidth=2, label='Velocity')
        self.traj_ax2.set_title("Velocity vs Time", fontsize=12, fontweight='bold')
        self.traj_ax2.set_xlabel("Time (s)", fontsize=10)
        self.traj_ax2.set_ylabel("Velocity (m/s)", fontsize=10)
        self.traj_ax2.grid(True, which='both', linestyle='--', alpha=0.6)
        self.traj_ax2.minorticks_on()
        self.traj_ax2.legend(loc='upper right', fontsize=8, frameon=False)
        max_vel = max(velocity_data) if velocity_data else 0
        self.traj_ax2.annotate(f"Max: {max_vel:.0f}", xy=(time_data[velocity_data.index(max_vel)], max_vel),
                               xytext=(10, 10), textcoords='offset points', color='red', fontsize=8,
                               arrowprops=dict(arrowstyle='->', color='red'))

        self.traj_ax3.plot(velocity_data, altitude_data, 'g-', linewidth=2, label='Alt vs Vel')
        self.traj_ax3.set_title("Altitude vs Velocity", fontsize=12, fontweight='bold')
        self.traj_ax3.set_xlabel("Velocity (m/s)", fontsize=10)
        self.traj_ax3.set_ylabel("Altitude (m)", fontsize=10)
        self.traj_ax3.grid(True, which='both', linestyle='--', alpha=0.6)
        self.traj_ax3.minorticks_on()
        self.traj_ax3.legend(loc='upper right', fontsize=8, frameon=False)

        tw_ratio = []
        for t, f in zip(thrust_data, fuel_data):
            try:
                mass = float(self.rocket_vars["intmass"].get()) - float(self.rocket_vars["propmass"].get()) + f
                weight = mass * 9.81
                ratio = t / weight if weight > 0 else 0
                tw_ratio.append(ratio)
            except:
                tw_ratio.append(0)

        self.traj_ax4.plot(time_data, tw_ratio, 'y-', linewidth=2, label='T/W Ratio')
        self.traj_ax4.set_title("Thrust/Weight Ratio", fontsize=12, fontweight='bold')
        self.traj_ax4.set_xlabel("Time (s)", fontsize=10)
        self.traj_ax4.set_ylabel("T/W Ratio", fontsize=10)
        self.traj_ax4.grid(True, which='both', linestyle='--', alpha=0.6)
        self.traj_ax4.minorticks_on()
        self.traj_ax4.legend(loc='upper right', fontsize=8, frameon=False)

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


    def export_report(self):
        if not self.simulation_data:
            messagebox.showwarning("Warning", "No simulation data to export")
            return
        
        try:
            config_data = {
                "fuel_type": self.rocket_vars["fuel_type"].get(),
                "cocp": float(self.rocket_vars["cocp"].get()),
                "ct": float(self.rocket_vars["ct"].get()),
                "altitude": float(self.rocket_vars["altitude"].get()),
                "intmass": float(self.rocket_vars["intmass"].get()),
                "propmass": float(self.rocket_vars["propmass"].get()),
                "mfr": float(self.rocket_vars["mfr"].get()),
                "dt": float(self.rocket_vars["dt"].get()),
                "reference_area": float(self.rocket_vars["reference_area"].get())
            }
            
            report_path = self.report_generator.generate_simulation_report(
                self.simulation_data, config_data
            )
            messagebox.showinfo("Success", f"Report generated: {report_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")

    def undo(self):
        if self.undo_stack:
            # Placeholder for undo functionality
            messagebox.showinfo("Info", "Undo functionality not implemented yet")

    def redo(self):
        if self.redo_stack:
            # Placeholder for redo functionality
            messagebox.showinfo("Info", "Redo functionality not implemented yet")

    def show_preferences(self):
        messagebox.showinfo("Info", "Preferences dialog not implemented yet")

    def run_multi_stage_simulation(self):
        try:
            stage1 = Stage(
                name="First Stage",
                fuel_type=self.rocket_vars["fuel_type"].get(),
                chamber_pressure=float(self.rocket_vars["cocp"].get()),
                combustion_temp=float(self.rocket_vars["ct"].get()),
                total_mass=float(self.rocket_vars["intmass"].get()) * 0.8,
                propellant_mass=float(self.rocket_vars["propmass"].get()) * 0.8,
                mass_flow_rate=float(self.rocket_vars["mfr"].get()),
                reference_area=float(self.rocket_vars["reference_area"].get()),
                separation_altitude=10000
            )
            
            stage2 = Stage(
                name="Second Stage",
                fuel_type=self.rocket_vars["fuel_type"].get(),
                chamber_pressure=float(self.rocket_vars["cocp"].get()),
                combustion_temp=float(self.rocket_vars["ct"].get()),
                total_mass=float(self.rocket_vars["intmass"].get()) * 0.2,
                propellant_mass=float(self.rocket_vars["propmass"].get()) * 0.2,
                mass_flow_rate=float(self.rocket_vars["mfr"].get()) * 0.5,
                reference_area=float(self.rocket_vars["reference_area"].get()) * 0.5
            )
            
            self.advanced_engine.stages = [stage1, stage2]
            results = self.advanced_engine.multi_stage_simulation()
            
            if "error" not in results:
                self.simulation_data = results
                self.update_static_charts(results)
                self.update_data_view(results)
                messagebox.showinfo("Success", "Multi-stage simulation completed")
            else:
                messagebox.showerror("Error", results["error"])
        except Exception as e:
            messagebox.showerror("Error", f"Multi-stage simulation failed: {str(e)}")

    def run_orbital_analysis(self):
        if not self.simulation_data:
            messagebox.showwarning("Warning", "Run a simulation first")
            return
        
        try:
            max_altitude_idx = self.simulation_data["altitude"].index(max(self.simulation_data["altitude"]))
            altitude = float(self.simulation_data["altitude"][max_altitude_idx])
            velocity = float(self.simulation_data["velocity"][max_altitude_idx])
            
            escape_velocity = OrbitalMechanics.calculate_escape_velocity(altitude)
            circular_velocity = OrbitalMechanics.calculate_circular_velocity(altitude)
            
            analysis_text = f"""
            Orbital Analysis Results:
            
            Maximum Altitude: {altitude:.2f} m
            Velocity at Max Altitude: {velocity:.2f} m/s
            Escape Velocity at Altitude: {escape_velocity:.2f} m/s
            Circular Orbital Velocity: {circular_velocity:.2f} m/s
            
            Analysis:
            • {'Achieved orbit' if velocity >= circular_velocity else 'Suborbital flight'}
            • {'Escape velocity reached' if velocity >= escape_velocity else 'Below escape velocity'}
            • Orbital period: {2 * 3.14159 * (6371000 + altitude) / circular_velocity:.0f} seconds
            """
            
            messagebox.showinfo("Orbital Analysis", analysis_text)
        except Exception as e:
            messagebox.showerror("Error", f"Orbital analysis failed: {str(e)}")

    def run_thermal_analysis(self):
        if not self.simulation_data:
            messagebox.showwarning("Warning", "Run a simulation first")
            return
        
        try:
            max_velocity_idx = self.simulation_data["velocity"].index(max(self.simulation_data["velocity"]))
            velocity = float(self.simulation_data["velocity"][max_velocity_idx])
            altitude = float(self.simulation_data["altitude"][max_velocity_idx])
            
            thermal_results = self.thermal_analysis.calculate_heat_transfer(
                velocity, altitude, "aluminum", 0.01
            )
            
            analysis_text = f"""
            Thermal Analysis Results:
            
            Maximum Velocity: {velocity:.2f} m/s
            Altitude at Max Velocity: {altitude:.2f} m
            
            Heat Transfer:
            • Convective Heat: {thermal_results['convective_heat']:.2f} W/m²
            • Radiative Heat: {thermal_results['radiative_heat']:.2f} W/m²
            • Total Heat Flux: {thermal_results['total_heat']:.2f} W/m²
            • Temperature Rise: {thermal_results['temperature_rise']:.2f} K
            
            Material: {thermal_results['material']}
            """
            
            messagebox.showinfo("Thermal Analysis", analysis_text)
        except Exception as e:
            messagebox.showerror("Error", f"Thermal analysis failed: {str(e)}")

    def show_3d_trajectory(self):
        if not self.simulation_data:
            messagebox.showwarning("Warning", "No simulation data available")
            return
        win = tk.Toplevel(self.root)
        win.title("3D Trajectory Visualization")
        try:
            win.iconbitmap(self.get_icon_path())
        except Exception:
            pass
        fig = Figure(figsize=(8, 6))
        ax = fig.add_subplot(111, projection='3d')
        time_data = self.simulation_data['time']
        altitude_data = self.simulation_data['altitude']
        velocity_data = self.simulation_data['velocity']
        line, = ax.plot([], [], [], color='cyan', linewidth=2)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Velocity (m/s)')
        ax.set_zlabel('Altitude (m)')  # type: ignore[attr-defined]
        ax.set_title('3D Trajectory (Time, Velocity, Altitude)')
        ax.grid(True)
        ax.set_xlim(float(min(time_data)), float(max(time_data)))
        ax.set_ylim(float(min(velocity_data)), float(max(velocity_data)))
        ax.set_zlim(float(min(altitude_data)), float(max(altitude_data)))  # type: ignore[attr-defined]
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        def animate(i):
            idx = max(1, int(len(time_data) * i / 100))
            line.set_data(time_data[:idx], velocity_data[:idx])
            line.set_3d_properties(altitude_data[:idx])  # type: ignore[attr-defined]
            return line,
        anim = FuncAnimation(fig, animate, frames=100, interval=50, blit=True, repeat=False)
        canvas.draw()

    def show_performance_dashboard(self):
        if not self.simulation_data:
            messagebox.showwarning("Warning", "No simulation data available")
            return
        
        dash_win = tk.Toplevel(self.root)
        dash_win.title("Performance Dashboard")
        try:
            dash_win.iconbitmap(self.get_icon_path())
        except Exception:
            pass
        tk.Label(dash_win, text="Performance dashboard not implemented yet").pack(padx=20, pady=20)

    def show_mission_timeline(self):
        """Show mission timeline"""
        if not self.simulation_data:
            messagebox.showwarning("Warning", "No simulation data available")
            return
        
        timeline_win = tk.Toplevel(self.root)
        timeline_win.title("Mission Timeline")
        try:
            timeline_win.iconbitmap(self.get_icon_path())
        except Exception:
            pass
        tk.Label(timeline_win, text="Mission timeline not implemented yet").pack(padx=20, pady=20)

    def show_earth_trajectory(self):
        import numpy as np
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from mpl_toolkits.mplot3d import Axes3D
        from matplotlib.animation import FuncAnimation
        import os
        import urllib.request
        if not self.simulation_data:
            messagebox.showwarning("Warning", "No simulation data available")
            return
        R_earth = 6371000  # meters
        lat0 = np.radians(28.3922)
        lon0 = np.radians(-80.6077)
        alt = np.array(self.simulation_data['altitude'])
        time = np.array(self.simulation_data['time'])
        lat = np.full_like(alt, lat0)
        lon = np.full_like(alt, lon0)
        x = (R_earth + alt) * np.cos(lat) * np.cos(lon)
        y = (R_earth + alt) * np.cos(lat) * np.sin(lon)
        z = (R_earth + alt) * np.sin(lat)
        xg = R_earth * np.cos(lat) * np.cos(lon)
        yg = R_earth * np.cos(lat) * np.sin(lon)
        zg = R_earth * np.sin(lat)
        win = tk.Toplevel(self.root)
        win.title("3D Earth Trajectory Animation")
        fig = plt.figure(figsize=(8, 7))
        ax = fig.add_subplot(111, projection='3d')
        texture_path = "earth_texture.png"
        if not os.path.exists(texture_path):
            url = "https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57730/land_ocean_ice_2048.png"
            urllib.request.urlretrieve(url, texture_path)
        img = plt.imread(texture_path)
        # High-res sphere
        n = 200
        u = np.linspace(0, 2 * np.pi, n)
        v = np.linspace(0, np.pi, n//2)
        u, v = np.meshgrid(u, v)
        xe = R_earth * np.cos(u) * np.sin(v)
        ye = R_earth * np.sin(u) * np.sin(v)
        ze = R_earth * np.cos(v)
        # Map texture
        lon_img = (u / (2 * np.pi) * img.shape[1]).astype(int) % img.shape[1]
        lat_img = (v / np.pi * img.shape[0]).astype(int) % img.shape[0]
        facecolors = img[lat_img, lon_img] / 255.0
        ax.plot_surface(xe, ye, ze, rstride=2, cstride=2, facecolors=facecolors, linewidth=0, antialiased=False, shade=True)  # type: ignore[attr-defined]
        eq_u = np.linspace(0, 2 * np.pi, 400)
        ax.plot(R_earth * np.cos(eq_u), R_earth * np.sin(eq_u), 0, color='w', linewidth=1, alpha=0.7)

        ax.plot([0, 0], [0, 0], [-R_earth, R_earth], color='w', linewidth=1, alpha=0.7)
        ax.plot(xg, yg, zg, color='yellow', linewidth=2, label='Ground Track')
        traj_line, = ax.plot([], [], [], color='red', linewidth=2, label='Trajectory')
        max_alt = max(alt) if len(alt) else 1000
        ax.set_xlim(-R_earth*1.1, R_earth*1.1)
        ax.set_ylim(-R_earth*1.1, R_earth*1.1)
        ax.set_zlim(-R_earth*0.2, R_earth*1.2+max_alt)  # type: ignore[attr-defined]
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_zlabel('Z (m)')  # type: ignore[attr-defined]
        ax.set_title('3D Trajectory over Earth', fontsize=14, fontweight='bold')
        ax.legend(loc='upper left')
        ax.grid(False)
        def animate(i):
            idx = max(1, int(len(x) * i / 100))
            traj_line.set_data(x[:idx], y[:idx])
            traj_line.set_3d_properties(z[:idx])  # type: ignore[attr-defined]
            return traj_line,
        anim = FuncAnimation(fig, animate, frames=100, interval=50, blit=True, repeat=False)
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def show_manual(self):
        manual_text = """
        FlarePie 6.0 - Professional Rocket Simulation
        
        Features:
        • Basic rocket simulation
        • Multi-stage rocket simulation
        • Orbital mechanics analysis
        • Thermal analysis
        • Project management
        • Professional reporting
        
        Usage:
        1. Set rocket parameters
        2. Run simulation
        3. View results and charts
        4. Generate reports
        """
        manual_win = tk.Toplevel(self.root)
        manual_win.title("User Manual")
        try:
            manual_win.iconbitmap(self.get_icon_path())
        except Exception:
            pass
        tk.Label(manual_win, text=manual_text, justify='left', font=("Helvetica", 10)).pack(padx=20, pady=20)

    def show_about(self):
        about_text = """
        FlarePie 6.0 - Professional Rocket Simulation
        
        Version: 6.0
        Build: 2024
        
        Features:
        • Advanced rocket propulsion simulation
        • Multi-stage rocket support
        • Orbital mechanics calculations
        • Thermal analysis
        • Professional reporting system
        • Project management
        
        Developed for professional rocket engineering applications.
        """
        about_win = tk.Toplevel(self.root)
        about_win.title("About FlarePie")
        try:
            about_win.iconbitmap(self.get_icon_path())
        except Exception:
            pass
        tk.Label(about_win, text=about_text, justify='left', font=("Helvetica", 10)).pack(padx=20, pady=20)

    def open_nozzle_designer(self):
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import json
        win = tk.Toplevel(self.root)
        win.title("Advanced Engine/Nozzle Designer")
        try:
            win.iconbitmap(self.get_icon_path())
        except Exception:
            pass
        materials = {
            "Steel": {"density": 7850, "max_temp": 1700},
            "Aluminum": {"density": 2700, "max_temp": 900},
            "Titanium": {"density": 4500, "max_temp": 2000},
            "Inconel": {"density": 8470, "max_temp": 2200},
            "Copper": {"density": 8960, "max_temp": 1085}
        }
        param_frame = ttk.Frame(win)
        param_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        ttk.Label(param_frame, text="Chamber Radius (m):").grid(row=0, column=0, sticky='w')
        chamber_r_var = tk.StringVar(value="0.25")
        ttk.Entry(param_frame, textvariable=chamber_r_var, width=10).grid(row=0, column=1)
        ttk.Label(param_frame, text="Throat Radius (m):").grid(row=1, column=0, sticky='w')
        throat_r_var = tk.StringVar(value="0.1")
        ttk.Entry(param_frame, textvariable=throat_r_var, width=10).grid(row=1, column=1)
        ttk.Label(param_frame, text="Exit Radius (m):").grid(row=2, column=0, sticky='w')
        exit_r_var = tk.StringVar(value="0.3")
        ttk.Entry(param_frame, textvariable=exit_r_var, width=10).grid(row=2, column=1)
        ttk.Label(param_frame, text="Nozzle Length (m):").grid(row=3, column=0, sticky='w')
        length_var = tk.StringVar(value="1.0")
        ttk.Entry(param_frame, textvariable=length_var, width=10).grid(row=3, column=1)
        ttk.Label(param_frame, text="Nozzle Angle (deg):").grid(row=4, column=0, sticky='w')
        angle_var = tk.StringVar(value="15.0")
        ttk.Entry(param_frame, textvariable=angle_var, width=10).grid(row=4, column=1)
        ttk.Label(param_frame, text="Wall Thickness (m):").grid(row=5, column=0, sticky='w')
        wall_var = tk.StringVar(value="0.01")
        ttk.Entry(param_frame, textvariable=wall_var, width=10).grid(row=5, column=1)
        ttk.Label(param_frame, text="Material:").grid(row=6, column=0, sticky='w')
        material_var = tk.StringVar(value="Steel")
        material_menu = ttk.Combobox(param_frame, textvariable=material_var, values=list(materials.keys()), state="readonly", width=10)
        material_menu.grid(row=6, column=1)
        def save_design():
            design = {
                "chamber_r": chamber_r_var.get(),
                "throat_r": throat_r_var.get(),
                "exit_r": exit_r_var.get(),
                "length": length_var.get(),
                "angle": angle_var.get(),
                "wall": wall_var.get(),
                "material": material_var.get()
            }
            file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
            if file:
                with open(file, 'w') as f:
                    json.dump(design, f, indent=2)
        def load_design():
            file = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
            if file:
                with open(file, 'r') as f:
                    design = json.load(f)
                chamber_r_var.set(design.get("chamber_r", "0.25"))
                throat_r_var.set(design.get("throat_r", "0.1"))
                exit_r_var.set(design.get("exit_r", "0.3"))
                length_var.set(design.get("length", "1.0"))
                angle_var.set(design.get("angle", "15.0"))
                wall_var.set(design.get("wall", "0.01"))
                material_var.set(design.get("material", "Steel"))
        ttk.Button(param_frame, text="Save Design", command=save_design).grid(row=7, column=0, pady=5)
        ttk.Button(param_frame, text="Load Design", command=load_design).grid(row=7, column=1, pady=5)
        metrics_frame = ttk.LabelFrame(win, text="Performance Metrics")
        metrics_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        metrics_text = tk.StringVar(value="")
        metrics_label = ttk.Label(metrics_frame, textvariable=metrics_text, justify='left')
        metrics_label.pack(anchor='w', padx=5, pady=5)
        plot_frame = ttk.Frame(win)
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        fig, ax = plt.subplots(figsize=(4, 7))
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        def update_plot_and_metrics(*args):
            try:
                chamber_r = float(chamber_r_var.get())
                throat_r = float(throat_r_var.get())
                exit_r = float(exit_r_var.get())
                length = float(length_var.get())
                angle = float(angle_var.get())
                wall = float(wall_var.get())
                mat = material_var.get()
                ax.clear()
                ax.plot([chamber_r, throat_r, exit_r, 0], [0, length*0.2, length, length], color='blue', lw=2)
                ax.plot([-chamber_r, -throat_r, -exit_r, 0], [0, length*0.2, length, length], color='blue', lw=2)
                ax.plot([chamber_r-wall, throat_r-wall, exit_r-wall, 0], [0, length*0.2, length, length], color='gray', lw=1)
                ax.plot([-(chamber_r-wall), -(throat_r-wall), -(exit_r-wall), 0], [0, length*0.2, length, length], color='gray', lw=1)
                ax.set_xlim(-exit_r*1.2, exit_r*1.2)
                ax.set_ylim(-0.1, length+0.1)
                ax.set_aspect('equal')
                ax.set_title('Nozzle Schematic')
                ax.axis('off')
                canvas.draw()
                area_throat = 3.14159 * (throat_r)**2
                area_exit = 3.14159 * (exit_r)**2
                area_chamber = 3.14159 * (chamber_r)**2
                expansion_ratio_calc = area_exit / area_throat if area_throat > 0 else 0
                Pc = 7e6
                Tc = 3500
                k = 1.2
                R = 287
                ve = (2*k/(k-1)*R*Tc*(1-(101325/Pc)**((k-1)/k)))**0.5
                mfr = area_throat * Pc / (ve * k)
                thrust = mfr * ve
                mat_props = materials.get(mat, {"density":0,"max_temp":0})
                wall_vol = (3.14159*((chamber_r)**2-(chamber_r-wall)**2)*length*0.2 + 3.14159*((exit_r)**2-(exit_r-wall)**2)*length*0.8)
                nozzle_mass = wall_vol * mat_props["density"]
                metrics = f"Throat Area: {area_throat:.4f} m²\nExit Area: {area_exit:.4f} m²\nChamber Area: {area_chamber:.4f} m²\nExpansion Ratio: {expansion_ratio_calc:.2f}\nTheoretical ISP: {ve/9.81:.1f} s\nTheoretical Thrust: {thrust/1000:.2f} kN\nNozzle Mass: {nozzle_mass:.2f} kg\nMaterial: {mat}\nMax Temp: {mat_props['max_temp']} K"
                metrics_text.set(metrics)
            except Exception as e:
                metrics_text.set(f"Error: {e}")
        for var in [chamber_r_var, throat_r_var, exit_r_var, length_var, angle_var, wall_var, material_var]:
            var.trace_add('write', update_plot_and_metrics)
        update_plot_and_metrics()
        def apply_to_sim():
            try:
                exit_r = float(exit_r_var.get())
                throat_r = float(throat_r_var.get())
                area_exit = 3.14159 * (exit_r)**2
                area_throat = 3.14159 * (throat_r)**2
                Pc = 7e6
                Tc = 3500
                k = 1.2
                R = 287
                ve = (2*k/(k-1)*R*Tc*(1-(101325/Pc)**((k-1)/k)))**0.5
                mfr = area_throat * Pc / (ve * k)
                expa = 101325  # Assume sea level exit pressure for now
                self.nozzle_vars['ea'].set(f"{area_exit:.4f}")
                self.nozzle_vars['mfr'].set(f"{mfr:.2f}")
                self.nozzle_vars['ve'].set(f"{ve:.2f}")
                self.nozzle_vars['expa'].set(f"{expa:.2f}")
                messagebox.showinfo("Applied", "Nozzle parameters applied to simulation.")
                win.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        ttk.Button(win, text="Apply to Simulation", command=apply_to_sim).pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

    def calculate_cg_cp(self):
        try:
            L = float(self.body_length_var.get())
            D = float(self.body_diam_var.get())
            nose_L = float(self.nose_length_var.get())
            fin_root = float(self.fin_root_var.get())
            fin_tip = float(self.fin_tip_var.get())
            fin_span = float(self.fin_span_var.get())
            fin_num = int(self.fin_num_var.get())
            # CG: assume uniform body, nose is lighter
            cg_body = (L - nose_L/2) * (L - nose_L) / L + nose_L/2 * nose_L / L
            cg = cg_body
            # CP: Barrowman (approx)
            cp_nose = 0.666 * nose_L
            S_fin = 0.5 * (fin_root + fin_tip) * fin_span
            lf = L - nose_L
            cp_fin = lf + (fin_root + fin_tip - fin_root * fin_tip / (fin_root + fin_tip)) / 3
            cp = (cp_nose * nose_L + cp_fin * S_fin * fin_num) / (nose_L + S_fin * fin_num)
            static_margin = (cg - cp) / D
            self.last_cg = cg
            self.last_cp = cp
            self.cgcp_result_var.set(f"CG: {cg:.2f} m, CP: {cp:.2f} m, Static Margin: {static_margin:.2f} D")
            self.draw_cgcp_schematic()
        except Exception as e:
            self.cgcp_result_var.set(f"Error: {e}")

    def get_icon_path(self):
        import sys, os
        if getattr(sys, 'frozen', False):
            meipass = getattr(sys, '_MEIPASS', None)
            if meipass is not None:
                return os.path.join(meipass, 'logo.ico')
        return 'logo.ico'


def main():
    root = tk.Tk()
    app = FlarePieApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()