#include <iostream>
#include <cmath>
using namespace std;

int main() {
    string fuel_type;
    double cocp, ct, ap, ve, mfr, thr, expa, amp, ea, si, f;
    int fuel_code, inp;

    cout << "Welcome to FlarePie! - Open Source Rocket Engine Simulator -\n";

    cout << "For Rocket Engine Simulator, type 1. For Nozzle Performance Calculator, type 2.\n";
    cin >> inp;

    if (inp == 1) {
        cout << "Fuel Type (RP1, LH2, SRF): ";
        cin >> fuel_type;

        cout << "Combustion Chamber Pressure (Pa): ";
        cin >> cocp;

        cout << "Combustion Temperature (K): ";
        cin >> ct;

        cout << "Atmospheric Pressure (Pa): ";
        cin >> ap;

        if (fuel_type == "RP1") fuel_code = 1;
        else if (fuel_type == "LH2") fuel_code = 2;
        else if (fuel_type == "SRF") fuel_code = 3;
        else fuel_code = 0;

        switch (fuel_code) {
        case 1: {
            double k = 1.2;
            double R = 287.0;
            ve = sqrt((2 * k) / (k - 1) * R * ct * (1 - pow((ap / cocp), (k - 1) / k)));
            cout << "Nozzle Outlet Velocity for RP1 (ve): " << ve << " m/s" << endl;
            break;
        }
        case 2: {
            double k = 1.4;
            double R = 4124.0;
            ve = sqrt((2 * k) / (k - 1) * R * ct * (1 - pow((ap / cocp), (k - 1) / k)));
            cout << "Nozzle Outlet Velocity for LH2 (ve): " << ve << " m/s" << endl;
            break;
        }
        case 3: {
            double k = 1.2;
            double R = 191.0;
            ve = sqrt((2 * k) / (k - 1) * R * ct * (1 - pow((ap / cocp), (k - 1) / k)));
            cout << "Nozzle Outlet Velocity for Sugar Rocket (ve): " << ve << " m/s" << endl;
            break;
        }
        default:
            cout << "Invalid fuel type" << endl;
            break;
        }
    }

    if (inp == 2) {
        cout << "Mass Flow Rate (Kg/s): ";
        cin >> mfr;

        cout << "Exhaust Velocity (m/s): ";
        cin >> ve;

        cout << "Exit Pressure (Pa): ";
        cin >> expa;

        cout << "Ambient Pressure (Pa): ";
        cin >> amp;

        cout << "Exit Area (m^2): ";
        cin >> ea;

        f = (mfr * ve) + ((expa - amp) * ea);
        cout << "Thrust (F): " << f << " N" << endl;

        si = f / (mfr * 9.81);
        cout << "Specific Impulse (Isp): " << si << " s" << endl;
    }

    return 0;
}
