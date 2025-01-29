import tkinter as tk
from tkinter import messagebox
from Flarepie import rocket_simulation, nozzle_performance  # Import the functions

def simulate_rocket():
    try:
        fuel_type = fuel_type_entry.get()
        cocp = float(cocp_entry.get())
        ct = float(ct_entry.get())
        ap = float(ap_entry.get())
        intmass = float(intmass_entry.get())
        propmass = float(propmass_entry.get())
        mfr = float(mfr_entry.get())
        dt = float(dt_entry.get())

        rocket_simulation(fuel_type, cocp, ct, ap, intmass, propmass, mfr, dt)
    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numeric values.")

def simulate_nozzle():
    try:
        mfr = float(mfr_nozzle_entry.get())
        ve = float(ve_entry.get())
        expa = float(expa_entry.get())
        amp = float(amp_entry.get())
        ea = float(ea_entry.get())

        nozzle_performance(mfr, ve, expa, amp, ea)
    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numeric values.")

root = tk.Tk()
root.title("FlarePie - Rocket Engine Simulator")

tk.Label(root, text="Fuel Type (RP1, LH2, SRF):").grid(row=0, column=0)
fuel_type_entry = tk.Entry(root)
fuel_type_entry.grid(row=0, column=1)

tk.Label(root, text="Combustion Chamber Pressure (Pa):").grid(row=1, column=0)
cocp_entry = tk.Entry(root)
cocp_entry.grid(row=1, column=1)

tk.Label(root, text="Combustion Temperature (K):").grid(row=2, column=0)
ct_entry = tk.Entry(root)
ct_entry.grid(row=2, column=1)

tk.Label(root, text="Atmospheric Pressure (Pa):").grid(row=3, column=0)
ap_entry = tk.Entry(root)
ap_entry.grid(row=3, column=1)

tk.Label(root, text="Total Mass, including Propellant (Kg):").grid(row=4, column=0)
intmass_entry = tk.Entry(root)
intmass_entry.grid(row=4, column=1)

tk.Label(root, text="Propellant Mass (Kg):").grid(row=5, column=0)
propmass_entry = tk.Entry(root)
propmass_entry.grid(row=5, column=1)

tk.Label(root, text="Mass Flow Rate (Kg/s):").grid(row=6, column=0)
mfr_entry = tk.Entry(root)
mfr_entry.grid(row=6, column=1)

tk.Label(root, text="Simulation Timestep (s):").grid(row=7, column=0)
dt_entry = tk.Entry(root)
dt_entry.grid(row=7, column=1)

tk.Button(root, text="Run Rocket Simulation", command=simulate_rocket).grid(row=8, column=0, columnspan=2)

tk.Label(root, text="Mass Flow Rate (Kg/s):").grid(row=9, column=0)
mfr_nozzle_entry = tk.Entry(root)
mfr_nozzle_entry.grid(row=9, column=1)

tk.Label(root, text="Exhaust Velocity (m/s):").grid(row=10, column=0)
ve_entry = tk.Entry(root)
ve_entry.grid(row=10, column=1)

tk.Label(root, text="Exit Pressure (Pa):").grid(row=11, column=0)
expa_entry = tk.Entry(root)
expa_entry.grid(row=11, column=1)

tk.Label(root, text="Ambient Pressure (Pa):").grid(row=12, column=0)
amp_entry = tk.Entry(root)
amp_entry.grid(row=12, column=1)

tk.Label(root, text="Exit Area (m^2):").grid(row=13, column=0)
ea_entry = tk.Entry(root)
ea_entry.grid(row=13, column=1)

tk.Button(root, text="Run Nozzle Performance", command=simulate_nozzle).grid(row=14, column=0, columnspan=2)

root.mainloop()