# Defines functions for project
# Cole Jansma, Vinh Le, Noah Tarver, Bennet Kruse, Connor Schultz, Matthew Spalla
# 11/12/2026

import numpy as np
import openpyxl as xl
from numpy.polynomial import Polynomial as poly
from matplotlib import pyplot as plt

def data_function(workbook_data, car_selection, spacer):

    data_sheet = workbook_data["Car{}".format(car_selection)]

    print(spacer)
    print("\t\t    Checking Original Data")
    print(spacer)

    car = data_sheet["A1"].value

    gear_ratios_labels = []
    gear_ratios = []
    parameters_symbols = []
    parameters = []
    exp_omega_es = []
    exp_torque_es = []
    max_omega_e = []
    max_omega_e_label = []

    for i in range(4,10): # pulls gear ratios and labels from sheet
        gear_ratio_label = data_sheet["A{}".format(i)].value
        gear_ratio = data_sheet["B{}".format(i)].value

        while gear_ratio != np.abs(gear_ratio): # verifies gear ratios are not negative
            gear_ratio = float(input("{} is negative. Please insert it again: ".format(gear_ratio_label)))

        data_sheet["B{}".format(i)] = gear_ratio # overwrites negative data with positive input
        
        gear_ratios_labels.append(gear_ratio_label)
        gear_ratios.append(gear_ratio)


    for i in range(12,26): # pulls parameters from sheet
        parameter_symbol = data_sheet["B{}".format(i)].value
        parameter = data_sheet["C{}".format(i)].value

        while parameter != np.abs(parameter): # verifies parameters are not negative
            parameter = float(input("{} is negative. Please insert it again: ".format(parameter_symbol)))

        data_sheet["C{}".format(i)] = parameter # overwrites negative data with positive input

        parameters_symbols.append(parameter_symbol)
        parameters.append(parameter)

    for i in range(4,19): # pulls dyno data from sheet
        exp_omega_e = data_sheet["F{}".format(i)].value
        exp_torque_e = data_sheet["G{}".format(i)].value

        exp_omega_es.append(exp_omega_e)
        exp_torque_es.append(exp_torque_e)

    # pulls max rpm and label from sheet
    max_omega_e_label.append(data_sheet["F21"].value)
    max_omega_e.append(data_sheet["G21"].value)

    workbook_data.save("project_data.xlsx")

    print("All data is positive.")

    return  car, gear_ratios_labels, gear_ratios, parameters_symbols, parameters, exp_omega_es, exp_torque_es, max_omega_e, max_omega_e_label

def calculation_function(gear_ratios,parameters,exp_omega_es, exp_torque_es, max_omega_e):

    # Assigns names to parameters to aid in calculation
    car_velocity_ms = parameters[0] * 1000 / 3600 # converts km/hr to m/s
    terrain_angle_rad = np.atan(parameters[1] / 100) # converts from grade to rad
    wheelbase = parameters[2]
    wheel_radius = parameters[3]
    roll_resistance_coeff = parameters[4] 
    CoG_height = parameters[5]
    final_drive_eff = parameters[6] / 100 # converts out of percent and into decimal
    transmission_eff = parameters[7] / 100 # converts out of percent and into decimal
    car_weight = parameters[8]
    air_density = parameters[9]
    final_drive_ratio = parameters[10]
    front_wheel_CoG_distance = parameters[11]
    drag_coeff = parameters[12]
    frontal_area = parameters[13]

    rear_wheel_CoG_distance = wheelbase - front_wheel_CoG_distance

    torque_rpm_curve_fit = poly.fit(exp_omega_es,exp_torque_es,4) # fits a quartic curve to the rpm-torque data

    omega_w = (car_velocity_ms / wheel_radius) * (60/(2*np.pi)) # rpm at wheels
    omega_t = final_drive_ratio * omega_w # rpm at transmission

    omega_es = [] # rpm at engine for each gear
    rs = [] # R
    torque_e_nms = [] # torque at engine for each gear
    powers = [] # power at engine for each gear
    torque_ts = [] # torque at transmission for each gear
    torque_ds = [] # torque at differential for each gear
    ps = [] # P for each gear
    accelerations = [] # a for each gear
    wfs = [] # dynamic front axle load for each gear
    wrs = [] # dynamic rear axle load for each gear
    wf_stats = [] # static front axle load for each gear
    wr_stats = [] # static front axle load for each gear

    g = 9.8

    for i in range(0,6):
        
        omega_e = gear_ratios[i] * omega_t

        if omega_e > max_omega_e[0]:
            omega_e = "OOR"
            omega_es.append(omega_e)

            r = "OOR"
            rs.append(r)

            power = "OOR"
            powers.append(power)

            torque_e_nm = "OOR"
            torque_e_nms.append(torque_e_nm)
            
            torque_t = "OOR"
            torque_ts.append(torque_t)

            torque_d = "OOR"
            torque_ds.append(torque_d)

            p = "OOR"
            ps.append(p)

            acceleration = "OOR"
            accelerations.append(acceleration)
            
            wf_stat = "OOR"
            wf_stats.append(wf_stat)

            wr_stat = "OOR"
            wr_stats.append(wr_stat)

            wf = "OOR"
            wfs.append(wf)

            wr = "OOR"
            wrs.append(wr)
        else:
            r_rolling = roll_resistance_coeff * car_weight * np.cos(terrain_angle_rad) # rolling resistance
            grade_load = car_weight * np.sin(terrain_angle_rad) # grade load
            r_air = 0.5 * air_density * drag_coeff * frontal_area * car_velocity_ms**2 # air drag

            r = r_rolling + grade_load + r_air
            rs.append(r)

            omega_es.append(omega_e)

            torque_e_nm = torque_rpm_curve_fit(omega_e)
            torque_e_nms.append(torque_e_nm)
            
            torque_e_ftlb = torque_e_nm * 0.737562149277

            power = (omega_e * torque_e_ftlb) / 5252.113
            powers.append(power)

            torque_t = transmission_eff * gear_ratios[i] * torque_e_nm
            torque_ts.append(torque_t)

            torque_d = final_drive_eff * final_drive_ratio * torque_t
            torque_ds.append(torque_d)

            p = torque_d / wheel_radius
            ps.append(p)

            acceleration = (g / car_weight) * (p - r)
            accelerations.append(acceleration)

            wf = ((car_weight * rear_wheel_CoG_distance * np.cos(terrain_angle_rad)) - (car_weight * CoG_height * np.sin(terrain_angle_rad)) - ((car_weight / g) * acceleration * CoG_height) - (r_air * CoG_height)) / wheelbase
            wfs.append(wf)

            wr = car_weight * np.cos(terrain_angle_rad) - wf
            wrs.append(wr)

            wf_stat = car_weight * (rear_wheel_CoG_distance / wheelbase)
            wf_stats.append(wf_stat)

            wr_stat = car_weight * (front_wheel_CoG_distance / wheelbase)
            wr_stats.append(wr_stat)

    return rs, omega_es, torque_e_nms, powers, ps, accelerations, wfs, wrs, wf_stats, wr_stats, torque_rpm_curve_fit, g

def output_function(workbook_results, counter, car, gear_ratios_labels, gear_ratios, rs, omega_es, torque_e_Nms, powers, ps, accelerations, wfs, wrs, wf_stats, wr_stats, parameters_symbols, parameters, max_omega_e):

    results_sheet = workbook_results.create_sheet("Results{}".format(counter))

    columns = ["B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M"]
    results_labels = ["Gear", "Ratio", "WR(N)", "WF(N)", "WRstat(N)", "WFstat(N)", "a(m/s2)", "P(N)", "R(N)", "HP(hp)", "Te(Nm)", "omega_e(RPM)"]
    results = [gear_ratios_labels, gear_ratios, wrs, wfs, wr_stats, wf_stats, accelerations, ps, rs, powers, torque_e_Nms, omega_es]

    results_sheet["B1"] = "Results for:"
    results_sheet["D1"] = car

    for i in range(0,12):
        results_sheet["{}3".format(columns[i])] = results_labels[i]

        for k in range(0,6):
            results_sheet["{}{}".format(columns[i],4+k)] = results[i][k]

    results_sheet["B11"] = "Data:"

    for i in range(0,14):
        results_sheet["C{}".format(12+i)] = parameters_symbols[i]
        results_sheet["B{}".format(12+i)] = parameters[i]

    results_sheet["B25"] = "Max Omega"
    results_sheet["C25"] = max_omega_e[0]
    
    workbook_results.save("project_results.xlsx")

def plotting_function(car, counter, parameters, gear_ratios_labels, gear_ratios, torque_rpm_curve_fit, max_omega_e, g):

    # data used for calculations
    car_velocity_ms = parameters[0] * 1000 / 3600 # converts km/hr to m/s
    terrain_angle_rad = np.atan(parameters[1]/100)
    wheel_radius = parameters[3]
    roll_resistance_coeff = parameters[4]
    final_drive_eff = parameters[6]/100
    transmission_eff = parameters[7]/100
    car_weight = parameters[8]
    air_density = parameters[9]
    final_drive_ratio = parameters[10]
    drag_coeff = parameters[12]
    frontal_area = parameters[13]

    car_figure= plt.figure(counter)

    # traction vs speed  

    valid_ps = [] # only ps that come from rpms less than max
    valid_speeds_1 = [] # 1 is used to distinguish from 1st subplot

    car_velocity_kmh_array = np.linspace(0,200,500) # used for x axis 
    car_velocity_ms_array = car_velocity_kmh_array * 1000 / 3600 # used for calculation

    for i in range(0,6): # loops through each gear

        valid_ps = []
        valid_speeds_1 = [] # 1 is used to distinguish from 1st subplot

        car_velocity_kmh_array = np.linspace(5,200,500)
        car_velocity_ms_array = car_velocity_kmh_array * (1000/3600)
        
        for velocity in car_velocity_ms_array: 
            omega_w = (velocity / wheel_radius) * (60/(2*np.pi)) # rpm at wheels
            omega_t = final_drive_ratio * omega_w # rpm at transmission
            omega_e = gear_ratios[i] * omega_t # rpm at engine

            if omega_e <= max_omega_e[0]:
                torque_e_nm = torque_rpm_curve_fit(omega_e)
                torque_t = transmission_eff * gear_ratios[i] * torque_e_nm
                torque_d = final_drive_eff * final_drive_ratio * torque_t
                
                p = torque_d / wheel_radius
                valid_ps.append(p)

                valid_speeds_1.append(velocity * 3.6) # converts to km/h

        plt.subplot(2,2,1)
        plt.plot(valid_speeds_1, valid_ps, label = gear_ratios_labels[i])

    plt.title("Traction vs Speed")
    plt.xlabel("Car Velocity (km/h)")
    plt.ylabel("Traction (N)")
    plt.xlim(0)
    plt.ylim(0)
    plt.legend()

    # weight vs acceleration

    car_weight_array = np.linspace(car_weight-2000,car_weight+4500)
   
    for i in range(0,6):
        omega_w = (car_velocity_ms / wheel_radius) * (60/(2*np.pi)) # rpm at wheels
        omega_t = final_drive_ratio * omega_w # rpm at transmission
        omega_e = gear_ratios[i] * omega_t # rpm at engine
        
        if omega_e <= max_omega_e[0]: # only plots if rpms less than max rpm
            torque_e_nm = torque_rpm_curve_fit(omega_e)
            torque_t = transmission_eff * gear_ratios[i] * torque_e_nm
            torque_d = final_drive_eff * final_drive_ratio * torque_t
            p = torque_d / wheel_radius
            
            r_rolling = roll_resistance_coeff *  car_weight_array * np.cos(terrain_angle_rad)
            grade_load = car_weight_array * np.sin(terrain_angle_rad)
            r_air = 0.5 * air_density * drag_coeff * frontal_area * car_velocity_ms**2

            r = r_rolling + grade_load + r_air

            acceleration = (g / car_weight_array) * (p - r)

            plt.subplot(2,2,2)
            plt.plot(car_weight_array, acceleration, label = gear_ratios_labels[i])
        
    plt.title("Car Weight vs Acceleration")
    plt.xlabel("Car Weight (N)")
    plt.ylabel("Acceleration (m/s^2)")
    plt.legend()

    # speed vs acceleration

    for i in range(0,6): # loops through each gear

        valid_accelerations = []
        valid_speeds_2 = [] # 2 is used to distinguish from 1st subplot

        car_velocity_kmh_array = np.linspace(50,200,500) # Reassigns car velocity array to a more reasonable range for this plot
        car_velocity_ms_array = car_velocity_kmh_array * (1000/3600)
        
        for velocity in car_velocity_ms_array: 
            omega_w = (velocity / wheel_radius) * (60/(2*np.pi)) # rpm at wheels
            omega_t = final_drive_ratio * omega_w # rpm at transmission
            omega_e = gear_ratios[i] * omega_t # rpm at engine

            if omega_e <= max_omega_e[0]:
                torque_e_nm = torque_rpm_curve_fit(omega_e)
                torque_t = transmission_eff * gear_ratios[i] * torque_e_nm
                torque_d = final_drive_eff * final_drive_ratio * torque_t
                p = torque_d / wheel_radius

                r_rolling = roll_resistance_coeff *  car_weight * np.cos(terrain_angle_rad)
                grade_load = car_weight * np.sin(terrain_angle_rad)
                r_air = 0.5 * air_density * drag_coeff * frontal_area * velocity**2

                r = r_rolling + grade_load + r_air

                acceleration = (g / car_weight) * (p - r)
                valid_accelerations.append(acceleration)

                valid_speeds_2.append(velocity * 3.6) # converts to km/h

        plt.subplot(2,2,3)
        plt.plot(valid_speeds_2, valid_accelerations, label = gear_ratios_labels[i])
    
    plt.title("Speed vs Acceleration")
    plt.xlabel("Car Velocity (km/h)")
    plt.ylabel("Acceleration (m/s^2)")
    plt.legend()

    # rpm vs power 

    rpm_array = np.linspace(1000,max_omega_e[0],500)

    torque_e_nm_array = torque_rpm_curve_fit(rpm_array)
    torque_e_ftlb_array = torque_e_nm_array * 0.737562149277
    power_array = (rpm_array * torque_e_ftlb_array) / 5252.113

    plt.subplot(2,2,4)
    plt.plot(rpm_array, torque_e_ftlb_array, "r")
    plt.plot(rpm_array, power_array, "b")

    plt.title("RPM vs Torque and Power")
    plt.xlabel("RPM")
    plt.ylabel("Torque (Nm) and Power (hp)")
    plt.legend(["Torque", "Power"])

    plt.suptitle(car)
    plt.tight_layout()
    plt.show()
    car_figure.savefig("{} figure.png".format(car), dpi = 600)