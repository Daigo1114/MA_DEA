import calendar
import pandas as pd
import math
from collections import defaultdict
from datetime import datetime, timedelta
import pickle

#Emissions Factors lb/MWh
electricity_factor_co2_old = 657.4
electricity_factor_ch4_old = 0.045
electricity_factor_n2o_old = 0.006

commuting_factor_co2_old = 0.175  #kg/vehicle-mile
commuting_factor_ch4_old = 0.005  #g/vehicle-mile
commuting_factor_n2o_old = 0.003  #g/vehicle-mile

deliver_factor_co2_old = 0.168  #kg/ton-mile
deliver_factor_ch4_old = 0.0015  #g/ton-mile
deliver_factor_n2o_old = 0.0047  #g/ton-mile

waste_factor_cardboard_old = 0.05  #Metric Tons CO2/ Short Ton Material;
waste_factor_bubble_old = 2.8

#Assumptions
power_computers = 0.2  #kWh
power_area = 6.1 / 365  #6.1kWh per year per m^2
warehouse_area = 1000  #m^2
office_area = 3  #m^2
seller_num = 1
warehouse_worker_num = 2
distance_work = 10   #km
density_cardboard = 0.69   #g/cm^3
density_bubble = 0.017  #g/cm^3

def extract_timestamp(order_id, df):
    specific_order = df[df['order_id'] == order_id]
    specific_order['timestamp'] = pd.to_datetime(specific_order['timestamp'])
    specific_order = specific_order.sort_values('timestamp')
    timestamps = specific_order['timestamp'].tolist()
    #print(timestamps)
    return timestamps

#Transformation
def kg_to_g(kg):
    return kg * 1000

def g_to_kg(g):
    return g / 1000

def lb_per_MWh_to_kg_per_kWh(lb_per_MWh):
    kg_per_kWh = (lb_per_MWh * 0.453592) / 1000
    return kg_per_kWh

def kgCO2_per_mile_to_kgCO2_per_km(kgCO2_per_mile):
    kgCO2_per_km = kgCO2_per_mile / 1.60934
    return kgCO2_per_km

def g_per_mile_to_g_per_km(g_per_mile):
    g_per_km = g_per_mile / 1.60934
    return g_per_km

def kgCO2_per_ton_mile_to_kgCO2_per_kg_km(kgCO2_per_ton_mile):
    kgCO2_per_kg_km = (kgCO2_per_ton_mile / 907.185) / 1.60934
    return kgCO2_per_kg_km

def g_per_ton_mile_to_g_per_kg_km(g_per_ton_mile):
    g_per_kg_km = (g_per_ton_mile / 907.185) / 1.60934
    return g_per_kg_km

def metric_tons_CO2_per_short_ton_to_kgCO2_per_kg(metric_tons_CO2_per_short_ton):
    kgCO2_per_kg = (metric_tons_CO2_per_short_ton * 1000) / 907.185
    return kgCO2_per_kg

#compute activity duration
def working_hours_between(timestamp1, timestamp2):
    # Ensure timestamp1 is earlier than timestamp2
    if timestamp1 > timestamp2:
        timestamp1, timestamp2 = timestamp2, timestamp1

    # Calculate the total seconds between timestamps
    total_seconds = (timestamp2 - timestamp1).total_seconds()

    # Convert total seconds to hours
    total_hours = total_seconds / 3600

    return total_hours

def count_days_between(timestamp1, timestamp2):
    if timestamp1 > timestamp2:
        timestamp1, timestamp2 = timestamp2, timestamp1
    start_date = timestamp1.normalize()
    end_date = timestamp2.normalize()
    full_days = (end_date - start_date).days + 1
    return full_days

def haversine(lat1, lon1, lat2, lon2):
    # Convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of Earth in kilometers. Use 3956 for miles
    return c * r

#compute scope 2 equiment emission
def computer_emission(hours, power_usage, factors, equi_num):
    equi_emission = power_usage * factors * hours * equi_num
    return equi_emission

#compute scope 2 electricity emission
def electricity_emission(hours, area, power_usage, factors):
    day = hours / 24
    elec_emission = area * factors * power_usage * day
    return elec_emission 


def convert_factors():
    # Convert all factors to unified units (CO2 in kg, CH4 and N2O in g)
    factors = {
        'electricity_factor_co2': lb_per_MWh_to_kg_per_kWh(electricity_factor_co2_old),
        'electricity_factor_ch4': kg_to_g(lb_per_MWh_to_kg_per_kWh(electricity_factor_ch4_old)),
        'electricity_factor_n2o': kg_to_g(lb_per_MWh_to_kg_per_kWh(electricity_factor_n2o_old)),
        
        'commuting_factor_co2': kgCO2_per_mile_to_kgCO2_per_km(commuting_factor_co2_old),
        'commuting_factor_ch4': g_per_mile_to_g_per_km(commuting_factor_ch4_old),
        'commuting_factor_n2o': g_per_mile_to_g_per_km(commuting_factor_n2o_old),

        'deliver_factor_co2': kgCO2_per_ton_mile_to_kgCO2_per_kg_km(deliver_factor_co2_old),
        'deliver_factor_ch4': g_per_ton_mile_to_g_per_kg_km(deliver_factor_ch4_old),
        'deliver_factor_n2o': g_per_ton_mile_to_g_per_kg_km(deliver_factor_n2o_old),

        'waste_factor_cardboard': metric_tons_CO2_per_short_ton_to_kgCO2_per_kg(waste_factor_cardboard_old),
        'waste_factor_bubble': metric_tons_CO2_per_short_ton_to_kgCO2_per_kg(waste_factor_bubble_old)
    }
    return factors


def calculate_stage_emissions(hours, area, power_computers, factors, equi = 1):
    # Compute emissions for each gas type, separating equipment and electricity sources
    emissions = {
        'co2': {
            'equipment': computer_emission(hours, power_computers, factors['electricity_factor_co2'], equi),
            'electricity': electricity_emission(hours, area, power_area, factors['electricity_factor_co2'])
        },
        'ch4': {
            'equipment': computer_emission(hours, power_computers, factors['electricity_factor_ch4'], equi),
            'electricity': electricity_emission(hours, area, power_area, factors['electricity_factor_ch4'])
        },
        'n2o': {
            'equipment': computer_emission(hours, power_computers, factors['electricity_factor_n2o'], equi),
            'electricity': electricity_emission(hours, area, power_area, factors['electricity_factor_n2o'])
        }
    }
    return emissions


def compute_emissions_for_order(order_id, event_log_data, product_weight, product_height, product_length, product_width, cus_lat, cus_lon, sel_lat, sel_lon):
    t = extract_timestamp(order_id,event_log_data)

    factors = convert_factors()

    hours_data = []
    total_area = office_area + warehouse_area

    #1_deal_with_order
    hours_1 = working_hours_between(t[0],t[1])

    #2_communicate_with_warehouse
    hours_2 = working_hours_between(t[1],t[2])

    #3_packing_warehouse
    hours_3 = working_hours_between(t[2],t[3])
    
    #4_prepare_send
    hours_4 = working_hours_between(t[3],t[5])

    #5_deliver
    hours_5 = working_hours_between(t[5],t[6])

    #6_close_order
    hours_6 = working_hours_between(t[6],t[8])
    hours_data.append(hours_1)
    hours_data.append(hours_2)
    hours_data.append(hours_3)
    hours_data.append(hours_4)
    hours_data.append(hours_5)
    hours_data.append(hours_6)
    #print(hours_data)

    emissions = {}
    for i, hours in enumerate(hours_data):
        if f'stage_{i+1}' not in emissions:
                emissions[f'stage_{i+1}'] = {}
        emissions[f'stage_{i+1}']['emissions'] = calculate_stage_emissions(hours_data[i], total_area, power_computers, factors)

    emissions['stage_1']['time_between'] = (t[0],t[1])
    emissions['stage_2']['time_between'] = (t[1],t[2])
    emissions['stage_3']['time_between'] = (t[2],t[3])
    emissions['stage_4']['time_between'] = (t[3],t[5])
    emissions['stage_5']['time_between'] = (t[5],t[6])
    emissions['stage_6']['time_between'] = (t[6],t[8])

    #scope3_daily_commuting
    working_days = count_days_between(t[0],t[-1])
    workers = seller_num + warehouse_worker_num
    emissions['commuting'] = {
        'co2': workers * 2 * distance_work * factors['commuting_factor_co2'] * working_days,
        'ch4': workers * 2 * distance_work * factors['commuting_factor_ch4'] * working_days,
        'n2o': workers * 2 * distance_work * factors['commuting_factor_n2o'] * working_days,
    }

    #scope3_waste
    cardboard_weight_g = 2 * (product_length * product_width + product_length * product_height + product_width * product_height) * 0.5 * density_cardboard
    cardboard_weight = g_to_kg(cardboard_weight_g)
    bubble_weight_g = product_height * product_length * product_width * density_bubble
    bubble_weight = g_to_kg(bubble_weight_g)
    waste_emission = cardboard_weight * factors['waste_factor_cardboard'] + bubble_weight * factors['waste_factor_bubble']
    #print(cardboard_weight, bubble_weight, waste_emission)
    emissions['waste'] = {'co2': waste_emission}

    #scope3_delivery
    distance_order = haversine(cus_lat, cus_lon, sel_lat, sel_lon)
    product_weight_kg = g_to_kg(product_weight)  
    emissions['delivery'] = {
        'co2': distance_order * (cardboard_weight + product_weight_kg + bubble_weight) * factors['deliver_factor_co2'],
        'ch4': distance_order * (cardboard_weight_g + product_weight + bubble_weight_g) * factors['deliver_factor_ch4'],
        'n2o': distance_order * (cardboard_weight_g + product_weight + bubble_weight_g) * factors['deliver_factor_n2o']
    }
    
    return emissions

#the office related workers and warehouse related workers may changed due to order numbers

def calculate_scale_factors(times):
    monthly_orders = defaultdict(int)

    for start, end in times.values():
        start = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")

        # Make sure to include the end month if it ends on the first day of the month
        if end.day == 1 and end != start:
            end -= timedelta(days=1)

        current = start
        while current <= end:
            year_month = (current.year, current.month)
            monthly_orders[year_month] += 1
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
            current = current.replace(day=1)  # Set to the first of the month


    print(monthly_orders)
    # Calculate scale factors for each month
    scale_factors = {}
    for year_month, count in monthly_orders.items():
        scale_factors[year_month] = (count - 1) // 10 + 1  # Calculate scale factor for this month

    return scale_factors

def calculate_monthly_hours(start, end):
    """ Calculate the number of hours in each month between two dates. """
    monthly_hours = defaultdict(int)
    current = start
    last_month_key = None
    while current <= end:
        last_day_of_month = datetime(current.year, current.month, calendar.monthrange(current.year, current.month)[1])
        next_month_start = last_day_of_month + timedelta(days=1)
        # If the end date is before the next month starts, use the end date instead
        period_end = min(next_month_start, end + timedelta(days=1))
        hours_in_month = (period_end - current).total_seconds() / 3600
        month_key = (current.year, current.month)
        monthly_hours[month_key] += hours_in_month
        last_month_key = month_key
        current = next_month_start

    # Subtract 24 hours from the last month's total if it's non-zero and exists
    if last_month_key and monthly_hours[last_month_key] > 24:
        monthly_hours[last_month_key] -= 24

    return monthly_hours

#main function
def main():
    # Load the sorted_traces.csv file
    sorted_traces_df = pd.read_csv('sorted_traces.csv')

    event_logs_df = pd.read_csv('sorted_event_logs.csv')

    num = 5
    truncated_df = sorted_traces_df.head(num)
   
    single_emissions = {}
    times = {}
    event_dt = {}
    for index, row in truncated_df.iterrows():
        order_id = row['order_id']
        event_log_data = event_logs_df[event_logs_df['order_id'] == order_id]
        #print(event_log_data)
        em = compute_emissions_for_order(
            order_id,
            event_log_data,
            row['product_weight_g'],
            row['product_height_cm'],
            row['product_length_cm'],
            row['product_width_cm'],
            row['customer_geo_lat'],
            row['customer_geo_lng'],
            row['seller_geo_lat'],
            row['seller_geo_lng']
        )
        single_emissions[order_id] = em
        if not event_log_data.empty:
            start_timestamp = event_log_data['timestamp'].min()
            end_timestamp = event_log_data['timestamp'].max()
            times[order_id] = (start_timestamp, end_timestamp)
            event_dt[order_id] = event_log_data['timestamp'].to_list()
        else:
            times[order_id] = (None, None)
            event_dt[order_id] = []

    print(single_emissions)
    #print(times)
    #print(event_dt)
    earliest_timestamp = None
    latest_timestamp = None
    for timestamps in times.values():
        start, end = timestamps
        # Convert strings to datetime for comparison
        start = pd.to_datetime(start)
        end = pd.to_datetime(end)
    
        if earliest_timestamp is None or start < earliest_timestamp:
            earliest_timestamp = start
        if latest_timestamp is None or end > latest_timestamp:
            latest_timestamp = end

    mon_hour = calculate_monthly_hours(earliest_timestamp, latest_timestamp)
    #print(mon_hour) 
    factors = convert_factors()
    faci = calculate_scale_factors(times)
    #print(h, d, faci)
    month_days = {}
    multiple_emissions = {}
    multiple_emissions['Scope 2'] = {}
    multiple_emissions['Scope 3'] = {}
    multiple_emissions['Scope 3']['commuting'] = {}
    multiple_emissions['Scope 3']['waste'] = {}
    multiple_emissions['Scope 3']['delivery'] = {}
    #total emission on scope 2 (equipment and electricity)
    for (year,month), hours in mon_hour.items():
        scale = faci.get((year,month),1)
        d = math.ceil(hours/24)
        #print(year, month, hours, d)
        emm = calculate_stage_emissions(hours, (office_area * scale + warehouse_area), power_computers, factors, equi=scale)
        month_key = f"{year}-{month:02d}"
        multiple_emissions['Scope 2'][month_key] = emm
        total_workers_num = scale * (seller_num + warehouse_worker_num)
        #total commuting emission on scope 3.1
        multiple_emissions['Scope 3']['commuting'][month_key] = {
        'co2': total_workers_num * 2 * distance_work * factors['commuting_factor_co2'] * d,
        'ch4': total_workers_num * 2 * distance_work * factors['commuting_factor_ch4'] * d,
        'n2o': total_workers_num * 2 * distance_work * factors['commuting_factor_n2o'] * d,
        }
    #print(multiple_emissions)

    #total waste emission on scope 3.2
    #total delivery emission on scope 3.3
    total_waste = 0
    total_delivery_co2 = 0
    total_delivery_ch4 = 0
    total_delivery_n2o = 0
    
    
    for order_id, emissions in single_emissions.items():
        waste_ = emissions.get('waste', 0)
        #print(waste_)
        #print(waste_['co2'])
        total_waste += waste_['co2']

        delivery_emissions = emissions.get('delivery', {})
        #print(delivery_emissions)
        #print(delivery_emissions['co2'])
        total_delivery_co2 += delivery_emissions['co2']
        total_delivery_ch4 += delivery_emissions['ch4']
        total_delivery_n2o += delivery_emissions['n2o']

    #print(total_waste, total_delivery_co2, total_delivery_ch4, total_delivery_n2o)
    multiple_emissions['Scope 3']['waste']['co2'] = total_waste
    multiple_emissions['Scope 3']['delivery']['co2'] = total_delivery_co2
    multiple_emissions['Scope 3']['delivery']['ch4'] = total_delivery_ch4
    multiple_emissions['Scope 3']['delivery']['n2o'] = total_delivery_n2o

    
    return single_emissions, multiple_emissions, times, event_dt, earliest_timestamp, latest_timestamp
    

if __name__ == "__main__":
    single_emissions, multiple_emissions, times, event_dt, earliest_timestamp, latest_timestamp = main()
    #main()
    with open('data.pickle', 'wb') as f:
        pickle.dump((single_emissions, multiple_emissions, times, event_dt, earliest_timestamp, latest_timestamp), f)
    