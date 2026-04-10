
import csv as _csv_module
import logging
import math

import numpy as np

G_ACCEL = 9.80665   
RHO0 = 1.225        
H_SCALE = 8500.0    
P0 = 101325.0       



def _air_density(altitude: float) -> float:
    alt = max(0.0, altitude)
    if alt > 1e6:
        return 0.0
    try:
        return RHO0 * math.exp(-alt / H_SCALE)
    except OverflowError:
        return 0.0


def _atm_pressure(altitude: float) -> float:
    alt = max(0.0, altitude)
    lapse_rate = 2.25577e-5
    exponent = 5.25588
    base = max(0.0, 1.0 - lapse_rate * alt)
    return max(0.0, P0 * base ** exponent)


def _cd_from_mach(mach: float) -> float:
    if mach < 0.8:
        return 0.3
    elif mach < 1.1:
        return 0.3 + (mach - 0.8) * 1.0
    else:
        return 0.6 - 0.1 * min(mach - 1.1, 0.4)




def load_thrust_csv(csv_path: str):
    
    times = []
    thrusts = []
    with open(csv_path, newline='') as f:
        reader = _csv_module.reader(f)
        for row in reader:
            if len(row) < 2:
                continue
            try:
                t_val = float(row[0])
                th_val = float(row[1])
                times.append(t_val)
                thrusts.append(th_val)
            except ValueError:
                continue  

    if not times:
        raise ValueError(f"No valid numeric data found in thrust CSV: {csv_path}")

    return np.array(times, dtype=float), np.array(thrusts, dtype=float)




def _thrust_direction(inclination_deg: float, heading_deg: float):
   
    inc_rad = math.radians(inclination_deg)
    head_rad = math.radians(heading_deg)
    tz = math.sin(inc_rad)
    horiz = math.cos(inc_rad)
    tx = horiz * math.sin(head_rad)   
    ty = horiz * math.cos(head_rad)   
    return (tx, ty, tz)


def simulate_3dof(
    
    fuel_type: str,
    cocp: float,
    ct: float,
    intmass: float,
    propmass: float,
    mfr: float,
    dt: float = 0.1,
    initial_altitude: float = 0.0,
    reference_area: float = 1.0,
    max_time: float = 10000.0,
    inclination_deg: float = 90.0,
    heading_deg: float = 0.0,
    wind_ground: float = 0.0,
    wind_alt: float = 0.0,
    wind_dir_deg: float = 0.0,
    wind_ref_altitude: float = 10000.0,
    thrust_csv_path=None,
):
    
    fuel_properties = {
        "RP1": (1.2, 287.0),
        "LH2": (1.4, 4124.0),
        "SRF": (1.2, 191.0),
        "N2O4": (1.26, 320.0),
    }
    if fuel_type not in fuel_properties:
        return {"error": f"Invalid fuel type: {fuel_type}"}

    k, R = fuel_properties[fuel_type]

    use_csv_thrust = thrust_csv_path is not None
    if use_csv_thrust:
        csv_times, csv_thrusts = load_thrust_csv(thrust_csv_path)

    td_x, td_y, td_z = _thrust_direction(inclination_deg, heading_deg)

    wind_dir_rad = math.radians(wind_dir_deg)
    wind_sin = math.sin(wind_dir_rad)   
    wind_cos = math.cos(wind_dir_rad)   

    def _wind_speed_at(alt):
        if wind_ref_altitude <= 0:
            return wind_ground
        frac = min(max(alt, 0.0) / wind_ref_altitude, 1.0)
        return wind_ground + (wind_alt - wind_ground) * frac

    def _analytical_thrust(z_m):
        ap = _atm_pressure(z_m)
        pr = (ap / cocp) ** ((k - 1.0) / k) if cocp > 0 else 0.0
        ve = math.sqrt(max(0.0, (2.0 * k) / (k - 1.0) * R * ct * (1.0 - pr)))
        return mfr * ve, ve

    def _deriv(state, thrust_mag, mass_now):
    
        px, py, pz, pvx, pvy, pvz = state

        ws = _wind_speed_at(pz)
        wx_w = ws * wind_sin
        wy_w = ws * wind_cos

        vrx = pvx - wx_w
        vry = pvy - wy_w
        vrz = pvz              
        V_rel = math.sqrt(vrx * vrx + vry * vry + vrz * vrz)

        density = _air_density(pz)
        p_atm = _atm_pressure(pz)
        sos = 340.0 * math.sqrt(p_atm / P0) if p_atm > 0 else 1.0
        mach = V_rel / max(sos, 0.1)
        cd = _cd_from_mach(mach)
        drag_mag = 0.5 * density * V_rel * V_rel * cd * reference_area

        if V_rel > 0:
            inv_v = 1.0 / V_rel
            d_x = -drag_mag * vrx * inv_v
            d_y = -drag_mag * vry * inv_v
            d_z = -drag_mag * vrz * inv_v
        else:
            d_x = d_y = d_z = 0.0

        fx = thrust_mag * td_x + d_x
        fy = thrust_mag * td_y + d_y
        fz = thrust_mag * td_z + d_z

        inv_m = 1.0 / max(mass_now, 1e-6)
        return [pvx, pvy, pvz,
                fx * inv_m,
                fy * inv_m,
                fz * inv_m - G_ACCEL]

    x, y, z = 0.0, 0.0, float(initial_altitude)
    vx, vy, vz = 0.0, 0.0, 0.0
    current_mass = float(intmass)
    prop_remaining = float(propmass)
    t = 0.0

    time_steps = []
    thrust_values = []
    fuel_remaining = []
    mass_flow_values = []
    velocity_values = []       
    altitude_values = []       
    isp_values = []
    drag_values = []
    acceleration_values = []
    energy_values = []
    position_list = []
    velocity_vector_list = []

    delta_v = 0.0
    initial_thrust = None

    while prop_remaining >= 0 and t < max_time:
        if prop_remaining > 0:
            mass_used = min(mfr * dt, prop_remaining)
            step_mfr = mass_used / dt   

            if use_csv_thrust:
                thrust = float(np.interp(t, csv_times, csv_thrusts,
                                         left=float(csv_thrusts[0]),
                                         right=0.0))
                ve_exhaust = thrust / step_mfr if step_mfr > 0 else 0.0
            else:
                thrust, ve_exhaust = _analytical_thrust(z)
        else:
            mass_used = 0.0
            step_mfr = 0.0
            thrust = 0.0
            ve_exhaust = 0.0

        if initial_thrust is None:
            initial_thrust = thrust

  
        state = [x, y, z, vx, vy, vz]

        k1 = _deriv(state, thrust, current_mass)
        s2 = [s + 0.5 * dt * d for s, d in zip(state, k1)]
        k2 = _deriv(s2, thrust, current_mass)
        s3 = [s + 0.5 * dt * d for s, d in zip(state, k2)]
        k3 = _deriv(s3, thrust, current_mass)
        s4 = [s + dt * d for s, d in zip(state, k3)]
        k4 = _deriv(s4, thrust, current_mass)

        new_state = [
            s + dt * (d1 + 2.0 * d2 + 2.0 * d3 + d4) / 6.0
            for s, d1, d2, d3, d4 in zip(state, k1, k2, k3, k4)
        ]
        x_n, y_n, z_n, vx_n, vy_n, vz_n = new_state

       
        V = math.sqrt(vx * vx + vy * vy + vz * vz)
        V_new = math.sqrt(vx_n * vx_n + vy_n * vy_n + vz_n * vz_n)

       
        ws = _wind_speed_at(z)
        vrx = vx - ws * wind_sin
        vry = vy - ws * wind_cos
        vrz = vz
        V_rel = math.sqrt(vrx * vrx + vry * vry + vrz * vrz)
        density = _air_density(z)
        p_atm = _atm_pressure(z)
        sos = 340.0 * math.sqrt(p_atm / P0) if p_atm > 0 else 1.0
        mach_num = V_rel / max(sos, 0.1)
        cd_cur = _cd_from_mach(mach_num)
        drag_cur = 0.5 * density * V_rel * V_rel * cd_cur * reference_area

        accel_deriv = _deriv(state, thrust, current_mass)
        accel_mag = math.sqrt(accel_deriv[3] ** 2 +
                              accel_deriv[4] ** 2 +
                              accel_deriv[5] ** 2)

        isp = ve_exhaust / G_ACCEL if ve_exhaust > 0 else 0.0

        delta_v_step = (thrust / current_mass) * dt if current_mass > 0 else 0.0
        delta_v += delta_v_step

        ke = 0.5 * current_mass * V * V
        pe = current_mass * G_ACCEL * z
        energy_values.append(ke + pe)

        time_steps.append(t)
        thrust_values.append(thrust)
        fuel_remaining.append(prop_remaining)
        mass_flow_values.append(step_mfr)
        velocity_values.append(V)
        altitude_values.append(z)
        isp_values.append(isp)
        drag_values.append(drag_cur)
        acceleration_values.append(accel_mag)
        position_list.append([x, y, z])
        velocity_vector_list.append([vx, vy, vz])

        x, y, z = x_n, y_n, z_n
        vx, vy, vz = vx_n, vy_n, vz_n
        prop_remaining -= mass_used
        current_mass -= mass_used
        if current_mass < (intmass - propmass):
            current_mass = intmass - propmass  
        t += dt

        if prop_remaining <= 0:
            break

    logging.info(
        "Simulation Complete. t=%.2fs  max_alt=%.1fm  max_speed=%.1fm/s",
        t,
        max(altitude_values) if altitude_values else 0.0,
        max(velocity_values) if velocity_values else 0.0,
    )

    return {
        "time": time_steps,
        "thrust": thrust_values,
        "fuel_remaining": fuel_remaining,
        "mass_flow": mass_flow_values,
        "velocity": velocity_values,
        "altitude": altitude_values,
        "isp_values": isp_values,
        "drag": drag_values,
        "acceleration": acceleration_values,
        "energy": energy_values,
        "final_time": t,
        "initial_thrust": initial_thrust if initial_thrust is not None else 0.0,
        "delta_v": delta_v,
        "simulation_complete": True,
        "position": position_list,
        "velocity_vector": velocity_vector_list,
    }
