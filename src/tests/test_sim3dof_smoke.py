"""
Smoke test for the 3-DOF simulation backend.

Run with:
    cd src && python tests/test_sim3dof_smoke.py

No GUI required. Exercises:
  1. Constant (analytical) thrust — vertical launch.
  2. CSV thrust curve — 30-degree angled launch with wind.
  3. Engine.rocket_simulation_3dof adapter.
"""

import math
import os
import sys
import tempfile

# Allow running from repo root or from src/
_here = os.path.dirname(__file__)
_src = os.path.join(_here, "..")
if _src not in sys.path:
    sys.path.insert(0, _src)

from sim3dof import simulate_3dof, load_thrust_csv


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _check(name, results):
    assert "error" not in results, f"{name}: simulation returned error: {results['error']}"
    assert results["simulation_complete"], f"{name}: simulation_complete is False"
    assert len(results["time"]) > 0, f"{name}: no time steps recorded"
    max_alt = max(results["altitude"])
    max_spd = max(results["velocity"])
    print(f"  [{name}]  steps={len(results['time'])}  "
          f"max_alt={max_alt:.1f} m  max_speed={max_spd:.1f} m/s  "
          f"delta_v={results['delta_v']:.1f} m/s  "
          f"final_time={results['final_time']:.2f} s")
    assert max_alt > 0, f"{name}: max altitude should be positive"
    assert max_spd >= 0, f"{name}: max speed should be non-negative"
    assert "position" in results, f"{name}: missing 'position' key"
    assert "velocity_vector" in results, f"{name}: missing 'velocity_vector' key"
    assert len(results["position"]) == len(results["time"]), \
        f"{name}: position length mismatch"
    return max_alt, max_spd


# ---------------------------------------------------------------------------
# Test 1: vertical launch, analytical thrust
# ---------------------------------------------------------------------------

def test_vertical_analytical():
    results = simulate_3dof(
        fuel_type="RP1",
        cocp=7_000_000,
        ct=3500,
        intmass=10_000,
        propmass=8_000,
        mfr=250,
        dt=0.1,
        inclination_deg=90,
        heading_deg=0,
        wind_ground=0,
        wind_alt=0,
        wind_dir_deg=0,
    )
    max_alt, max_spd = _check("vertical/analytical", results)

    # Vertical launch: x and y displacement should remain near zero
    final_pos = results["position"][-1]
    assert abs(final_pos[0]) < 1e-6, "East displacement should be ~0 for vertical launch"
    assert abs(final_pos[1]) < 1e-6, "North displacement should be ~0 for vertical launch"


# ---------------------------------------------------------------------------
# Test 2: angled launch with wind and CSV thrust curve
# ---------------------------------------------------------------------------

def test_angled_csv_thrust():
    # Build a simple CSV thrust curve: ramps up then holds steady.
    # Use parameters that give T/W > 1 even at 60° inclination:
    #   thrust_z = 8000 * sin(60°) ≈ 6928 N > 250*9.81=2452 N ✓
    csv_data = "time_s,thrust_n\n0,0\n0.5,8000\n1.0,8000\n10.0,8000\n12.0,0\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_data)
        csv_path = f.name

    try:
        results = simulate_3dof(
            fuel_type="RP1",
            cocp=7_000_000,
            ct=3500,
            intmass=250,
            propmass=200,
            mfr=20,
            dt=0.1,
            inclination_deg=60,    # 60° above horizon
            heading_deg=45,        # NE
            wind_ground=5.0,       # 5 m/s at ground
            wind_alt=15.0,         # 15 m/s at 10 km
            wind_dir_deg=90,       # blowing East
            thrust_csv_path=csv_path,
        )
    finally:
        os.unlink(csv_path)

    max_alt, max_spd = _check("angled/csv-thrust", results)

    # With 60° inclination there should be some horizontal displacement
    final_pos = results["position"][-1]
    horiz_disp = math.sqrt(final_pos[0] ** 2 + final_pos[1] ** 2)
    assert horiz_disp > 0, "Horizontal displacement should be > 0 for angled launch"


# ---------------------------------------------------------------------------
# Test 3: Engine.py adapter
# ---------------------------------------------------------------------------

def test_engine_adapter():
    from Engine import rocket_simulation_3dof
    results = rocket_simulation_3dof(
        fuel_type="LH2",
        cocp=9_000_000,
        ct=3700,
        altitude=0,
        intmass=20_000,
        propmass=16_000,
        mfr=400,
        dt=0.1,
        reference_area=1.2,
        inclination_deg=90,
        heading_deg=0,
    )
    _check("adapter/LH2-vertical", results)


# ---------------------------------------------------------------------------
# Test 4: CSV loading helper
# ---------------------------------------------------------------------------

def test_load_thrust_csv():
    csv_data = "# header line\ntime_s,thrust_n\n0,100\n5,500\n10,300\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_data)
        csv_path = f.name
    try:
        times, thrusts = load_thrust_csv(csv_path)
    finally:
        os.unlink(csv_path)

    assert list(times) == [0, 5, 10], f"Unexpected times: {times}"
    assert list(thrusts) == [100, 500, 300], f"Unexpected thrusts: {thrusts}"
    print("  [load_thrust_csv]  OK — 3 data rows loaded, header skipped")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Running 3-DOF smoke tests...\n")
    test_load_thrust_csv()
    test_vertical_analytical()
    test_angled_csv_thrust()
    test_engine_adapter()
    print("\nAll smoke tests passed.")
