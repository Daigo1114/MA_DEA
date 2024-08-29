import pandas as pd

# Load the CSV file
file_path = 'emissions_data.csv'
tdata = pd.read_csv(file_path)

data = tdata[tdata['Source'].isin(['electricity', 'equipment'])]

# Sum the Amounts
# Group by Order ID, Stage, and GHG Type, and sum the Amounts
grouped_data = data.groupby(['Order ID', 'Stage', 'GHG Type'], as_index=False).agg({
    'Amount': 'sum'
})

# Add the new Source column value
grouped_data['Source'] = 'total'
grouped_data['Scope'] = 'scope2'

# Combine with the original data
combined_data = pd.concat([tdata, grouped_data], ignore_index=True)

# Save the result to a new CSV file
output_file_path = 'augmented_emissions_total.csv'
combined_data.to_csv(output_file_path, index=False)

t3data = pd.read_csv('scope3_emissions.csv')
t3data['source'] = 'total3'

t3data.to_csv('augmented_scope3.csv', index=False)


file_path = 'augmented_emissions_total.csv'
data = pd.read_csv(file_path)

# Change the lines with column Scope = scope3, the line[source] to 'total3'
data.loc[data['Scope'] == 'scope3', 'Source'] = 'total3'

# Save the modified data to a new CSV file
output_file_path = 'augmented_emissions_total3.csv'
data.to_csv(output_file_path, index=False)

