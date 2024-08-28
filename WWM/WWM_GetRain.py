import os
import statistics
import math
import numpy as np

def getRainfallByAEP(AEP, M_location, B_scale):
    K = -math.log(-math.log(1-float(AEP)))
    Total_rain = M_location + B_scale * K

    return Total_rain

# step 1 get total rainfall, then get rainfall boundary (rainfall_profile * total rainfall) and inflow boundary (getFlowFromDescriptors)
def calculateTotalRainfall(AEP, AMAX_series):


    AMAX_series.sort() # to ensure they are ranked
    N_AMAX_count = len(AMAX_series)
    Xbar = sum(AMAX_series) / N_AMAX_count
    S = statistics.stdev(AMAX_series)

    M_location = Xbar - 0.45005 * S
    B_scale =0.7797 * S

    rain_out = getRainfallByAEP(AEP, M_location, B_scale)

    return rain_out

# a = calculateTotalRainfall(0.1, [121,104,102,100,97,96,94,92,89,87,87,82,77,72,67,56] )




def desc_slope(pnt1_height_m, pnt2_height_m, longest_path_length_in_m):
    # Slope calculation for Kirpich
    height_differnce = (pnt2_height_m - pnt1_height_m)
    slope = height_differnce/longest_path_length_in_m
    return slope

def desc_TimeOfConcentration(longest_path_length_in_m, slope):
    #tc, Kirpich
    # (0.01947 * length to power of 0.77) / slope to power of 0.385
    tc_mins = (0.01947 * math.pow(longest_path_length_in_m, 0.77))/(math.pow(slope, 0.385))
    tc_hrs = tc_mins/60
    return tc_hrs

def desc_TimeToPeak(storm_duration_hrs, time_of_concentration_hrs):
    #tp
    #(storm duration/2)+0.6 * tc
    tp_hrs = (float(storm_duration_hrs)/2) + 0.6 * time_of_concentration_hrs
    return tp_hrs

def desc_TimeOfBase(tp_hrs):
    #tb
    #ISIS Documentation suggests 5x Tp value
    tb_hrs = tp_hrs * 5
    return tb_hrs

#step 2 - this to get inflow from catchment geometry
def getFlowFromDescriptors(pnt1_height_m, pnt2_height_m, longest_path_length_in_m, catchment_area_km2, runoff_fraction, storm_duration_hrs, total_rainfall_mm):
    slope = desc_slope(pnt1_height_m, pnt2_height_m, longest_path_length_in_m)
    tc_hrs = desc_TimeOfConcentration(longest_path_length_in_m, slope)
    tp_hrs = desc_TimeToPeak(storm_duration_hrs, tc_hrs)
    tb_hrs = desc_TimeOfBase(tp_hrs)
    out_q = unitHydrograph(tp_hrs, catchment_area_km2, tb_hrs)

    return tp_hrs, getInflow(storm_duration_hrs, tp_hrs, total_rainfall_mm, out_q, runoff_fraction)


def getInflow(storm_duration_hrs, tp_hrs, total_rainfall_mm, out_q, runoff_fraction):
    UH_total_fraction_series = rainfall_profile(storm_duration_hrs, tp_hrs)[0] # first output is fraction, second is timestep
    discharge_hydrograph = convolusion(total_rainfall_mm, UH_total_fraction_series, out_q, runoff_fraction)
    return discharge_hydrograph


def unitHydrograph(tp_hrs, catchment_area_km2, tb_hrs):
    UH_cm = (2.08 * catchment_area_km2) / tp_hrs
    UH_mm = UH_cm/10

    t_int = tp_hrs/5

    #unit hydrograph ratios
    # Time Ratios(t/tp)
    t_tp = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2, 2.2, 2.4, 2.6, 2.8, 3, 3.2, 3.4, 3.6, 3.8, 4, 4.5, 5]
    #Discharge Ratios (q/qp)
    q_qp = [0, 0.03, 0.1, 0.19, 0.31, 0.47, 0.66, 0.82, 0.93, 0.99, 1, 0.99, 0.93, 0.86, 0.78, 0.68, 0.56, 0.46, 0.39, 0.33, 0.28, 0.207, 0.147, 0.107, 0.077, 0.055, 0.04, 0.029, 0.021, 0.015, 0.011, 0.005, 0]

    UH_lookup = dict(zip(t_tp, q_qp))

    #Outputs
    out_t = []
    out_t_tp = []
    out_q_qp = []
    out_q = []

    i = 1
    temp_t_tp = t_int/tp_hrs
    while temp_t_tp < max(t_tp):
        out_t.append(t_int * i)
        out_t_tp.append(out_t[i-1]/tp_hrs)
        out_q_qp.append(min(UH_lookup.items(), key=lambda x: abs(out_t_tp[i-1] - x[0]))[1])
        out_q.append(UH_mm * out_q_qp[i-1])

        i += 1
        temp_t_tp = (t_int * (i - 1)) / tp_hrs

    return out_q


# step 3 get rainfall profile
def rainfall_profile(storm_duration_hrs, tp_hrs=5):

    rainfall_profile_time = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 5, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 6, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 7, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 8, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 9, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 10, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9, 11, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 12, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9, 13, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9, 14, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9, 15, 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8, 15.9, 16, 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8, 16.9, 17, 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 17.8, 17.9, 18, 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7, 18.8, 18.9, 19, 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8, 19.9, 20, 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7, 20.8, 20.9, 21, 21.1, 21.2, 21.3, 21.4, 21.5, 21.6, 21.7, 21.8, 21.9, 22, 22.1, 22.2, 22.3, 22.4, 22.5, 22.6, 22.7, 22.8, 22.9, 23.0, 23.1, 23.2, 23.3, 23.4, 23.5, 23.6, 23.7, 23.8, 23.9, 24.0]
    rainfall_profile_fraction_type1 = [0, 0.00174, 0.00348, 0.00522, 0.00697, 0.00871, 0.01046, 0.0122, 0.01395, 0.0157, 0.01745, 0.0192, 0.02095, 0.0227, 0.02446, 0.02621, 0.02797, 0.02972, 0.03148, 0.03324, 0.035, 0.03677, 0.03858, 0.04041, 0.04227, 0.04416, 0.04608, 0.04803, 0.05001, 0.05201, 0.05405, 0.05611, 0.05821, 0.06033, 0.06248, 0.06466, 0.06687, 0.06911, 0.07138, 0.07367, 0.076, 0.07835, 0.0807, 0.08307, 0.08545, 0.08784, 0.09024, 0.09265, 0.09507, 0.09751, 0.09995, 0.10241, 0.10487, 0.10735, 0.10984, 0.11234, 0.11485, 0.11737, 0.1199, 0.12245, 0.125, 0.12761, 0.13034, 0.13317, 0.1361, 0.13915, 0.1423, 0.14557, 0.14894, 0.15241, 0.156, 0.15966, 0.16334, 0.16706, 0.17082, 0.1746, 0.17842, 0.18226, 0.18614, 0.19006, 0.194, 0.19817, 0.20275, 0.20775, 0.21317, 0.219, 0.22523, 0.23185, 0.23885, 0.24623, 0.254, 0.26233, 0.27139, 0.28119, 0.29173, 0.303, 0.31942, 0.34542, 0.38784, 0.46316, 0.515, 0.5322, 0.5476, 0.5612, 0.573, 0.583, 0.59188, 0.60032, 0.60832, 0.61588, 0.623, 0.62982, 0.63648, 0.64298, 0.64932, 0.6555, 0.66152, 0.66738, 0.67308, 0.67862, 0.684, 0.68925, 0.6944, 0.69945, 0.7044, 0.70925, 0.714, 0.71865, 0.7232, 0.72765, 0.732, 0.73625, 0.7404, 0.74445, 0.7484, 0.75225, 0.756, 0.75965, 0.7632, 0.76665, 0.77, 0.77329, 0.77656, 0.77981, 0.78304, 0.78625, 0.78944, 0.79261, 0.79576, 0.79889, 0.802, 0.80509, 0.80816, 0.81121, 0.81424, 0.81725, 0.82024, 0.82321, 0.82616, 0.82909, 0.832, 0.83489, 0.83776, 0.84061, 0.84344, 0.84625, 0.84904, 0.85181, 0.85456, 0.85729, 0.86, 0.86269, 0.86536, 0.86801, 0.87064, 0.87325, 0.87584, 0.87841, 0.88096, 0.88349, 0.886, 0.88849, 0.89096, 0.89341, 0.89584, 0.89825, 0.90064, 0.90301, 0.90536, 0.90769, 0.91, 0.91229, 0.91456, 0.91681, 0.91904, 0.92125, 0.92344, 0.92561, 0.92776, 0.92989, 0.932, 0.93409, 0.93616, 0.93821, 0.94024, 0.94225, 0.94424, 0.94621, 0.94816, 0.95009, 0.952, 0.95389, 0.95576, 0.95761, 0.95944, 0.96125, 0.96304, 0.96481, 0.96656, 0.96829, 0.97, 0.97169, 0.97336, 0.97501, 0.97664, 0.97825, 0.97984, 0.98141, 0.98296, 0.98449, 0.986, 0.98749, 0.98896, 0.99041, 0.99184, 0.99325, 0.99464, 0.99601, 0.99736, 0.99869, 1]
    rainfall_fraction_in_timestep_type1 =[]
    for i in range(len(rainfall_profile_time)):
        if i == 0:
            rainfall_fraction_in_timestep_type1.append(0)
        else:
            rainfall_fraction_in_timestep_type1.append(rainfall_profile_fraction_type1[i] - rainfall_profile_fraction_type1[i-1])

    UH_fraction_lookup = dict(zip(rainfall_fraction_in_timestep_type1, rainfall_profile_time))

    #condense to same timestep of unit hydrograph
    UH_timestep_series = []
    UH_total_fraction_series = []
    if tp_hrs is None:
        tp_hrs = 5
    t_int = tp_hrs / 5
    last_ts = 0
    for n in range(math.ceil(float(storm_duration_hrs)/t_int)+1):
        UH_timestep_series.append(n * t_int)
        UH_total_fraction_series.append(sum(i for i in rainfall_fraction_in_timestep_type1 if UH_fraction_lookup[i] <= UH_timestep_series[n] and UH_fraction_lookup[i] > last_ts))
        last_ts = UH_timestep_series[n]
    return UH_total_fraction_series, UH_timestep_series



def convolusion(rainfall_total_mm, UH_total_fraction_series, UH_out_q, runoff_fraction):
    #using numpy convolve
    UH_rainfall_series = np.array(UH_total_fraction_series) * rainfall_total_mm * float(runoff_fraction)
    discharge_hydrograph = np.convolve(UH_rainfall_series, UH_out_q)
    z= 1
    return discharge_hydrograph


