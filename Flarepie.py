import math

def rocket_simulation(fuel_type, cocp, ct, ap, intmass, propmass, mfr, dt):
    if fuel_type == "RP1":
        k = 1.2
        R = 287.0
    elif fuel_type == "LH2":
        k = 1.4
        R = 4124.0
    elif fuel_type == "SRF":
        k = 1.2
        R = 191.0
    else:
        print("Invalid fuel type")
        return

    ve = math.sqrt((2 * k) / (k - 1) * R * ct * (1 - (ap / cocp) ** ((k - 1) / k)))
    cm = intmass
    te = 0.0

    while propmass > 0:
        thrust = mfr * ve
        massUsed = mfr * dt
        if massUsed > propmass:
            massUsed = propmass

        propmass -= massUsed
        cm -= massUsed

        print(f"Time: {te} s | Thrust: {thrust} N | Remaining Propellant: {propmass} kg | Total Mass: {cm} kg")

        te += dt

    print("Propellant Consumed! Simulation Ended.")

def nozzle_performance(mfr, ve, expa, amp, ea):
    f = (mfr * ve) + ((expa - amp) * ea)
    print(f"Thrust (F): {f} N")

    si = f / (mfr * 9.81)
    print(f"Specific Impulse (Isp): {si} s")

def main():
    print("Welcome to FlarePie! - Open Source Rocket Engine Simulator -")
    print("For Rocket Engine Simulator, type 1. For Nozzle Performance Calculator, type 2.")
    inp = int(input())

    if inp == 1:
        fuel_type = input("Fuel Type (RP1, LH2, SRF): ")
        cocp = float(input("Combustion Chamber Pressure (Pa): "))
        ct = float(input("Combustion Temperature (K): "))
        ap = float(input("Atmospheric Pressure (Pa): "))
        intmass = float(input("Total Mass, including Propellant (Kg): "))
        propmass = float(input("Propellant Mass (Kg): "))
        mfr = float(input("Mass Flow Rate (Kg/s): "))
        dt = float(input("Simulation Timestep (s): "))

        rocket_simulation(fuel_type, cocp, ct, ap, intmass, propmass, mfr, dt)
    elif inp == 2:
        mfr = float(input("Mass Flow Rate (Kg/s): "))
        ve = float(input("Exhaust Velocity (m/s): "))
        expa = float(input("Exit Pressure (Pa): "))
        amp = float(input("Ambient Pressure (Pa): "))
        ea = float(input("Exit Area (m^2): "))

        nozzle_performance(mfr, ve, expa, amp, ea)

if __name__ == "__main__":
    main()