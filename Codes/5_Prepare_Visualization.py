import pandas as pd
import pickle

with open('data.pickle', 'rb') as f:
    single_emissions, multiple_emissions, times, event_dt, earliest_timestamp, latest_timestamp = pickle.load(f)

def flatten_data(data, order_id, stage_mapping):
    
    stages = []
    ghg_types = []
    sources_list = []
    amounts = []
    order_ids = []
    scopes = []  

    for key, value in data.items():
        stage_name = stage_mapping.get(key, key) 
        scope_label = 'scope2' if key in stage_mapping else 'scope3'  
        if 'emissions' in value:
            for ghg, sources in value['emissions'].items():
                for source, amount in sources.items():
                    stages.append(stage_name)
                    ghg_types.append(ghg)
                    sources_list.append(source)
                    amounts.append(amount)
                    order_ids.append(order_id)
                    scopes.append(scope_label) 
        elif isinstance(value, dict):
            for ghg, amount in value.items():
                stages.append(stage_name)
                ghg_types.append(ghg)
                sources_list.append('total')
                amounts.append(amount)
                order_ids.append(order_id)
                scopes.append(scope_label)

    df = pd.DataFrame({
        'Order ID': order_ids,
        'Stage': stages,
        'GHG Type': ghg_types,
        'Source': sources_list,
        'Amount': amounts,
        'Scope': scopes  
    })
    return df

stage_mapping = {
    'stage_1': '1. Deal With Orders',
    'stage_2': '2. Communicate With Warehouse',
    'stage_3': '3. Pack Orders',
    'stage_4': '4. Prepare to Send Orders',
    'stage_5': '5. Deliver Orders',
    'stage_6': '6. Close Orders'
}

all_data = pd.DataFrame()
for order_id, emissions_data in single_emissions.items():
    df = flatten_data(emissions_data, order_id, stage_mapping)
    all_data = pd.concat([all_data, df], ignore_index=True)

all_data.to_csv('emissions_data.csv', index=False)
print("Data has been flattened and saved to 'emissions_data.csv'.")