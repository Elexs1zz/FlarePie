"""
3-DOF point-mass rocket flight dynamics simulation.

State vector: position (x, y, z) and velocity (vx, vy, vz) in a local ENU frame.
  x = East  (m)
  y = North (m)
  z = Up    (m) — altitude above launch point origin

Physics:
  - Gravity: constant g = 9.80665 m/s^2 in -z direction.
  - Atmosphere: exponential density model (consistent with Engine.py).
  - Drag: D = 0.5 * rho * V_rel^2 * Cd(Mach) * A, opposing relative airspeed.
  - Wind: linear increase with altitude from ground value to altitude value.
  - Thrust: fixed direction defined by launch inclination and heading angles.
  - Mass: depletes at constant mass_flow_rate until propellant exhausted.
  - Thrust curve: optionally loaded from a CSV file (time_s, thrust_n columns).

Output dict is compatible with the existing UI result schema:
  time, thrust, fuel_remaining, mass_flow, velocity (speed magnitude),
  altitude (z), isp_values, drag (magnitude), acceleration (magnitude), energy,
  final_time, initial_thrust, delta_v, simulation_complete.
Extra outputs (for future 3-D plotting):
  position      — list of [x, y, z] at each step
  velocity_vector — list of [vx, vy, vz] at each step
"""

import csv as _csv_module
import logging
import math

import numpy as np

# Physical constants
G_ACCEL = 9.80665   # m/s^2
RHO0 = 1.225        # kg/m^3 sea-level air density
H_SCALE = 8500.0    # density scale height (m)
P0 = 101325.0       # sea-level pressure (Pa)


# ---------------------------------------------------------------------------
# Atmosphere helpers (consistent with Engine.py)
# ---------------------------------------------------------------------------

def _air_density(altitude: float) -> float:
    """Exponential atmosphere density model."""
    alt = max(0.0, altitude)
    if alt > 1e6:
        return 0.0
    try:
        return RHO0 * math.exp(-alt / H_SCALE)
    except OverflowError:
        return 0.0


def _atm_pressure(altitude: float) -> float:
    """ISA-approximate pressure model (matches Engine.get_atmospheric_pressure)."""
    alt = max(0.0, altitude)
    lapse_rate = 2.25577e-5
    exponent = 5.25588
    base = max(0.0, 1.0 - lapse_rate * alt)
    return max(0.0, P0 * base ** exponent)


def _cd_from_mach(mach: float) -> float:
    """Simple Mach-dependent drag coefficient (matches Engine.calculate_drag)."""
    if mach < 0.8:
        return 0.3
    elif mach < 1.1:
        return 0.3 + (mach - 0.8) * 1.0
    else:
        return 0.6 - 0.1 * min(mach - 1.1, 0.4)


# ---------------------------------------------------------------------------
# Thrust-curve CSV loader
# ---------------------------------------------------------------------------

def load_thrust_csv(csv_path: str):
    """
    Load a thrust curve CSV file.

    Expected format: two columns (time_s, thrust_n) with an optional header row.
    Rows whose first column cannot be parsed as a float (e.g. header text) are
    silently skipped.

    Returns (times_array, thrusts_array) as 1-D numpy arrays.
    Raises ValueError if the file contains no valid numeric rows.
    """
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
                continue  # skip header / non-numeric rows

    if not times:
        raise ValueError(f"No valid numeric data found in thrust CSV: {csv_path}")

    return np.array(times, dtype=float), np.array(thrusts, dtype=float)


# ---------------------------------------------------------------------------
# Geometry helper
# ---------------------------------------------------------------------------

def _thrust_direction(inclination_deg: float, heading_deg: float):
    """
    Return a unit thrust-direction vector in the ENU frame.

    inclination_deg : angle above the horizon (90 = straight up, 0 = horizontal).
    heading_deg     : compass bearing of the horizontal projection
                      (0 = North, 90 = East).
    """
    inc_rad = math.radians(inclination_deg)
    head_rad = math.radians(heading_deg)
    tz = math.sin(inc_rad)
    horiz = math.cos(inc_rad)
    tx = horiz * math.sin(head_rad)   # East
    ty = horiz * math.cos(head_rad)   # North
    return (tx, ty, tz)


# ---------------------------------------------------------------------------
# Main simulation function
# ---------------------------------------------------------------------------

def simulate_3dof(
    # Propellant / engine
    fuel_type: str,
    cocp: float,
    ct: float,
    intmass: float,
    propmass: float,
    mfr: float,
    # Numerics
    dt: float = 0.1,
    initial_altitude: float = 0.0,
    reference_area: float = 1.0,
    max_time: float = 10000.0,
    # Launch geometry
    inclination_deg: float = 90.0,
    heading_deg: float = 0.0,
    # Wind
    wind_ground: float = 0.0,
    wind_alt: float = 0.0,
    wind_dir_deg: float = 0.0,
    wind_ref_altitude: float = 10000.0,
    # Optional thrust-curve CSV
    thrust_csv_path=None,
):
    """
    Run a 3-DOF point-mass rocket simulation using RK4 integration.

    Parameters
    ----------
    fuel_type      : one of 'RP1', 'LH2', 'SRF', 'N2O4'
    cocp           : chamber pressure (Pa)
    ct             : combustion temperature (K)
    intmass        : total initial mass (kg)
    propmass       : propellant mass (kg)
    mfr            : nominal mass flow rate (kg/s)
    dt             : time step (s)
    initial_altitude: launch altitude above sea level (m)
    reference_area : aerodynamic reference area (m²)
    max_time       : hard upper limit on simulation time (s)
    inclination_deg: launch elevation angle (90 = vertical, 0 = horizontal)
    heading_deg    : launch compass bearing, horizontal projection (0 = N, 90 = E)
    wind_ground    : wind speed at ground level (m/s)
    wind_alt       : wind speed at wind_ref_altitude (m/s)
    wind_dir_deg   : direction the wind blows *toward* (0 = N, 90 = E)
    wind_ref_altitude: altitude at which wind_alt applies (m)
    thrust_csv_path: path to a CSV thrust curve, or None for analytical thrust

    Returns
    -------
    dict with keys:
      time, thrust, fuel_remaining, mass_flow, velocity (speed magnitude),
      altitude (z), isp_values, drag (magnitude), acceleration (magnitude),
      energy, final_time, initial_thrust, delta_v, simulation_complete,
      position (list of [x,y,z]), velocity_vector (list of [vx,vy,vz]).
    On error: {'error': <message>}.
    """
    fuel_properties = {
        "RP1": (1.2, 287.0),
        "LH2": (1.4, 4124.0),
        "SRF": (1.2, 191.0),
        "N2O4": (1.26, 320.0),
    }
    if fuel_type not in fuel_properties:
        return {"error": f"Invalid fuel type: {fuel_type}"}

    k, R = fuel_properties[fuel_type]

    # --- Thrust curve setup ---
    use_csv_thrust = thrust_csv_path is not None
    if use_csv_thrust:
        csv_times, csv_thrusts = load_thrust_csv(thrust_csv_path)

    # --- Fixed thrust direction (unit vector in ENU) ---
    td_x, td_y, td_z = _thrust_direction(inclination_deg, heading_deg)

    # --- Wind direction components (wind blows *toward* wind_dir_deg) ---
    wind_dir_rad = math.radians(wind_dir_deg)
    wind_sin = math.sin(wind_dir_rad)   # East
    wind_cos = math.cos(wind_dir_rad)   # North

    def _wind_speed_at(alt):
        """Linear wind profile."""
        if wind_ref_altitude <= 0:
            return wind_ground
        frac = min(max(alt, 0.0) / wind_ref_altitude, 1.0)
        return wind_ground + (wind_alt - wind_ground) * frac

    def _analytical_thrust(z_m):
        """Thermodynamic thrust varying with ambient back-pressure."""
        ap = _atm_pressure(z_m)
        pr = (ap / cocp) ** ((k - 1.0) / k) if cocp > 0 else 0.0
        ve = math.sqrt(max(0.0, (2.0 * k) / (k - 1.0) * R * ct * (1.0 - pr)))
        return mfr * ve, ve

    def _deriv(state, thrust_mag, mass_now):
        """
        RHS of the EOM for RK4.
        state = [x, y, z, vx, vy, vz]
        Returns [dx/dt, dy/dt, dz/dt, d²x/dt², d²y/dt², d²z/dt²].
        """
        px, py, pz, pvx, pvy, pvz = state

        # Wind at this altitude
        ws = _wind_speed_at(pz)
        wx_w = ws * wind_sin
        wy_w = ws * wind_cos

        # Relative (air) velocity
        vrx = pvx - wx_w
        vry = pvy - wy_w
        vrz = pvz              # no vertical wind component
        V_rel = math.sqrt(vrx * vrx + vry * vry + vrz * vrz)

        # Aerodynamic drag
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

        # Thrust force
        fx = thrust_mag * td_x + d_x
        fy = thrust_mag * td_y + d_y
        fz = thrust_mag * td_z + d_z

        inv_m = 1.0 / max(mass_now, 1e-6)
        return [pvx, pvy, pvz,
                fx * inv_m,
                fy * inv_m,
                fz * inv_m - G_ACCEL]

    # --- Initial state ---
    x, y, z = 0.0, 0.0, float(initial_altitude)
    vx, vy, vz = 0.0, 0.0, 0.0
    current_mass = float(intmass)
    prop_remaining = float(propmass)
    t = 0.0

    # --- Output arrays ---
    time_steps = []
    thrust_values = []
    fuel_remaining = []
    mass_flow_values = []
    velocity_values = []       # speed magnitude
    altitude_values = []       # z
    isp_values = []
    drag_values = []
    acceleration_values = []
    energy_values = []
    position_list = []
    velocity_vector_list = []

    delta_v = 0.0
    initial_thrust = None

    while prop_remaining >= 0 and t < max_time:
        # ---- Determine thrust and mass flow for this step ----
        if prop_remaining > 0:
            mass_used = min(mfr * dt, prop_remaining)
            step_mfr = mass_used / dt   # effective mfr for this step

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

        # ---- RK4 integration (6-state: x,y,z,vx,vy,vz) ----
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

        # ---- Derived quantities at the *current* step (before update) ----
        V = math.sqrt(vx * vx + vy * vy + vz * vz)
        V_new = math.sqrt(vx_n * vx_n + vy_n * vy_n + vz_n * vz_n)

        # Drag magnitude at current position / velocity
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

        # Net acceleration magnitude
        accel_deriv = _deriv(state, thrust, current_mass)
        accel_mag = math.sqrt(accel_deriv[3] ** 2 +
                              accel_deriv[4] ** 2 +
                              accel_deriv[5] ** 2)

        # ISP
        isp = ve_exhaust / G_ACCEL if ve_exhaust > 0 else 0.0

        # Delta-V: accumulate thrust-derived impulse per unit mass (rocket equation rate).
        # This gives the ideal propulsive delta-V, independent of gravity/drag losses.
        delta_v_step = (thrust / current_mass) * dt if current_mass > 0 else 0.0
        delta_v += delta_v_step

        # Mechanical energy
        ke = 0.5 * current_mass * V * V
        pe = current_mass * G_ACCEL * z
        energy_values.append(ke + pe)

        # ---- Record data ----
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

        # ---- Advance state ----
        x, y, z = x_n, y_n, z_n
        vx, vy, vz = vx_n, vy_n, vz_n
        prop_remaining -= mass_used
        current_mass -= mass_used
        if current_mass < (intmass - propmass):
            current_mass = intmass - propmass  # clamp to dry mass
        t += dt

        if prop_remaining <= 0:
            break

    logging.info(
        "3-DOF simulation complete. t=%.2fs  max_alt=%.1fm  max_speed=%.1fm/s",
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
        # 3-D extras
        "position": position_list,
        "velocity_vector": velocity_vector_list,
    }
