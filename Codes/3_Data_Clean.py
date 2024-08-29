import pandas as pd

# Load the data from both files
data_olist_traces = pd.read_csv('sorted_data_traces.csv')
data_sorted_path = pd.read_csv('sorted_data_event_logs.csv')

# Find unique order_ids in each file
order_ids_olist_traces = set(data_olist_traces['order_id'].unique())
order_ids_sorted_path = set(data_sorted_path['order_id'].unique())

# Compute the order_ids to remove (those in olist_traces but not in sorted_path)
order_ids_to_remove = order_ids_olist_traces - order_ids_sorted_path

# Filter the olist traces, removing the unwanted order_ids
filtered_data_olist_traces = data_olist_traces[~data_olist_traces['order_id'].isin(order_ids_to_remove)]

# Save the filtered data to a new CSV file
filtered_data_olist_traces.to_csv('sorted_traces.csv', index=False)

print("Data has been filtered and saved.")
