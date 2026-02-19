import math
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from Engine import rocket_simulation, nozzle_performance, get_atmospheric_pressure

@dataclass
class Stage:

    name: str
    fuel_type: str
    chamber_pressure: float
    combustion_temp: float
    total_mass: float
    propellant_mass: float
    mass_flow_rate: float
    reference_area: float
    separation_altitude: Optional[float] = None
    separation_time: Optional[float] = None
    fairing_mass: float = 0.0
    fairing_separation_altitude: Optional[float] = None

@dataclass
class OrbitalParameters:
    semi_major_axis: float
    eccentricity: float
    inclination: float
    argument_of_periapsis: float
    longitude_of_ascending_node: float
    true_anomaly: float

class AdvancedRocketEngine:

    def __init__(self):
        self.stages: List[Stage] = []
        self.current_stage = 0
        self.separation_events = []
        self.orbital_data = []
        
    def add_stage(self, stage: Stage):
        self.stages.append(stage)
    
    def multi_stage_simulation(self, dt: float = 0.1, max_time: Optional[float] = None) -> Dict:
        if not self.stages:
            return {"error": "No stages defined"}
        
        time_data = []
        altitude_data = []
        velocity_data = []
        mass_data = []
        thrust_data = []
        stage_data = []
        events = []
        
        current_time = 0.0
        current_altitude = 0.0
        current_velocity = 0.0
        current_mass = sum(stage.total_mass for stage in self.stages)
        
        stage_masses = [stage.total_mass for stage in self.stages]
        stage_propellants = [stage.propellant_mass for stage in self.stages]
        stage_flow_rates = [stage.mass_flow_rate for stage in self.stages]
        
        while current_time < (max_time or float('inf')):
            if self.current_stage < len(self.stages):
                stage = self.stages[self.current_stage]
                
                if (stage.separation_altitude and current_altitude >= stage.separation_altitude) or \
                   (stage.separation_time and current_time >= stage.separation_time):
                    events.append({
                        "time": current_time,
                        "type": "stage_separation",
                        "stage": self.current_stage,
                        "altitude": current_altitude,
                        "velocity": current_velocity
                    })
                    self.current_stage += 1
                    continue
            
            if self.current_stage < len(self.stages):
                stage = self.stages[self.current_stage]
                if (stage.fairing_separation_altitude and 
                    current_altitude >= stage.fairing_separation_altitude and
                    stage.fairing_mass > 0):
                    events.append({
                        "time": current_time,
                        "type": "fairing_separation",
                        "stage": self.current_stage,
                        "altitude": current_altitude,
                        "mass_jettisoned": stage.fairing_mass
                    })
                    current_mass -= stage.fairing_mass
                    stage.fairing_mass = 0
            
            if self.current_stage < len(self.stages):
                stage = self.stages[self.current_stage]
                
                ap = get_atmospheric_pressure(current_altitude)
                k, R = self._get_fuel_properties(stage.fuel_type)
                pressure_ratio = (ap / stage.chamber_pressure) ** ((k - 1) / k) if stage.chamber_pressure > 0 else 0.0
                ve = math.sqrt((2.0 * k) / (k - 1.0) * R * stage.combustion_temp * (1.0 - pressure_ratio))
                thrust = stage_flow_rates[self.current_stage] * ve
                
                mass_used = min(stage_flow_rates[self.current_stage] * dt, stage_propellants[self.current_stage])
                stage_propellants[self.current_stage] -= mass_used
                current_mass -= mass_used
                
                if stage_propellants[self.current_stage] <= 0:
                    events.append({
                        "time": current_time,
                        "type": "stage_depletion",
                        "stage": self.current_stage,
                        "altitude": current_altitude,
                        "velocity": current_velocity
                    })
                    self.current_stage += 1
                    continue
            else:
                thrust = 0
                events.append({
                    "time": current_time,
                    "type": "mission_complete",
                    "altitude": current_altitude,
                    "velocity": current_velocity
                })
                break
            
            drag = self._calculate_drag(current_velocity, current_altitude,
                                      self.stages[self.current_stage].reference_area)
            acceleration = (thrust / current_mass) - 9.81 - (drag / current_mass)
            
            velocity_new, altitude_new = self._rk4_integration(
                current_velocity, current_altitude, acceleration, dt
            )
            
            time_data.append(current_time)
            altitude_data.append(current_altitude)
            velocity_data.append(current_velocity)
            mass_data.append(current_mass)
            thrust_data.append(thrust)
            stage_data.append(self.current_stage)
            
            current_velocity = velocity_new
            current_altitude = altitude_new
            current_time += dt
        
        return {
            "time": time_data,
            "altitude": altitude_data,
            "velocity": velocity_data,
            "mass": mass_data,
            "thrust": thrust_data,
            "stage": stage_data,
            "events": events,
            "final_time": current_time,
            "max_altitude": max(altitude_data) if altitude_data else 0,
            "max_velocity": max(velocity_data) if velocity_data else 0
        }
    
    def _get_fuel_properties(self, fuel_type: str) -> Tuple[float, float]:
        fuel_properties = {
            "RP1": (1.2, 287.0),
            "LH2": (1.4, 4124.0),
            "SRF": (1.2, 191.0),
            "N2O4": (1.26, 320.0)
        }
        return fuel_properties.get(fuel_type, (1.2, 287.0))
    
    def _calculate_drag(self, velocity: float, altitude: float, reference_area: float) -> float:
        p0 = 1.225
        h0 = 8500
        density = p0 * math.exp(-altitude / h0)
        
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
    
    def _rk4_integration(self, v: float, h: float, a: float, dt: float) -> Tuple[float, float]:

        k1_v = a * dt
        k1_h = v * dt
        

        k2_v = a * dt
        k2_h = (v + 0.5 * k1_v) * dt
        

        k3_v = a * dt
        k3_h = (v + 0.5 * k2_v) * dt
        
        k4_v = a * dt
        k4_h = (v + k3_v) * dt
        
        v_new = v + (k1_v + 2*k2_v + 2*k3_v + k4_v) / 6
        h_new = h + (k1_h + 2*k2_h + 2*k3_h + k4_h) / 6
        
        return v_new, h_new

class OrbitalMechanics:

    G = 6.67430e-11
    M_EARTH = 5.972e24
    R_EARTH = 6.371e6
    
    @staticmethod
    def calculate_orbital_parameters(position: np.ndarray, velocity: np.ndarray) -> OrbitalParameters:
        r = np.linalg.norm(position)
        v = np.linalg.norm(velocity)
        
        h = np.cross(position, velocity)
        h_mag = np.linalg.norm(h)
        
        mu = OrbitalMechanics.G * OrbitalMechanics.M_EARTH
        e_vec = np.cross(velocity, h) / mu - position / r
        e = np.linalg.norm(e_vec)
        
        energy = 0.5 * v**2 - mu / r
        a = -mu / (2 * energy) if energy < 0 else float('inf')
        
        i = math.acos(h[2] / h_mag)
        
        n = np.cross([0, 0, 1], h)
        n_mag = np.linalg.norm(n)
        if n_mag > 0:
            omega = math.acos(n[0] / n_mag)
            if n[1] < 0:
                omega = 2 * math.pi - omega
        else:
            omega = 0
        
        if n_mag > 0 and e > 0:
            cos_w = np.dot(n, e_vec) / (n_mag * e)
            w = math.acos(cos_w)
            if e_vec[2] < 0:
                w = 2 * math.pi - w
        else:
            w = 0
        
        if e > 0:
            cos_nu = np.dot(e_vec, position) / (e * r)
            nu = math.acos(cos_nu)
            if np.dot(position, velocity) < 0:
                nu = 2 * math.pi - nu
        else:
            nu = 0
        
        return OrbitalParameters(float(a), float(e), float(i), float(w), float(omega), float(nu))
    
    @staticmethod
    def calculate_escape_velocity(altitude: float) -> float:
        r = OrbitalMechanics.R_EARTH + altitude
        return math.sqrt(2 * OrbitalMechanics.G * OrbitalMechanics.M_EARTH / r)
    
    @staticmethod
    def calculate_circular_velocity(altitude: float) -> float:
        r = OrbitalMechanics.R_EARTH + altitude
        return math.sqrt(OrbitalMechanics.G * OrbitalMechanics.M_EARTH / r)

class ThermalAnalysis:

    def __init__(self):
        self.material_properties = {
            "aluminum": {"thermal_conductivity": 237, "density": 2700, "specific_heat": 900},
            "steel": {"thermal_conductivity": 50, "density": 7850, "specific_heat": 460},
            "carbon_fiber": {"thermal_conductivity": 8, "density": 1600, "specific_heat": 1000}
        }
    
    def calculate_heat_transfer(self, velocity: float, altitude: float, 
                              material: str = "aluminum", thickness: float = 0.01) -> Dict:

        p0 = 1.225
        h0 = 8500
        density = p0 * math.exp(-altitude / h0)
        
        if velocity > 0:
            h_conv = 0.026 * (velocity ** 0.8) * (density ** 0.2)
            
            q_conv = h_conv * (velocity ** 2) / 2
            
            q_rad = 5.67e-8 * 0.8 * (300 ** 4)
            
            total_heat = q_conv + q_rad
        else:
            total_heat = 0
        
        properties = self.material_properties.get(material, self.material_properties["aluminum"])
        temp_rise = total_heat * thickness / (properties["thermal_conductivity"] * properties["density"] * properties["specific_heat"])
        
        return {
            "convective_heat": q_conv if velocity > 0 else 0,
            "radiative_heat": q_rad if velocity > 0 else 0,
            "total_heat": total_heat,
            "temperature_rise": temp_rise,
            "material": material
        } 