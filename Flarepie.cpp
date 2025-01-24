#include <iostream>
#include <cmath>
using namespace std;

int main() {

    string fuel_type;
    double cocp, nia, ap, ct, pf, w;
    int fuel_code;

    cout << "Welcome to FlarePie! - Open Source Rocket Engine Simulator -\n";

    cout << "Fuel Type: ";
    cin >> fuel_type;

    cout << "Combustion Chamber Pressure: ";
    cin >> cocp;

    cout << "Combustion Temperature: ";
    cin >> ct;

    cout << "Nozzle Inlet Area: ";
    cin >> nia;

    cout << "Atmospheric Pressure: ";
    cin >> ap;

    cout << "Push Force: ";
    cin >> pf;

    cout << "Weight: ";
    cin >> w;

    if (fuel_type == "RP1") fuel_code = 1;
    else if (fuel_type == "LOX") fuel_code = 2;
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
        double R = 259.8;

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
