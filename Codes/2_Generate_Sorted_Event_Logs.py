import pandas as pd
import numpy as np

# Load datasets
orders_data = pd.read_csv('archive\olist_orders_dataset.csv')
# Assuming reviews are contained in the 'final_olist_data_traces.csv'
traces_data = pd.read_csv('sorted_data_traces.csv')
reviews_data = pd.read_csv('archive/olist_order_reviews_dataset.csv')

# Merge necessary data
data = pd.merge(orders_data, traces_data, on='order_id', how='left')

data = pd.merge(data, reviews_data[['order_id', 'review_answer_timestamp']], on='order_id', how='left')

data.dropna(inplace=True)

# Combine order_purchase_timestamp_x and order_purchase_timestamp_y into order_purchase_timestamp
data['order_purchase_timestamp'] = data['order_purchase_timestamp_x']
data.drop(columns=['order_purchase_timestamp_x', 'order_purchase_timestamp_y'], inplace=True)

# Prepare the event log DataFrame
event_logs = pd.DataFrame()

# Loop through each order to generate events
for idx, row in data.iterrows():
    events = []
    order_id = row['order_id']
    #print(row)
    
    # Generating random times for events
    order_approved_at = pd.to_datetime(row['order_approved_at'])
    rnd_minutes_warehouse = pd.Timedelta(minutes=np.random.randint(5, 30))  # 30 minutes to 2 hours
    rnd_minutes_close = pd.Timedelta(minutes=np.random.randint(10, 30))  # 10 to 30 minutes
    rnd_minutes_prepared = pd.Timedelta(minutes=np.random.randint(5, 15))
    
    # Event 3 calculation
    order_sent_to_warehouse = order_approved_at + rnd_minutes_warehouse

    # Event 5 calculation
    order_delivered_carrier_date = pd.to_datetime(row['order_delivered_carrier_date'])
    delivery_date_established = order_delivered_carrier_date - pd.Timedelta(minutes=10)
    
    # Event 4 calculation
    time_diff = delivery_date_established - order_sent_to_warehouse

    if time_diff.total_seconds() <= 0:
        # Skip the current iteration and start a new loop
        continue

    order_prepared_warehouse = order_sent_to_warehouse + pd.Timedelta(seconds=np.random.randint(0, time_diff.total_seconds()))
    


    print(row['order_purchase_timestamp'], row['order_approved_at'], order_sent_to_warehouse, order_prepared_warehouse, delivery_date_established, row['order_delivered_carrier_date'], row['order_delivered_customer_date'], row['review_answer_timestamp'], pd.to_datetime(row['review_answer_timestamp']) + rnd_minutes_close )
    
    events.append([order_id, order_id+'_1', row['order_purchase_timestamp'], 'ORDER_PLACED_BY_CUSTOMERS', 'CUSTOMER'])
    events.append([order_id, order_id+'_2', row['order_approved_at'], 'ORDER_APPROVED_BY_SELLER', 'SELLER'])
    events.append([order_id, order_id+'_3', order_sent_to_warehouse, 'ORDER_SENT_TO_WAREHOUSE', 'SELLER'])
    events.append([order_id, order_id+'_4', order_prepared_warehouse, 'ITEM_PACKED_IN_WAREHOUSE', 'WAREHOUSE'])
    events.append([order_id, order_id+'_5', delivery_date_established, 'DELIVERY_DATE_ESTABLISHED', 'WAREHOUSE'])
    events.append([order_id, order_id+'_6', row['order_delivered_carrier_date'], 'ITEM_DELIVERED', 'WAREHOUSE'])
    events.append([order_id, order_id+'_7', row['order_delivered_customer_date'], 'ITEM_RECEIVED', 'CUSTOMER'])
    events.append([order_id, order_id+'_8', row['review_answer_timestamp'], 'ORDER_COMMENTED_BY_CUSTOMER', 'CUSTOMER'])
    events.append([order_id, order_id+'_9', pd.to_datetime(row['review_answer_timestamp']) + rnd_minutes_close, 'ORDER_CLOSED', 'SELLER'])

    # Append to the main DataFrame
    event_logs = pd.concat([event_logs, pd.DataFrame(events, columns=['order_id', 'event_id', 'timestamp', 'event_name', 'role'])], ignore_index=True)


# Convert 'timestamp' column to datetime format
event_logs['timestamp'] = pd.to_datetime(event_logs['timestamp'])

# Group by 'order_id' to find the first timestamp for each group
first_timestamp = event_logs.groupby('order_id')['timestamp'].min().reset_index()

# Merge this minimum timestamp back into the original data
data_with_first_timestamp = event_logs.merge(first_timestamp, on='order_id', suffixes=('', '_first'))

# Sort the data by the first timestamp and then by each event's timestamp
sorted_data = data_with_first_timestamp.sort_values(['timestamp_first', 'timestamp'])

# Drop the auxiliary column used for sorting
sorted_data.drop(columns=['timestamp_first'], inplace=True)

# Save the sorted data
sorted_data.to_csv('sorted_data_event_logs.csv', index=False)
