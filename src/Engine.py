import math
import logging
import numpy as np
from datetime import datetime

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename=f"rocket_simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)


def get_atmospheric_pressure(altitude):
    altitude = max(0, altitude)
    p0 = 101325.0
    lapse_rate = 2.25577e-5
    exponent = 5.25588
    base = max(0.0, 1 - lapse_rate * altitude)
    if base == 0.0:
        pressure = 0.0
    else:
        pressure = p0 * base ** exponent
    return max(pressure, 0.0)


def calculate_drag(velocity, altitude, reference_area=1.0):

    p0 = 1.225
    h0 = 8500
    try:
        if altitude > 1e6:
            density = 0.0
        else:
            density = p0 * math.exp(-altitude / h0)
    except OverflowError:
        density = 0.0


    speed_of_sound = 340.0 * math.sqrt(get_atmospheric_pressure(altitude) / 101325.0)
    mach = abs(velocity) / max(speed_of_sound, 0.1)

    if mach < 0.8:
        cd = 0.3
    elif mach < 1.1:
        cd = 0.3 + (mach - 0.8) * 1.0
    else:
        cd = 0.6 - 0.1 * min(mach - 1.1, 0.4)

    drag = 0.5 * density * velocity ** 2 * reference_area * cd
    return drag if velocity > 0 else -drag


def rocket_simulation(fuel_type, cocp, ct, altitude, intmass, propmass, mfr, dt,
                      reference_area=1.0, real_time_mode=False, max_time=None):

    fuel_properties = {
        "RP1": (1.2, 287.0),
        "LH2": (1.4, 4124.0),
        "SRF": (1.2, 191.0),
        "N2O4": (1.26, 320.0)
    }

    if fuel_type not in fuel_properties:
        return {"error": "Invalid fuel type"}

    k, R = fuel_properties[fuel_type]

    current_mass = intmass
    time_elapsed = 0.0
    velocity = 0.0
    current_altitude = altitude
    delta_v = 0.0
    energy_values = []
    drag_values = []
    acceleration_values = []

    time_steps, thrust_values, fuel_remaining, mass_flow_values = [], [], [], []
    velocity_values, altitude_values, isp_values = [], [], []

    logging.info(f"Starting simulation: Fuel={fuel_type}, Initial Mass={intmass} kg, Propellant={propmass} kg")


    last_return_time = 0.0
    real_time_data_interval = 0.25

    while propmass > 0 and (max_time is None or time_elapsed < max_time):
        ap = get_atmospheric_pressure(current_altitude)
        pressure_ratio = (ap / cocp) ** ((k - 1) / k) if cocp > 0 else 0.0

        ve = math.sqrt((2.0 * k) / (k - 1.0) * R * ct * (1.0 - pressure_ratio))
        thrust = mfr * ve

        mass_used = min(mfr * dt, propmass)
        propmass -= mass_used
        current_mass -= mass_used

        drag = calculate_drag(velocity, current_altitude, reference_area)

        acceleration = (thrust / current_mass) - 9.81 - (drag / current_mass)

        velocity_mid = velocity + 0.5 * acceleration * dt
        altitude_mid = current_altitude + 0.5 * velocity * dt

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

        if int(time_elapsed) % 5 == 0 or time_elapsed < 1.0:
            logging.info(
                f"t={time_elapsed:.2f}s | Thrust={thrust:.2f} N | Velocity={velocity:.2f} m/s | "
                f"Altitude={current_altitude:.2f} m | ΔV={delta_v_step:.2f} m/s | Drag={drag:.2f} N"
            )

        velocity = velocity_new
        current_altitude = altitude_new
        time_elapsed += dt

        if real_time_mode and time_elapsed - last_return_time >= real_time_data_interval:
            last_return_time = time_elapsed
            return {
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
                "simulation_complete": False
            }

    logging.info("Simulation complete.")

    return {
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
        "simulation_complete": True
    }


def nozzle_performance(mfr, ve, expa, amp, ea):
    thrust = (mfr * ve) + ((expa - amp) * ea)
    isp = thrust / (mfr * 9.81) if mfr > 0 else 0.0

    expansion_ratio = ea / 0.01
    pressure_ratio = expa / amp if amp > 0 else 0

    ideal_expansion = abs(expa - amp) < 0.1 * amp
    efficiency = 0.95 if ideal_expansion else 0.85 - 0.1 * min(abs(math.log10(pressure_ratio + 0.1)), 1.0)

    return {
        "thrust": thrust,
        "isp": isp,
        "pressure_thrust": (expa - amp) * ea,
        "momentum_thrust": mfr * ve,
        "expansion_ratio": expansion_ratio,
        "pressure_ratio": pressure_ratio,
        "efficiency": efficiency
    }


def generate_atmosphere_profile(max_altitude=100000, steps=100):
    altitudes = np.linspace(0, max_altitude, steps)
    pressures = [get_atmospheric_pressure(alt) for alt in altitudes]
    temperatures = [288.15 - min(alt / 100, 80) for alt in altitudes]

    return {
        "altitude": altitudes,
        "pressure": pressures,
        "temperature": temperatures
    }