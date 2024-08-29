import pandas as pd
import pickle

with open('data.pickle', 'rb') as f:
    single_emissions, multiple_emissions, times, event_dt, earliest_timestamp, latest_timestamp = pickle.load(f)


for order_id, t in event_dt.items():
    print(t)
    t_list = list(t)
    del t_list[4]
    del t_list[7]
    event_dt[order_id] = t_list

stage_mapping = {
    'stage_1': '1. Deal With Orders',
    'stage_2': '2. Communicate With Warehouse',
    'stage_3': '3. Pack Orders',
    'stage_4': '4. Prepare to Send Orders',
    'stage_5': '5. Deliver Orders',
    'stage_6': '6. Close Orders'
}

def generate_simulation_times(order_id):
    simulation_times = []
    # Accessing times dictionary correctly and converting each time string to pd.Timestamp
    order_start_time, order_end_time = (pd.Timestamp(times[order_id][0]), pd.Timestamp(times[order_id][1]))
    order_duration = order_end_time - order_start_time
    intervals = max(1, int(order_duration.total_seconds() / (6 * 3600)))
    current_time = order_start_time

    while current_time < order_end_time:
        simulation_times.append(current_time)
        next_time = current_time + pd.Timedelta(hours=6)
        # Ensure that the simulation time does not exceed the order end time
        current_time = next_time if next_time < order_end_time else order_end_time

    # Append the end time if not already included
    if simulation_times[-1] != order_end_time:
        simulation_times.append(order_end_time)

    return simulation_times

#simu_times = generate_simulation_times('3b697a20d9e427646d92567910af6d57')
#print(simu_times)

def generate_stage_times():
    scope2_stage_times = {}
    scope3_stage_times = {}
    stage_times = {}

    for order_id, timestamps in event_dt.items():
        scope2_stage_times[order_id] = {}
        scope3_stage_times[order_id] = {}
        stage_times[order_id] = {}

        for i in range(1, len(timestamps)):
            stage_number = i
            stage_key = f"stage_{stage_number}"
            mapped_stage_name = stage_mapping.get(stage_key, stage_key)
            start_time = timestamps[i-1]
            end_time = timestamps[i]
            scope2_stage_times[order_id][mapped_stage_name] = (start_time, end_time)
            stage_times[order_id][mapped_stage_name] = (start_time, end_time)

        scope3_stage_times[order_id]['commuting'] = (timestamps[0], timestamps[-1])
        stage_times[order_id]['commuting'] = (timestamps[0], timestamps[-1])
        if 'stage_3' in stage_mapping:
            mapped_stage_name = stage_mapping.get('stage_3', 'stage_3')
            scope3_stage_times[order_id]['waste'] = scope2_stage_times[order_id].get(mapped_stage_name)
            stage_times[order_id]['waste'] = scope2_stage_times[order_id].get(mapped_stage_name)

        if 'stage_5' in stage_mapping:
            mapped_stage_name = stage_mapping.get('stage_5', 'stage_5')
            scope3_stage_times[order_id]['delivery'] = scope2_stage_times[order_id].get(mapped_stage_name)
            stage_times[order_id]['delivery'] = scope2_stage_times[order_id].get(mapped_stage_name)
    
    return scope2_stage_times, scope3_stage_times, stage_times

s2_st, s3_st, st = generate_stage_times()
#print(s2_st, s3_st)

df = pd.read_csv('emissions_data.csv')

def calculate_units_scope2():
    overall_durations = {}
    for order_id, (start, end) in times.items():
        start_ts = pd.Timestamp(start)
        end_ts = pd.Timestamp(end)
        overall_durations[order_id] = (end_ts - start_ts).total_seconds() / 3600

    df_scope2 = df[df['Scope']=='scope2']
    results = {}
    for (order_id, ghg_type, source), group in df_scope2.groupby(['Order ID', 'GHG Type', 'Source']):
        total_emissions = group['Amount'].sum()
        units = total_emissions/overall_durations[order_id]

        if order_id not in results:
            results[order_id] = []
        results[order_id].append({
            'GHG Type': ghg_type,
            'Source': source,
            'Emissions Per Hour': units
        })

    return results

r = calculate_units_scope2()
print(r)


def calculate_scope3_units(df, scope3_times):
    results = {}
    
    # Filter the DataFrame for Scope 3 emissions only
    df_scope3 = df[df['Scope'] == 'scope3']
    
    # Loop over each order_id and their respective special stages
    for order_id, stages in scope3_times.items():
        for stage, (start, end) in stages.items():
            # Calculate duration differently for commuting vs waste/delivery
            start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)
            if stage == 'commuting':
                # Calculate total days, adding one to include both start and end days
                duration_days = (end_ts - start_ts).days + 1
            else:
                # Calculate duration in hours for waste and delivery
                duration_hours = (end_ts - start_ts).total_seconds() / 3600
            
            # Group by GHG Type and Source within this specific stage and order_id
            grouped = df_scope3[(df_scope3['Order ID'] == order_id) & (df_scope3['Stage'] == stage)].groupby(['GHG Type', 'Source'])
            
            # Calculate total emissions for each group and normalize by the appropriate duration
            for (ghg_type, source), group in grouped:
                total_emissions = group['Amount'].sum()
                if stage == 'commuting':
                    units = total_emissions / duration_days if duration_days > 0 else 0
                else:
                    units = total_emissions / duration_hours if duration_hours > 0 else 0

                # Append results
                if order_id not in results:
                    results[order_id] = []
                results[order_id].append({
                    'Stage': stage,
                    'GHG Type': ghg_type,
                    'Source': source,
                    'Units per day' if stage == 'commuting' else 'Units per hour': units
                })

    return results

def get_unit_scope2(data, order_id, ghg_type, source):
    if order_id in data:
        for emission_info in data[order_id]:
            if emission_info['GHG Type'] == ghg_type and emission_info['Source'] == source:
                return emission_info['Emissions Per Hour']
    # Return None if no match is found
    return None


def add_scope2_amounts_to_csv(df, stage_times, output_csv_path):
    # Assume df has been filtered for scope2 only
    df_scope2 = df[df['Scope'] == 'scope2']
    scope2_unit = calculate_units_scope2()
    # Prepare a list to collect all rows for the DataFrame
    all_rows = []

    # Loop over each unique (order_id, GHG type, source) combination
    for (order_id, ghg_type, source), group in df_scope2.groupby(['Order ID', 'GHG Type', 'Source']):
        print('--------------------------------------')
        simu_times = generate_simulation_times(order_id)
        unit = get_unit_scope2(scope2_unit, order_id, ghg_type, source)
        stage_amounts = {stage: 0 for stage in stage_times[order_id].keys()}
        last_stage_index = None
        last_stage = None
        gr = group[group['Stage']=='2. Communicate With Warehouse']
        stage_2_emi = gr['Amount'].iloc[0]
        grg = group[group['Stage']=='6. Close Orders']
        stage_6_emi = grg['Amount'].iloc[0]
        prev_sim_time = None
        # Process each simulation time
        for i, sim_time in enumerate(simu_times):
            sim_time = pd.Timestamp(sim_time)
            print(prev_sim_time, sim_time)
            emission_record = {
                'order_id': order_id,
                'GHG type': ghg_type,
                'source': source,
                'simulation time': sim_time
            }

            for stage, (start, end) in stage_times[order_id].items():
                start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)
                # Calculate total emissions only if the simulation time is within this stage's interval
                if start_ts <= sim_time <= end_ts or (i == len(simu_times) - 1 and sim_time == end_ts):
                    current_stage = stage
                    current_stage_index = int(stage.split('.')[0])
                    duration_seconds = (sim_time - (prev_sim_time if prev_sim_time else start_ts)).total_seconds()
                    duration_seconds = min(duration_seconds, 21600)
                    print(f"Stage: {stage}, Duration: {duration_seconds}")

                    if last_stage_index is None or last_stage_index == current_stage_index:
                        stage_amounts[stage] += unit * duration_seconds / 3600
                    else:
                        if abs(last_stage_index - current_stage_index) > 1:
                            # Missing stages (index difference > 1)
                            for missed_index in range(last_stage_index + 1, current_stage_index):
                                missed_stage = f"{missed_index}. " + list(stage_times[order_id].keys())[missed_index - 1].split(". ")[1]
                                stage_amounts[missed_stage] = stage_2_emi
                            gra = group[group['Stage']==last_stage]
                            stage_amounts[last_stage] = gra['Amount'].iloc[0]  # Given value when stage changes by 1
                            duration_seconds = min((sim_time-start_ts).total_seconds(), 21600)
                            stage_amounts[stage] += unit * duration_seconds / 3600
                        elif abs(last_stage_index - current_stage_index) == 1:
                            # If stage change and index difference is 1
                            gra = group[group['Stage']==last_stage]
                            stage_amounts[last_stage] = gra['Amount'].iloc[0]  # Given value when stage changes by 1
                            duration_seconds = min((sim_time-start_ts).total_seconds(), 21600)
                            stage_amounts[stage] += unit * duration_seconds / 3600

                    last_stage_index = current_stage_index
                    last_stage = current_stage
                    #emission_record[stage + ' amount'] = stage_amounts[stage]
                    #break
            
            if i == len(simu_times)-2:
                stage_amounts[stage] += unit * 21600/3600
            if i == len(simu_times) -1:
                stage_amounts[stage] = stage_6_emi
            for stage in stage_times[order_id]:
                emission_record[stage + ' amount'] = stage_amounts[stage]
            emission_record['current stage'] = current_stage or 'N/A'
            all_rows.append(emission_record)
            prev_sim_time = sim_time

    # Create a DataFrame from all_rows
    result_df = pd.DataFrame(all_rows)

    # Save the DataFrame to a CSV file
    result_df.to_csv(output_csv_path, index=False)
    print(f"Data saved to {output_csv_path}")

#add_scope2_amounts_to_csv(df,s2_st,'output1.csv')

def get_scope3_unit(scope3_units, order_id, ghg_type, stage):
    # Check if the order_id is in the dictionary
    if order_id in scope3_units:
        # Iterate over the list of GHG data for the given order_id
        for emission_info in scope3_units[order_id]:
            # Check if both GHG type and source match the requested data
            if emission_info['GHG Type'] == ghg_type and emission_info['Stage'] == stage:
                # Return the appropriate unit value
                # The key for unit might be 'Units per day' or 'Units per hour' depending on the stage
                unit_key = 'Units per day' if 'Units per day' in emission_info else 'Units per hour'
                return emission_info[unit_key]
    # Return None or an appropriate default/fallback value if not found
    return None

def add_scope3_amounts_to_csv():
    df_scope3 = df[df['Scope'] == 'scope3']
    scope3_unit = calculate_scope3_units(df, s3_st)
    #print(s3_st)
    #print(scope3_unit)
    all_rows = []

    for (order_id, ghg_type), group in df_scope3.groupby(['Order ID', 'GHG Type']):
        simulation_times = generate_simulation_times(order_id)
        initial_stages = 'commuting'
        amounts_by_stage = {stage: 0 for stage in s3_st[order_id].keys()}
        last_dates = None
        active_stages = set()
        unit_com = get_scope3_unit(scope3_unit, order_id, ghg_type, initial_stages)
        prev_sim_time = None
        stage_end_times = {}

        for sim_time in simulation_times:
            sim_time = pd.Timestamp(sim_time)
            current_date = sim_time.date()
            temp_active_stages = set()

            temp_active_stages.add('commuting')

            if last_dates is None or current_date>last_dates:
                amounts_by_stage[initial_stages] += unit_com
                last_dates = current_date

            for stage, (start, end) in s3_st[order_id].items():
                if stage == 'commuting':
                    continue
                start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)
                unitt = get_scope3_unit(scope3_unit, order_id, ghg_type, stage)
                #print(order_id, ghg_type, stage, unitt)
                if unitt is None:
                    continue
                if start_ts <= sim_time <= end_ts:
                    temp_active_stages.add(stage)
                    stage_end_times[stage] = end_ts
                    duration_seconds = (sim_time - (prev_sim_time if prev_sim_time else start_ts)).total_seconds()
                    duration_hours = duration_seconds/3600
                    amounts_by_stage[stage] += unitt * duration_hours
                    #print(sim_time, prev_sim_time, duration_hours)
                    df_o = df_scope3[df_scope3['Order ID']==order_id]
                    df_g = df_o[df_o['GHG Type']==ghg_type]
                    
                    break
            
            for stage, end_ in stage_end_times.items():
                #print(sim_time, stage, end_)
                if sim_time>end_:
                    df_s = df_g[df_g['Stage']==stage]
                    print('+++++++++++++++++++++')
                    print(df_s)
                    amounts_by_stage[stage] = df_s['Amount'].iloc[0]
                    if stage in temp_active_stages:
                        temp_active_stages.remove(stage)
                        
                        


            emission_record = {
                'order_id': order_id,
                'GHG type': ghg_type,
                'source': 'total',
                'simulation time': sim_time,
                **{f'{stage_details} amount': amount for stage_details, amount in amounts_by_stage.items()},
                'current extra stage': ', '.join(sorted(temp_active_stages))
            }
            all_rows.append(emission_record)
            prev_sim_time = sim_time
    
    result_df = pd.DataFrame(all_rows)
    result_df.to_csv('scope3_emissions.csv', index=False)
    print("Scope 3 emissions data saved to 'scope3_emissions.csv'.")


add_scope3_amounts_to_csv()