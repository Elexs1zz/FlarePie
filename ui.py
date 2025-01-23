from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QButtonGroup, QRadioButton, QVBoxLayout, \
    QHBoxLayout, QFormLayout, QPushButton
from PyQt6.QtGui import QFont
import sys


def window():
    app = QApplication(sys.argv)
    win = QWidget()

    font = QFont('Arial', 8)
    win.setFont(font)

    win.setStyleSheet("background-color: #f4f4f9;")

    fbox = QFormLayout()

    fuel_group = QButtonGroup()

    r1 = QRadioButton("Liquid Hydrogen")
    r2 = QRadioButton("RP-1")
    r3 = QRadioButton("Methane")
    r4 = QRadioButton("SRF")
    r5 = QRadioButton("Biofuel")

    fuel_group.addButton(r1)
    fuel_group.addButton(r2)
    fuel_group.addButton(r3)
    fuel_group.addButton(r4)
    fuel_group.addButton(r5)

    hbox_fuel = QHBoxLayout()
    hbox_fuel.addWidget(r1)
    hbox_fuel.addWidget(r2)
    hbox_fuel.addWidget(r3)
    hbox_fuel.addWidget(r4)
    hbox_fuel.addWidget(r5)
    hbox_fuel.addStretch()

    fbox.addRow(QLabel("<b>Fuel Type</b>"), hbox_fuel)

    fuel_ratio = QLineEdit()
    fuel_ratio.setPlaceholderText("Enter Fuel Mixture Ratio")
    fbox.addRow(QLabel("Fuel Mixture Ratio"), fuel_ratio)


    thrust = QLineEdit()
    thrust.setPlaceholderText("Enter Thrust (N)")
    fbox.addRow(QLabel("Thrust (N)"), thrust)

    exhaust_velocity = QLineEdit()
    exhaust_velocity.setPlaceholderText("Enter Exhaust Speed (m/s)")
    fbox.addRow(QLabel("Exhaust Velocity (m/s)"), exhaust_velocity)

    nozzle_diameter = QLineEdit()
    nozzle_diameter.setPlaceholderText("Enter Nozzle Diameter (m)")
    fbox.addRow(QLabel("Nozzle Diameter (m)"), nozzle_diameter)

    nozzle_geometry = QLineEdit()
    nozzle_geometry.setPlaceholderText("Enter Nozzle Geometry")
    fbox.addRow(QLabel("Nozzle Geometry"), nozzle_geometry)

    thrust_to_weight = QLineEdit()
    thrust_to_weight.setPlaceholderText("Enter Thrust/Weight Ratio")
    fbox.addRow(QLabel("Thrust-to-Weight Ratio"), thrust_to_weight)

    specific_impulse = QLineEdit()
    specific_impulse.setPlaceholderText("Enter Specific Impulse (Isp in s)")
    fbox.addRow(QLabel("Specific Impulse (Isp)"), specific_impulse)

    exhaust_temperature = QLineEdit()
    exhaust_temperature.setPlaceholderText("Enter Exhaust Temperature (K)")
    fbox.addRow(QLabel("Exhaust Temperature (K)"), exhaust_temperature)

    engine_weight = QLineEdit()
    engine_weight.setPlaceholderText("Enter Engine Weight (kg)")
    fbox.addRow(QLabel("Engine Weight (kg)"), engine_weight)

    engine_length = QLineEdit()
    engine_length.setPlaceholderText("Enter Engine Length (m)")
    fbox.addRow(QLabel("Engine Length (m)"), engine_length)

    engine_diameter = QLineEdit()
    engine_diameter.setPlaceholderText("Enter Engine Diameter (m)")
    fbox.addRow(QLabel("Engine Diameter (m)"), engine_diameter)

    oxygen_pressure = QLineEdit()
    oxygen_pressure.setPlaceholderText("Enter Oxygen Pressure (Pa)")
    fbox.addRow(QLabel("Oxygen Pressure (Pa)"), oxygen_pressure)

    oxygen_temperature = QLineEdit()
    oxygen_temperature.setPlaceholderText("Enter Oxygen Temperature (K)")
    fbox.addRow(QLabel("Oxygen Temperature (K)"), oxygen_temperature)

    internal_pressure = QLineEdit()
    internal_pressure.setPlaceholderText("Enter Internal Pressure (Pa)")
    fbox.addRow(QLabel("Internal Pressure (Pa)"), internal_pressure)

    fuel_consumption = QLineEdit()
    fuel_consumption.setPlaceholderText("Enter Fuel Consumption Rate (kg/s)")
    fbox.addRow(QLabel("Fuel Consumption Rate (kg/s)"), fuel_consumption)

    fuel_amount = QLineEdit()
    fuel_amount.setPlaceholderText("Enter Total Fuel Amount (kg)")
    fbox.addRow(QLabel("Total Fuel Amount (kg)"), fuel_amount)

    operation_time = QLineEdit()
    operation_time.setPlaceholderText("Enter Operation Time (s)")
    fbox.addRow(QLabel("Operation Time (s)"), operation_time)

    launch_angle = QLineEdit()
    launch_angle.setPlaceholderText("Enter Launch Angle")
    fbox.addRow(QLabel("Launch Angle (°)"), launch_angle)

    launch_height = QLineEdit()
    launch_height.setPlaceholderText("Enter Launch Height (m)")
    fbox.addRow(QLabel("Launch Height (m)"), launch_height)

    wind_speed = QLineEdit()
    wind_speed.setPlaceholderText("Enter Wind Speed (m/s)")
    fbox.addRow(QLabel("Wind Speed (m/s)"), wind_speed)

    calculate_btn = QPushButton("Calculate")
    cancel_btn = QPushButton("Cancel")
    cancel_btn.setStyleSheet("QPushButton { background-color: Red; color: white; font-weight: bold; }")
    calculate_btn.setStyleSheet("QPushButton { background-color: Green; color: white; font-weight: bold; }")

    fbox.addRow(cancel_btn, calculate_btn)

    win.setLayout(fbox)
    win.setGeometry(100, 100, 900, 600)
    win.setWindowTitle("FlarePie - Open Source Rocket Engine Simulator")

    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    window()
