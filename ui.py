from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QButtonGroup, QRadioButton, QVBoxLayout,
                             QHBoxLayout, QFormLayout, QPushButton, QGridLayout, QFrame, QTextEdit)
from PyQt6.QtGui import QFont
import sys

def window():
    app = QApplication(sys.argv)
    win = QWidget()

    font = QFont('Arial', 8)
    win.setFont(font)

    win.setStyleSheet("background-color: #f4f4f9;")

    main_layout = QHBoxLayout()

    # Left Section: Input Fields
    input_layout = QFormLayout()

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

    input_layout.addRow(QLabel("<b>Fuel Type</b>"), hbox_fuel)

    fields = [
        ("Fuel Mixture Ratio", "Enter Fuel Mixture Ratio"),
        ("Thrust (N)", "Enter Thrust (N)"),
        ("Exhaust Velocity (m/s)", "Enter Exhaust Speed (m/s)"),
        ("Nozzle Diameter (m)", "Enter Nozzle Diameter (m)"),
        ("Nozzle Geometry", "Enter Nozzle Geometry"),
        ("Thrust-to-Weight Ratio", "Enter Thrust/Weight Ratio"),
        ("Specific Impulse (Isp)", "Enter Specific Impulse (Isp in s)"),
        ("Exhaust Temperature (K)", "Enter Exhaust Temperature (K)"),
        ("Engine Weight (kg)", "Enter Engine Weight (kg)"),
        ("Engine Length (m)", "Enter Engine Length (m)"),
        ("Engine Diameter (m)", "Enter Engine Diameter (m)"),
        ("Oxygen Pressure (Pa)", "Enter Oxygen Pressure (Pa)"),
        ("Oxygen Temperature (K)", "Enter Oxygen Temperature (K)"),
        ("Internal Pressure (Pa)", "Enter Internal Pressure (Pa)"),
        ("Fuel Consumption Rate (kg/s)", "Enter Fuel Consumption Rate (kg/s)"),
        ("Total Fuel Amount (kg)", "Enter Total Fuel Amount (kg)"),
        ("Operation Time (s)", "Enter Operation Time (s)"),
        ("Launch Angle (°)", "Enter Launch Angle"),
        ("Launch Height (m)", "Enter Launch Height (m)"),
        ("Wind Speed (m/s)", "Enter Wind Speed (m/s)")
    ]

    for label, placeholder in fields:
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        input_layout.addRow(QLabel(label), line_edit)

    calculate_btn = QPushButton("Calculate")
    cancel_btn = QPushButton("Cancel")
    cancel_btn.setStyleSheet("QPushButton { background-color: Red; color: white; font-weight: bold; }")
    calculate_btn.setStyleSheet("QPushButton { background-color: Green; color: white; font-weight: bold; }")

    input_layout.addRow(cancel_btn, calculate_btn)

    # Right Section: Graph and Results
    right_layout = QVBoxLayout()

    graph_frame = QFrame()
    graph_frame.setStyleSheet("background-color: white; border: 1px solid black;")
    graph_frame.setMinimumSize(400, 300)

    results_text = QTextEdit()
    results_text.setPlaceholderText("Results will be displayed here...")
    results_text.setReadOnly(True)

    right_layout.addWidget(QLabel("<b>Graph</b>"))
    right_layout.addWidget(graph_frame)
    right_layout.addWidget(QLabel("<b>Results</b>"))
    right_layout.addWidget(results_text)

    # Add layouts to main layout
    main_layout.addLayout(input_layout, 2)
    main_layout.addLayout(right_layout, 3)

    win.setLayout(main_layout)
    win.setGeometry(100, 100, 1000, 600)
    win.setWindowTitle("FlarePie - Open Source Rocket Engine Simulator")

    win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    window()
