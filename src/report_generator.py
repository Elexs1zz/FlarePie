import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
import base64
from Engine import get_atmospheric_pressure

class ReportGenerator:

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        if 'Title' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Title',
                parent=self.styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.darkblue
            ))
        
        if 'Subtitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Subtitle',
                parent=self.styles['Heading2'],
                fontSize=16,
                spaceAfter=20,
                alignment=TA_CENTER,
                textColor=colors.darkblue
            ))
        
        if 'Section' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Section',
                parent=self.styles['Heading3'],
                fontSize=14,
                spaceAfter=15,
                textColor=colors.darkblue
            ))
        
        if 'Body' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Body',
                parent=self.styles['Normal'],
                fontSize=10,
                spaceAfter=12
            ))
    
    def generate_simulation_report(self, simulation_data: Dict, config: Dict, 
                                 output_path: str = None) -> str:
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"simulation_report_{timestamp}.pdf"
        
        doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=18)
        
        story = []
        
        story.extend(self._create_title_page(simulation_data, config))
        
        story.extend(self._create_executive_summary(simulation_data))
        
        story.extend(self._create_mission_parameters(config))
        
        story.extend(self._create_performance_analysis(simulation_data))
        
        story.extend(self._create_trajectory_analysis(simulation_data))
        
        story.extend(self._create_technical_details(simulation_data))
        
        story.extend(self._create_charts_section(simulation_data))
        
        story.extend(self._create_recommendations(simulation_data))
        
        doc.build(story)
        return output_path
    
    def _create_title_page(self, simulation_data: Dict, config: Dict) -> List:
        elements = []
        
        title = Paragraph("ROCKET SIMULATION REPORT", self.styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 50))
        
        subtitle = Paragraph("Comprehensive Analysis and Performance Evaluation", self.styles['Subtitle'])
        elements.append(subtitle)
        elements.append(Spacer(1, 100))
        
        details_data = [
            ["Report Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["Simulation Duration:", f"{simulation_data.get('final_time', 0):.2f} seconds"],
            ["Maximum Altitude:", f"{max(simulation_data.get('altitude', [0])):.2f} meters"],
            ["Maximum Velocity:", f"{max(simulation_data.get('velocity', [0])):.2f} m/s"],
            ["Fuel Type:", config.get('fuel_type', 'Unknown')],
            ["Total Mass:", f"{config.get('intmass', 0):.2f} kg"]
        ]
        
        details_table = Table(details_data, colWidths=[2*inch, 3*inch])
        details_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(details_table)
        elements.append(Spacer(1, 50))
        
        return elements
    
    def _create_executive_summary(self, simulation_data: Dict) -> List:
        elements = []
        
        # Section title
        title = Paragraph("EXECUTIVE SUMMARY", self.styles['Section'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Key metrics
        max_altitude = max(simulation_data.get('altitude', [0]))
        max_velocity = max(simulation_data.get('velocity', [0]))
        final_time = simulation_data.get('final_time', 0)
        delta_v = simulation_data.get('delta_v', 0)
        
        summary_text = f"""
        This simulation analyzed the performance of a rocket propulsion system over {final_time:.2f} seconds. 
        The mission achieved a maximum altitude of {max_altitude:.2f} meters and a peak velocity of {max_velocity:.2f} m/s, 
        with a total delta-V of {delta_v:.2f} m/s.
        
        Key findings include:
        • Mission duration: {final_time:.2f} seconds
        • Maximum altitude: {max_altitude:.2f} meters
        • Peak velocity: {max_velocity:.2f} m/s
        • Total delta-V: {delta_v:.2f} m/s
        • Propellant efficiency: {self._calculate_efficiency(simulation_data):.2f}%
        """
        
        summary = Paragraph(summary_text, self.styles['Body'])
        elements.append(summary)
        elements.append(Spacer(1, 30))
        
        return elements
    
    def _create_mission_parameters(self, config: Dict) -> List:
        elements = []
        
        title = Paragraph("MISSION PARAMETERS", self.styles['Section'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        params_data = [
            ["Parameter", "Value", "Units"],
            ["Fuel Type", config.get('fuel_type', 'N/A'), ""],
            ["Chamber Pressure", f"{config.get('cocp', 0):.0f}", "Pa"],
            ["Combustion Temperature", f"{config.get('ct', 0):.0f}", "K"],
            ["Initial Altitude", f"{config.get('altitude', 0):.2f}", "m"],
            ["Total Mass", f"{config.get('intmass', 0):.2f}", "kg"],
            ["Propellant Mass", f"{config.get('propmass', 0):.2f}", "kg"],
            ["Mass Flow Rate", f"{config.get('mfr', 0):.2f}", "kg/s"],
            ["Time Step", f"{config.get('dt', 0):.3f}", "s"],
            ["Reference Area", f"{config.get('reference_area', 0):.2f}", "m²"]
        ]
        
        params_table = Table(params_data, colWidths=[2*inch, 2*inch, 1*inch])
        params_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(params_table)
        elements.append(Spacer(1, 30))
        
        return elements
    
    def _create_performance_analysis(self, simulation_data: Dict) -> List:
        elements = []
        
        title = Paragraph("PERFORMANCE ANALYSIS", self.styles['Section'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        max_thrust = max(simulation_data.get('thrust', [0]))
        avg_isp = np.mean(simulation_data.get('isp_values', [0]))
        efficiency = self._calculate_efficiency(simulation_data)
        
        performance_text = f"""
        Performance Analysis Results:
        
        Thrust Performance:
        • Maximum thrust: {max_thrust:.2f} N
        • Average specific impulse: {avg_isp:.2f} s
        • Propellant efficiency: {efficiency:.2f}%
        
        Trajectory Performance:
        • Maximum altitude: {max(simulation_data.get('altitude', [0])):.2f} m
        • Peak velocity: {max(simulation_data.get('velocity', [0])):.2f} m/s
        • Total delta-V: {simulation_data.get('delta_v', 0):.2f} m/s
        
        Mission Efficiency:
        • Thrust-to-weight ratio range: {self._calculate_twr_range(simulation_data):.2f}
        • Average acceleration: {self._calculate_avg_acceleration(simulation_data):.2f} m/s²
        • Mission success probability: {self._calculate_success_probability(simulation_data):.1f}%
        """
        
        performance = Paragraph(performance_text, self.styles['Body'])
        elements.append(performance)
        elements.append(Spacer(1, 30))
        
        return elements
    
    def _create_trajectory_analysis(self, simulation_data: Dict) -> List:
        elements = []
        
        title = Paragraph("TRAJECTORY ANALYSIS", self.styles['Section'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        altitudes = simulation_data.get('altitude', [])
        velocities = simulation_data.get('velocity', [])
        times = simulation_data.get('time', [])
        
        if altitudes and velocities and times:
            max_altitude = max(altitudes)
            max_velocity = max(velocities)
            burn_time = times[-1] if times else 0
            
            max_altitude_time = times[altitudes.index(max_altitude)]
            max_velocity_time = times[velocities.index(max_velocity)]
            
            trajectory_text = f"""
            Trajectory Characteristics:
            
            Flight Profile:
            • Burn duration: {burn_time:.2f} seconds
            • Time to max altitude: {max_altitude_time:.2f} seconds
            • Time to max velocity: {max_velocity_time:.2f} seconds
            
            Trajectory Analysis:
            • Maximum altitude: {max_altitude:.2f} meters
            • Peak velocity: {max_velocity:.2f} m/s
            • Average climb rate: {max_altitude/max_altitude_time if max_altitude_time > 0 else 0:.2f} m/s
            
            Atmospheric Effects:
            • Maximum dynamic pressure: {self._calculate_max_q(simulation_data):.2f} Pa
            • Maximum Mach number: {self._calculate_max_mach(simulation_data):.2f}
            • Maximum drag force: {max(simulation_data.get('drag', [0])):.2f} N
            """
            
            trajectory = Paragraph(trajectory_text, self.styles['Body'])
            elements.append(trajectory)
        
        elements.append(Spacer(1, 30))
        return elements
    
    def _create_technical_details(self, simulation_data: Dict) -> List:
        """Create technical details section"""
        elements = []
        
        title = Paragraph("TECHNICAL DETAILS", self.styles['Section'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        technical_text = f"""
        Technical Analysis:
        
        Propulsion System:
        • Total impulse: {self._calculate_total_impulse(simulation_data):.2f} N·s
        • Average thrust: {np.mean(simulation_data.get('thrust', [0])):.2f} N
        • Thrust coefficient: {self._calculate_thrust_coefficient(simulation_data):.3f}
        
        Aerodynamics:
        • Maximum drag coefficient: {self._calculate_max_cd(simulation_data):.3f}
        • Average drag coefficient: {np.mean(simulation_data.get('drag', [0]))/max(simulation_data.get('velocity', [1]))**2:.3f}
        • Reynolds number range: {self._calculate_reynolds_range(simulation_data):.0f}
        
        Thermal Analysis:
        • Maximum heat flux: {self._calculate_max_heat_flux(simulation_data):.2f} W/m²
        • Average temperature rise: {self._calculate_avg_temp_rise(simulation_data):.2f} K
        • Thermal efficiency: {self._calculate_thermal_efficiency(simulation_data):.2f}%
        """
        
        technical = Paragraph(technical_text, self.styles['Body'])
        elements.append(technical)
        elements.append(Spacer(1, 30))
        
        return elements
    
    def _create_charts_section(self, simulation_data: Dict) -> List:
        elements = []
        
        title = Paragraph("CHARTS AND GRAPHS", self.styles['Section'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Create and save charts
        charts = self._generate_charts(simulation_data)
        
        for chart_path in charts:
            if os.path.exists(chart_path):
                img = Image(chart_path, width=6*inch, height=4*inch)
                elements.append(img)
                elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_recommendations(self, simulation_data: Dict) -> List:
        elements = []
        
        title = Paragraph("RECOMMENDATIONS", self.styles['Section'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        recommendations = self._generate_recommendations(simulation_data)
        
        for rec in recommendations:
            rec_para = Paragraph(f"• {rec}", self.styles['Body'])
            elements.append(rec_para)
            elements.append(Spacer(1, 10))
        
        elements.append(Spacer(1, 30))
        return elements
    
    def _generate_charts(self, simulation_data: Dict) -> List[str]:
        charts = []
        
        plt.style.use('dark_background')
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        times = simulation_data.get('time', [])
        altitudes = simulation_data.get('altitude', [])
        velocities = simulation_data.get('velocity', [])
        
        if times and altitudes and velocities:
            ax1.plot(times, altitudes, 'b-', linewidth=2, label='Altitude')
            ax1.set_ylabel('Altitude (m)')
            ax1.set_title('Flight Trajectory')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            ax2.plot(times, velocities, 'r-', linewidth=2, label='Velocity')
            ax2.set_xlabel('Time (s)')
            ax2.set_ylabel('Velocity (m/s)')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
        
        plt.tight_layout()
        chart_path = "trajectory_chart.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        charts.append(chart_path)
        plt.close()
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        
        thrusts = simulation_data.get('thrust', [])
        isp_values = simulation_data.get('isp_values', [])
        fuel_remaining = simulation_data.get('fuel_remaining', [])
        
        if times and thrusts:
            ax1.plot(times, thrusts, 'g-', linewidth=2)
            ax1.set_ylabel('Thrust (N)')
            ax1.set_title('Thrust Profile')
            ax1.grid(True, alpha=0.3)
        
        if times and isp_values:
            ax2.plot(times, isp_values, 'y-', linewidth=2)
            ax2.set_ylabel('Specific Impulse (s)')
            ax2.set_title('ISP Profile')
            ax2.grid(True, alpha=0.3)
        
        if times and fuel_remaining:
            ax3.plot(times, fuel_remaining, 'm-', linewidth=2)
            ax3.set_xlabel('Time (s)')
            ax3.set_ylabel('Fuel Remaining (kg)')
            ax3.set_title('Fuel Consumption')
            ax3.grid(True, alpha=0.3)
        
        # TWR plot
        if times and thrusts and fuel_remaining:
            twr_values = []
            for i, thrust in enumerate(thrusts):
                if i < len(fuel_remaining):
                    mass = simulation_data.get('intmass', 0) - simulation_data.get('propmass', 0) + fuel_remaining[i]
                    weight = mass * 9.81
                    twr = thrust / weight if weight > 0 else 0
                    twr_values.append(twr)
            
            ax4.plot(times[:len(twr_values)], twr_values, 'c-', linewidth=2)
            ax4.set_xlabel('Time (s)')
            ax4.set_ylabel('Thrust/Weight Ratio')
            ax4.set_title('TWR Profile')
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        chart_path = "performance_chart.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        charts.append(chart_path)
        plt.close()
        
        return charts
    
    def _generate_recommendations(self, simulation_data: Dict) -> List[str]:
        recommendations = []
        
        max_altitude = max(simulation_data.get('altitude', [0]))
        max_velocity = max(simulation_data.get('velocity', [0]))
        efficiency = self._calculate_efficiency(simulation_data)
        
        if efficiency < 80:
            recommendations.append("Consider optimizing propellant mixture ratio for better efficiency")
        
        if max_altitude < 10000:
            recommendations.append("Increase propellant mass or optimize trajectory for higher altitude")
        
        if max_velocity < 1000:
            recommendations.append("Consider higher thrust or longer burn time for increased velocity")
        
        twr_range = self._calculate_twr_range(simulation_data)
        if twr_range < 1.5:
            recommendations.append("Increase thrust-to-weight ratio for better performance")
        
        recommendations.append("Implement real-time monitoring systems for mission control")
        recommendations.append("Consider multi-stage configuration for orbital missions")
        recommendations.append("Add thermal protection systems for high-speed flight")
        
        return recommendations
    
    def _calculate_efficiency(self, simulation_data: Dict) -> float:
        fuel_remaining = simulation_data.get('fuel_remaining', [])
        if not fuel_remaining:
            return 0.0
        
        initial_fuel = fuel_remaining[0]
        final_fuel = fuel_remaining[-1]
        if initial_fuel > 0:
            return ((initial_fuel - final_fuel) / initial_fuel) * 100
        return 0.0
    
    def _calculate_twr_range(self, simulation_data: Dict) -> float:
        thrusts = simulation_data.get('thrust', [])
        fuel_remaining = simulation_data.get('fuel_remaining', [])
        
        if not thrusts or not fuel_remaining:
            return 0.0
        
        twr_values = []
        for i, thrust in enumerate(thrusts):
            if i < len(fuel_remaining):
                mass = simulation_data.get('intmass', 0) - simulation_data.get('propmass', 0) + fuel_remaining[i]
                weight = mass * 9.81
                twr = thrust / weight if weight > 0 else 0
                twr_values.append(twr)
        
        return max(twr_values) - min(twr_values) if twr_values else 0.0
    
    def _calculate_avg_acceleration(self, simulation_data: Dict) -> float:
        velocities = simulation_data.get('velocity', [])
        times = simulation_data.get('time', [])
        
        if len(velocities) < 2 or len(times) < 2:
            return 0.0
        
        total_acc = 0
        count = 0
        for i in range(1, len(velocities)):
            dt = times[i] - times[i-1]
            if dt > 0:
                acc = (velocities[i] - velocities[i-1]) / dt
                total_acc += acc
                count += 1
        
        return total_acc / count if count > 0 else 0.0
    
    def _calculate_success_probability(self, simulation_data: Dict) -> float:
        max_altitude = max(simulation_data.get('altitude', [0]))
        max_velocity = max(simulation_data.get('velocity', [0]))
        efficiency = self._calculate_efficiency(simulation_data)
        
        # Scoring system
        altitude_score = min(max_altitude / 10000, 1.0) * 30
        velocity_score = min(max_velocity / 1000, 1.0) * 30
        efficiency_score = min(efficiency / 100, 1.0) * 40
        
        return altitude_score + velocity_score + efficiency_score
    
    def _calculate_max_q(self, simulation_data: Dict) -> float:
        velocities = simulation_data.get('velocity', [])
        altitudes = simulation_data.get('altitude', [])
        
        if not velocities or not altitudes:
            return 0.0
        
        max_q = 0
        for v, h in zip(velocities, altitudes):
            # Simplified atmospheric density
            density = 1.225 * np.exp(-h / 8500)
            q = 0.5 * density * v**2
            max_q = max(max_q, q)
        
        return max_q
    
    def _calculate_max_mach(self, simulation_data: Dict) -> float:
        velocities = simulation_data.get('velocity', [])
        altitudes = simulation_data.get('altitude', [])
        
        if not velocities or not altitudes:
            return 0.0
        
        max_mach = 0
        for v, h in zip(velocities, altitudes):
            # Speed of sound at altitude
            speed_of_sound = 340 * np.sqrt(get_atmospheric_pressure(h) / 101325)
            mach = v / speed_of_sound if speed_of_sound > 0 else 0
            max_mach = max(max_mach, mach)
        
        return max_mach
    
    def _calculate_total_impulse(self, simulation_data: Dict) -> float:
        thrusts = simulation_data.get('thrust', [])
        times = simulation_data.get('time', [])
        
        if not thrusts or not times:
            return 0.0
        
        total_impulse = 0
        for i in range(1, len(thrusts)):
            dt = times[i] - times[i-1]
            avg_thrust = (thrusts[i] + thrusts[i-1]) / 2
            total_impulse += avg_thrust * dt
        
        return total_impulse
    
    def _calculate_thrust_coefficient(self, simulation_data: Dict) -> float:
        thrusts = simulation_data.get('thrust', [])
        if not thrusts:
            return 0.0
        
        return np.mean(thrusts) / max(thrusts) if max(thrusts) > 0 else 0.0
    
    def _calculate_max_cd(self, simulation_data: Dict) -> float:
        drags = simulation_data.get('drag', [])
        velocities = simulation_data.get('velocity', [])
        altitudes = simulation_data.get('altitude', [])
        
        if not drags or not velocities or not altitudes:
            return 0.0
        
        max_cd = 0
        for drag, v, h in zip(drags, velocities, altitudes):
            if v > 0:
                density = 1.225 * np.exp(-h / 8500)
                cd = drag / (0.5 * density * v**2 * 1.0)  # Assuming reference area of 1.0
                max_cd = max(max_cd, cd)
        
        return max_cd
    
    def _calculate_reynolds_range(self, simulation_data: Dict) -> float:
        velocities = simulation_data.get('velocity', [])
        altitudes = simulation_data.get('altitude', [])
        
        if not velocities or not altitudes:
            return 0.0
        
        reynolds_values = []
        for v, h in zip(velocities, altitudes):
            density = 1.225 * np.exp(-h / 8500)
            viscosity = 1.8e-5 * (288.15 / (288.15 - 0.0065 * h))**0.5
            reynolds = density * v * 1.0 / viscosity
            reynolds_values.append(reynolds)
        
        return max(reynolds_values) - min(reynolds_values) if reynolds_values else 0.0
    
    def _calculate_max_heat_flux(self, simulation_data: Dict) -> float:
        velocities = simulation_data.get('velocity', [])
        altitudes = simulation_data.get('altitude', [])
        
        if not velocities or not altitudes:
            return 0.0
        
        max_heat_flux = 0
        for v, h in zip(velocities, altitudes):
            if v > 0:
                density = 1.225 * np.exp(-h / 8500)
                heat_flux = 0.026 * (v**0.8) * (density**0.2) * (v**2) / 2
                max_heat_flux = max(max_heat_flux, heat_flux)
        
        return max_heat_flux
    
    def _calculate_avg_temp_rise(self, simulation_data: Dict) -> float:
        velocities = simulation_data.get('velocity', [])
        altitudes = simulation_data.get('altitude', [])
        
        if not velocities or not altitudes:
            return 0.0
        
        temp_rises = []
        for v, h in zip(velocities, altitudes):
            if v > 0:
                density = 1.225 * np.exp(-h / 8500)
                heat_flux = 0.026 * (v**0.8) * (density**0.2) * (v**2) / 2
                temp_rise = heat_flux * 0.01 / (237 * 2700 * 900)  # Aluminum properties
                temp_rises.append(temp_rise)
        
        return np.mean(temp_rises) if temp_rises else 0.0
    
    def _calculate_thermal_efficiency(self, simulation_data: Dict) -> float:
        max_heat_flux = self._calculate_max_heat_flux(simulation_data)
        max_thrust = max(simulation_data.get('thrust', [0]))
        
        if max_thrust > 0:
            return max(0, 100 - (max_heat_flux / max_thrust) * 1000)
        return 0.0 
