import pandas as pd

# Load the datasets
customers = pd.read_csv('archive\olist_customers_dataset.csv')
orders = pd.read_csv('archive\olist_orders_dataset.csv')
order_items = pd.read_csv('archive\olist_order_items_dataset.csv')
order_payments = pd.read_csv('archive\olist_order_payments_dataset.csv')
products = pd.read_csv('archive\olist_products_dataset.csv')
sellers = pd.read_csv('archive\olist_sellers_dataset.csv')
geolocation = pd.read_csv('archive\olist_geolocation_dataset.csv')

# Group by geolocation zip code prefix and calculate average lat and lng
geo_grouped = geolocation.groupby('geolocation_zip_code_prefix').agg({
    'geolocation_lat': 'mean',
    'geolocation_lng': 'mean'
}).reset_index()

# Merge the customer and seller geolocation data
customers = pd.merge(customers, geo_grouped, left_on='customer_zip_code_prefix', right_on='geolocation_zip_code_prefix', how='left')
customers.rename(columns={'geolocation_lat': 'customer_geo_lat', 'geolocation_lng': 'customer_geo_lng'}, inplace=True)

sellers = pd.merge(sellers, geo_grouped, left_on='seller_zip_code_prefix', right_on='geolocation_zip_code_prefix', how='left')
sellers.rename(columns={'geolocation_lat': 'seller_geo_lat', 'geolocation_lng': 'seller_geo_lng'}, inplace=True)

# Merge all datasets starting with orders
merged_data = pd.merge(orders, customers[['customer_id', 'customer_unique_id', 'customer_zip_code_prefix', 'customer_city', 'customer_state', 'customer_geo_lat', 'customer_geo_lng']], on='customer_id', how='left')
merged_data = pd.merge(merged_data, order_items, on='order_id', how='left')
merged_data = pd.merge(merged_data, order_payments, on='order_id', how='left')
merged_data = pd.merge(merged_data, products, on='product_id', how='left')
merged_data = pd.merge(merged_data, sellers[['seller_id', 'seller_zip_code_prefix', 'seller_city', 'seller_state', 'seller_geo_lat', 'seller_geo_lng']], on='seller_id', how='left')

# Selecting the specific columns needed as per your request, now including geo columns
final_data = merged_data[[
    'order_id', 'order_item_id', 'order_purchase_timestamp', 'payment_type', 
    'customer_id', 'customer_unique_id', 
    'customer_zip_code_prefix', 'customer_city', 'customer_state', 'customer_geo_lat', 'customer_geo_lng', 
    'seller_id', 'seller_zip_code_prefix', 'seller_city', 'seller_state', 'seller_geo_lat', 'seller_geo_lng', 
    'shipping_limit_date', 'price', 'freight_value', 'product_id', 
    'product_category_name', 'product_name_lenght', 'product_description_lenght', 
    'product_photos_qty', 'product_weight_g', 'product_length_cm', 'product_height_cm', 'product_width_cm'
]]

# Handle NaNs in payment_type before aggregation
final_data['payment_type'] = final_data['payment_type'].fillna('Unknown')

# Aggregate payment types for the same order_id
def combine_payment_types(series):
    unique_types = series.unique()
    return ', '.join(sorted(unique_types))

# Group by 'order_id' and aggregate
aggregated_payments = final_data.groupby('order_id')['payment_type'].apply(combine_payment_types).reset_index()

# Merge the aggregated payment types back to the main dataset
final_data = pd.merge(final_data.drop('payment_type', axis=1), aggregated_payments, on='order_id', how='left')

# Sort the data by 'order_purchase_timestamp'
final_data.sort_values(by='order_purchase_timestamp', inplace=True)


# Remove rows with any empty cells
final_data.dropna(inplace=True)

# Group by 'order_id' and keep the row with the maximum 'order_item_id'
data_max_item = final_data.loc[final_data.groupby('order_id')['order_item_id'].idxmax()]

# Sort the data by 'order_purchase_timestamp'
data_max_item.sort_values(by='order_purchase_timestamp', inplace=True)

# Save the cleaned dataset to a new CSV file
data_max_item.to_csv('sorted_data_traces.csv', index=False)


