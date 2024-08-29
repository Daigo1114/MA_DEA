from graphviz import Digraph
import dash
from dash import html, dcc
import base64
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
import json

with open('data.pickle', 'rb') as f:
    single_emissions, multiple_emissions, times, event_dt, earliest_timestamp, latest_timestamp = pickle.load(f)

#print(single_emissions)
#print(multiple_emissions)
#print(event_dt)
activities = ["Deal with Orders", "Communicate with Warehouse", "Pack Orders", "Prepare to Send Orders", "Deliver Orders", "Close Orders"]
time_acceleration_factor = 60   # 1 hour per second
extra_emissions = {"Waste Emission": 0.000, "Delivery Emission": 0.000, "Commuting Emission": 0.000}
order_ids = list(single_emissions.keys())
default_order_id = order_ids[0]
start_time, end_time = [pd.to_datetime(t) for t in times[default_order_id]]

for order_id, t in event_dt.items():
    print(t)
    t_list = list(t)
    del t_list[4]
    del t_list[7]
    event_dt[order_id] = t_list

def interpolate_color(value, min_value, max_value):
    # Normalize value
    norm_value = (value - min_value) / (max_value - min_value)
    # Interpolate between green (low) and red (high)
    return plt.cm.RdYlGn_r(norm_value)

def create_default_pie():
    scope_2 = []
    scope_3 = []
    labels_scope_2 = []
    labels_scope_3 = []
    order_id = ''
    for order_id, stages in single_emissions.items():
        order_id = order_id
        print(order_id)
        for stage, stage_info in stages.items():
            if stage == 'commuting' or stage == 'waste' or stage == 'delivery':
                labels_scope_3.append(stage)
                scope_3.append(stage_info['co2'])
                continue
            scope_2.append(stage_info['emissions']['co2']['equipment'])
            scope_2.append(stage_info['emissions']['co2']['electricity'])
            labels_1 = f"{stage}_equipment"
            labels_2 = f"{stage}_electricity"
            labels_scope_2.append(labels_1)
            labels_scope_2.append(labels_2)

        break
    fig_scope2 = go.Figure(data=[go.Pie(labels=labels_scope_2, values=scope_2, hole=0.3)])
    fig_scope3 = go.Figure(data=[go.Pie(labels=labels_scope_3, values=scope_3, hole=0.3)])
    bar_scope2 = go.Figure(data=[go.Bar(x=labels_scope_2, y=scope_2)])
    bar_scope3 = go.Figure(data=[go.Bar(x=labels_scope_3, y=scope_3)])
    return fig_scope2, fig_scope3, bar_scope2, bar_scope3

fig_scope2, fig_scope3, bar_scope2, bar_scope3 = create_default_pie()

def create_pie(order_id):
    if order_id not in single_emissions:
        return None, None, None, None  # or handle the error appropriately if the order_id is not found

    scope_2 = []
    scope_3 = []
    labels_scope_2 = []
    labels_scope_3 = []

    stages = single_emissions[order_id]
    for stage, stage_info in stages.items():
        if stage in ['commuting', 'waste', 'delivery']:
            labels_scope_3.append(stage)
            scope_3.append(stage_info['co2'])
        else:
            scope_2.append(stage_info['emissions']['co2']['equipment'])
            scope_2.append(stage_info['emissions']['co2']['electricity'])
            labels_1 = f"{stage}_equipment"
            labels_2 = f"{stage}_electricity"
            labels_scope_2.append(labels_1)
            labels_scope_2.append(labels_2)

    # Create the Pie chart for Scope 2 emissions
    fig_scope2 = go.Figure(data=[go.Pie(labels=labels_scope_2, values=scope_2, hole=0.3)])
    # Create the Pie chart for Scope 3 emissions
    fig_scope3 = go.Figure(data=[go.Pie(labels=labels_scope_3, values=scope_3, hole=0.3)])

    # Optionally return bar charts if needed
    bar_scope2 = go.Figure(data=[go.Bar(x=labels_scope_2, y=scope_2)])
    bar_scope3 = go.Figure(data=[go.Bar(x=labels_scope_3, y=scope_3)])

    return fig_scope2, fig_scope3, bar_scope2, bar_scope3


def create_flowchart(emissions, rankdir='LR', extra_activities={2: "Waste Emission", 4: "Delivery Emission", 0: "Commuting Emission"}, extra_emissions=extra_emissions):
    dot = Digraph()
    dot.attr(rankdir=rankdir)
    
    relevant_emissions = emissions[:6]
    '''
    if 'Waste Emission' in extra_emissions:
        relevant_emissions.append(extra_emissions['Waste Emission'])
    if 'Delivery Emission' in extra_emissions:
        relevant_emissions.append(extra_emissions['Delivery Emission'])
    if 'Commuting Emission' in extra_emissions:
        relevant_emissions.append(extra_emissions['Commuting Emission'])
    '''
    

    max_emissions = max(relevant_emissions) + 4
    min_emissions = min(min(relevant_emissions), 0)

    # Create nodes with emissions as labels
    for i, activity in enumerate(activities):
        color = interpolate_color(emissions[i], min_emissions, max_emissions)
        hex_color = '#{:02x}{:02x}{:02x}'.format(int(color[0]*255), int(color[1]*255), int(color[2]*255))
        dot.node(activity, f"{activity}\nGHG: {emissions[i]:.3f} kg CO2e", style='filled, rounded', fillcolor=hex_color, shape='rect', fontcolor='black')

    # Connect the activities
    for i in range(len(activities) - 1):
        dot.edge(activities[i], activities[i + 1])

    if extra_activities:
        for key, value in extra_activities.items():
            if key < len(activities):  # Ensure the parent index exists
                # Fetch extra emission value or display "Data not available"
                # Create an extra node
                print(key)
                extra_emission_value = extra_emissions.get(value, 0.000)
                extra_color = interpolate_color(extra_emission_value, min_emissions, max_emissions)
                extra_hex_color = '#{:02x}{:02x}{:02x}'.format(int(extra_color[0]*255), int(extra_color[1]*255), int(extra_color[2]*255))
                extra_emission_label = f"{extra_emission_value:.3f} kg CO2e"  # Properly format the number here
                if key == 0:
                    dot.node(value, f"{value}\nGHG: {extra_emission_label}", style='filled', fillcolor="#FF0000", shape='rect', fontcolor='black')
                else:
                    dot.node(value, f"{value}\nGHG: {extra_emission_label}", style='filled', fillcolor=extra_hex_color, shape='rect', fontcolor='black')
                # Connect the parent node to the extra node directly below it
                with dot.subgraph() as s:
                    s.attr(rank='same')  # This forces the child node to be directly below the parent
                    if key == 0:
                        s.edge(activities[key], value, style="invis")
                    else:
                        s.edge(activities[key], value)

    # Convert to image
    return dot.pipe(format='png')

app = dash.Dash(__name__)

initial_emissions = [0] * len(activities)
initial_image = create_flowchart(initial_emissions)
encoded_image = base64.b64encode(initial_image).decode('ascii')

# App layout
app.layout = html.Div([
    dcc.Dropdown(
        id='order-dropdown',
        options=[{'label': oid, 'value': oid} for oid in order_ids],
        value=order_ids[0]  # Set default value to the first order ID
    ),
    html.Div(id='hidden-div', children=order_ids[0], style={'display': 'none'}),
    html.Img(id='flowchart-image', src='data:image/png;base64,{}'.format(encoded_image), style={'marginTop': '20px'}),
    html.Img(src='/assets/colorscale.png', style={'height':'70px', 'width':'auto', 'display':'block', 'margin-left':'auto', 'margin-right':'auto','marginTop': '10px'}),
    html.Div(id='simulation-time', style={  # Simulation time div
            'fontSize': '20px', 
            'textAlign': 'right', 
            'margin': '10px', 
            'flex': 'none'
    }),
    html.Div([
        html.Div([
            dcc.Graph(id='pie-chart-scope2', figure=fig_scope2, style={'width': '50%', 'display': 'inline-block'}),
            dcc.Graph(id='pie-chart-scope3', figure=fig_scope3, style={'width': '50%', 'display': 'inline-block'}),
        ], style={'display': 'flex', 'margin-bottom': '10px'}),
        html.Div([
            dcc.Graph(id='bar-chart-scope2', figure=bar_scope2, style={'width': '50%', 'display': 'inline-block'}),
            dcc.Graph(id='bar-chart-scope3', figure=bar_scope3, style={'width': '50%', 'display': 'inline-block'}),
        ], style={'display': 'flex'})
    ], style={'margin': '20px', 'padding': '20px', 'border': '1px solid #ddd', 'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'}),
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0)  # 1-second interval in real-time
])

@app.callback(
    [Output('pie-chart-scope2', 'figure'),
     Output('pie-chart-scope3', 'figure'),
     Output('bar-chart-scope2', 'figure'),
     Output('bar-chart-scope3', 'figure')],
    [Input('order-dropdown', 'value')]
)

def update_charts(order_id):
    # Retrieve pie chart data
    pie_scope2, pie_scope3, bar_scope2, bar_scope3 = create_pie(order_id)
    return pie_scope2, pie_scope3, bar_scope2, bar_scope3

@app.callback(
    Output('interval-component', 'n_intervals'),
    [Input('order-dropdown', 'value')],
    [State('hidden-div', 'children')]
)
def reset_interval_on_order_change(new_order_id, current_order_id):
    if new_order_id != current_order_id:
        return 0  # Reset the interval count if the order ID changes
    raise dash.exceptions.PreventUpdate  # Do nothing if the order ID hasn't changed

@app.callback(
    [Output('simulation-time', 'children'),
     Output('hidden-div', 'children'),
     Output('flowchart-image', 'src')],
    [Input('interval-component', 'n_intervals')],
    [State('order-dropdown', 'value')]
)
def update_simulation_time(n_intervals, order_id):

    if order_id is None:
        raise dash.exceptions.PreventUpdate



    start_time, end_time = [pd.to_datetime(t) for t in times[order_id]]
    time_step = timedelta(minutes=1200 * (n_intervals - 1))
    current_time = max(min(start_time + time_step, end_time), start_time)

    display_time = f"Simulation Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"

    if current_time >= end_time:
        new_emissions = [0] * len(activities)
        extra_emission = {"Waste Emission": 0.000, "Delivery Emission": 0.000, "Commuting Emission": 0.000}
        
        stages = single_emissions.get(order_id, {})
        i = 0
        for stage, stage_info in stages.items():
            if i <= 5:
                new_emissions[i] = stage_info['emissions']['co2']['equipment']
            elif i == 6:
                commuting_emission = stage_info['co2']
            elif i == 7:
                waste_emission = stage_info['co2']
            elif i == 8:
                delivery_emission = stage_info['co2']
            i += 1  
        
        extra_emission = {"Commuting Emission":commuting_emission, "Waste Emission":waste_emission, "Delivery Emission":delivery_emission}
        #print(new_emissions, extra_emission)
        new_image = create_flowchart(new_emissions, extra_emissions=extra_emission)
        new_encoded_image = base64.b64encode(new_image).decode('ascii')

        return display_time, order_id, 'data:image/png;base64,{}'.format(new_encoded_image)
    
    simulation_duration = (end_time - start_time).total_seconds()
    days_duration = (end_time.date() - start_time.date()).days + 1

    emissions_data = single_emissions.get(order_id, {})
    stages = event_dt.get(order_id, [])    
    for stage, stage_info in emissions_data.items():
        if stage == 'commuting':
            co2_em = stage_info['co2']
            unit_cmt = co2_em / days_duration
            break
        stage_start, stage_end = stage_info['time_between']
        stage_start = pd.to_datetime(stage_start)
        stage_end = pd.to_datetime(stage_end)
        stage_duration = (stage_end - stage_start).total_seconds() / 60  # duration in minutes
        co2_equipment = stage_info['emissions']['co2']['equipment']
        emission_rate = co2_equipment / stage_duration
    
    emissions_rates = [emission_rate] * len(activities)

    print(emissions_rates)
    new_emissions = [0] * len(activities)
    extra_emission = {"Waste Emission": 0.0, "Delivery Emission": 0.0, "Commuting Emission": 0.0}
    days_passed = (current_time.date() - start_time.date()).days + 1
    comt_emi = unit_cmt * days_passed
    extra_emission = {"Commuting Emission": comt_emi}

    current_stage_index = None
    for i, stage_time in enumerate(stages[:-1]):  # Iterate over stages, excluding the last one
        stage_start = pd.to_datetime(stage_time)
        stage_end = pd.to_datetime(stages[i+1])
        if stage_start <= current_time <= stage_end:
            current_stage_index = i
            break

    if current_stage_index is not None:
        stage_start = pd.to_datetime(stages[current_stage_index])
        stage_end = pd.to_datetime(stages[current_stage_index+1])
        emission_rate = emissions_rates[current_stage_index]
        stage_duration = (stage_end - stage_start).total_seconds() / 60
        #if stage_start <= current_time <= stage_end:
        print(current_stage_index)
        for j in range(current_stage_index):
            previous_stage_start = pd.to_datetime(stages[j])
            previous_stage_end = pd.to_datetime(stages[j+1])
            previous_stage_duration = (previous_stage_end - previous_stage_start).total_seconds() / 60
            #print(current_stage_index, j, new_emissions[j])
            if new_emissions[j] == 0:
                new_emissions[j] = previous_stage_duration * emissions_rates[j]
            else:
                new_emissions[j] += previous_stage_duration * emissions_rates[j]

        stage_duration = (current_time - stage_start).total_seconds() / 60
        emission_rate = emissions_rates[current_stage_index]  # Use the emission rate for the current stage
        new_emissions[current_stage_index] += stage_duration * emission_rate
        #print(new_emissions)
            
        if 'Waste Emission' in extra_emissions:
            # Calculate emissions for Waste Emission if the current time is beyond its defined start time
            if current_stage_index >= 3:
                extra_emission = {"Waste Emission":single_emissions[order_id]['waste']['co2'], "Commuting Emission": comt_emi}
            
        if 'Delivery Emission' in extra_emissions:
            # Calculate emissions for Delivery Emission similarly
            if current_stage_index >= 5:
                extra_emission = {"Waste Emission":single_emissions[order_id]['waste']['co2'], "Delivery Emission":single_emissions[order_id]['delivery']['co2'], "Commuting Emission": comt_emi}
    
    new_image = create_flowchart(new_emissions, extra_emissions=extra_emission)
    new_encoded_image = base64.b64encode(new_image).decode('ascii')

    return display_time, order_id, 'data:image/png;base64,{}'.format(new_encoded_image)





if __name__ == '__main__':
    app.run_server(debug=True)