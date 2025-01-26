#include <iostream>
#include <cmath>
using namespace std;

int main() {

    string fuel_type;
    double cocp, nia, ap, ct, pf, w, csi,ve;
    int fuel_code;

    cout << "Welcome to FlarePie! - Open Source Rocket Engine Simulator -\n";

    cout << "Fuel Type: ";
    cin >> fuel_type;

    cout << "Combustion Chamber Pressure (Pa): ";
    cin >> cocp;

    cout << "Combustion Temperature (K): ";
    cin >> ct;

    cout << "Nozzle Inlet Area (m^2): ";
    cin >> nia;

    cout << "Atmospheric Pressure (Pa) : ";
    cin >> ap;

    cout << "Push Force (N) : ";
    cin >> pf;

    cout << "Weight (Kg) : ";
    cin >> w;

    if (fuel_type == "RP1") fuel_code = 1;
    else if (fuel_type == "LH2") fuel_code = 2;
    else if (fuel_type == "SRF") fuel_code = 3;
    else fuel_code = 0;

    switch (fuel_code) {
    case 1: {
        double k = 1.2;
        double R = 287.0;

        double ve = sqrt((2 * k) / (k - 1) * R * ct * (1 - pow((ap / cocp), (k - 1) / k)));
        cout << "Nozzle Outlet Velocity for RP1 (ve): " << ve << " m/s" << endl;
        
        break;
    }
    case 2: {
        double k = 1.4; 
        double R = 4124.0; 
        
        double ve = sqrt((2 * k) / (k - 1) * R * ct * (1 - pow((ap / cocp), (k - 1) / k)));
        cout << "Nozzle Outlet Velocity for LOX (ve): " << ve << " m/s" << endl;
        break;
    }
    case 3: {
        double k = 1.2;
        double R = 191.0;

        double ve = sqrt((2 * k) / (k - 1) * R * ct * (1 - pow((ap / cocp), (k - 1) / k)));
        cout << "Nozzle Outlet Velocity for Sugar Rocket (ve): " << ve << " m/s" << endl;
        break;
    }
    default:
        cout << "Invalid fuel type" << endl;
        break;
    }

    return 0;
}