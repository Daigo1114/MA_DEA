import pandas as pd

# Load your data
data = pd.read_csv('output1.csv')

# Filter to keep only rows where source is 'electricity' or 'equipment'
filtered_data = data[data['source'].isin(['electricity', 'equipment'])]

# Function to aggregate the sums and keep the first occurrence of non-numeric columns
def custom_agg(x):
    d = {}
    # Summing up the numeric columns
    d['1. Deal With Orders amount'] = x['1. Deal With Orders amount'].sum()
    d['2. Communicate With Warehouse amount'] = x['2. Communicate With Warehouse amount'].sum()
    d['3. Pack Orders amount'] = x['3. Pack Orders amount'].sum()
    d['4. Prepare to Send Orders amount'] = x['4. Prepare to Send Orders amount'].sum()
    d['5. Deliver Orders amount'] = x['5. Deliver Orders amount'].sum()
    d['6. Close Orders amount'] = x['6. Close Orders amount'].sum()
    # Keeping the first non-numeric columns that are not part of the grouping
    for col in x.select_dtypes(exclude=['number']).columns:
        if col not in ['order_id', 'GHG type', 'simulation time', 'source']:
            d[col] = x[col].iloc[0]
    return pd.Series(d, index=[*d.keys()])

# Group by 'order_id', 'GHG type', and 'simulation time' and use custom aggregation
grouped_totals = filtered_data.groupby(['order_id', 'GHG type', 'simulation time']).apply(custom_agg).reset_index()

# Adding the source as 'total'
grouped_totals['source'] = 'total'

# Merge the new 'total' rows back to the original dataframe
augmented_data = pd.concat([data, grouped_totals], ignore_index=True)

# Save the augmented data to a new CSV file
augmented_data.to_csv('augmented_data.csv', index=False)
