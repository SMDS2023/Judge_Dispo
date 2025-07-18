"""
Judge and Charge Sentencing Dashboard
Analyze sentencing patterns by judge and charge type
"""

import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os

# Initialize the Dash app
app = dash.Dash(__name__, 
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}])

# CRITICAL: Define server for deployment
server = app.server

# App title for browser tab
app.title = "Judge and Charge Sentencing Dashboard"

def load_data():
    """
    Load criminal cases data with focus on sentencing information
    """
    try:
        # Check if file exists
        if not os.path.exists('cases.csv'):
            print("ERROR: cases.csv file not found!")
            return create_sample_data()
        
        print("Found cases.csv file, attempting to load...")
        
        # Try to load the CSV file
        df = pd.read_csv('cases.csv')
        
        print(f"Successfully loaded CSV with shape: {df.shape}")
        print(f"Columns found: {list(df.columns)}")
        
        # Check if we have any data
        if len(df) == 0:
            print("ERROR: CSV file is empty!")
            return create_sample_data()
        
        # Clean up any potential BOM characters from the CSV
        df.columns = df.columns.str.replace('\ufeff', '')
        
        # Convert dates to datetime if columns exist
        date_columns = ['FileDate', 'OffenseDate', 'DispositionDate']
        for col in date_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                    print(f"Successfully converted {col} to datetime")
                except:
                    print(f"Warning: Could not convert {col} to datetime")
        
        # Clean up text fields by stripping whitespace
        text_columns = ['Judge', 'Judge_First_Name', 'Judge_Last_Name', 'ChargeOffenseDescription', 
                       'Statute', 'Statute_Description', 'DispositionDescription', 'Race_Tier_1', 
                       'Gender', 'ConfinementType']
        for col in text_columns:
            if col in df.columns:
                try:
                    df[col] = df[col].astype(str).str.strip()
                    print(f"Cleaned column: {col}")
                except:
                    print(f"Warning: Could not clean column: {col}")
        
        # Process sentencing data - convert to numeric and handle nulls
        # For jail time
        if 'MaxCnfmnt_Days' in df.columns:
            df['Jail_Days'] = pd.to_numeric(df['MaxCnfmnt_Days'], errors='coerce').fillna(0)
        else:
            df['Jail_Days'] = 0
            
        # For probation
        if 'Probation_Days' in df.columns:
            df['Probation_Days_Clean'] = pd.to_numeric(df['Probation_Days'], errors='coerce').fillna(0)
        elif 'Probation_Mths' in df.columns:
            df['Probation_Days_Clean'] = pd.to_numeric(df['Probation_Mths'], errors='coerce').fillna(0) * 30
        elif 'Probation_Yrs' in df.columns:
            df['Probation_Days_Clean'] = pd.to_numeric(df['Probation_Yrs'], errors='coerce').fillna(0) * 365
        else:
            df['Probation_Days_Clean'] = 0
            
        # For community control
        if 'ComCntrl_Days' in df.columns:
            df['CommunityControl_Days'] = pd.to_numeric(df['ComCntrl_Days'], errors='coerce').fillna(0)
        elif 'ComCntrl_Mths' in df.columns:
            df['CommunityControl_Days'] = pd.to_numeric(df['ComCntrl_Mths'], errors='coerce').fillna(0) * 30
        elif 'ComCntrl_Yrs' in df.columns:
            df['CommunityControl_Days'] = pd.to_numeric(df['ComCntrl_Yrs'], errors='coerce').fillna(0) * 365
        else:
            df['CommunityControl_Days'] = 0
            
        # For community service hours
        if 'CommunityService' in df.columns:
            df['CommunityService_Hours'] = pd.to_numeric(df['CommunityService'], errors='coerce').fillna(0)
        else:
            df['CommunityService_Hours'] = 0
        
        # Create a flag for cases with no sentence
        df['Has_Sentence'] = (
            (df['Jail_Days'] > 0) | 
            (df['Probation_Days_Clean'] > 0) | 
            (df['CommunityControl_Days'] > 0) | 
            (df['CommunityService_Hours'] > 0)
        )
        
        # Create full judge name if components exist
        if all(col in df.columns for col in ['Judge_First_Name', 'Judge_Middle_Intial', 'Judge_Last_Name']):
            df['Judge_Full_Name'] = df['Judge_First_Name'] + ' ' + df['Judge_Middle_Intial'].fillna('') + ' ' + df['Judge_Last_Name']
            df['Judge_Full_Name'] = df['Judge_Full_Name'].str.strip()
        elif 'Judge' in df.columns:
            df['Judge_Full_Name'] = df['Judge']
        else:
            df['Judge_Full_Name'] = 'Unknown'
            
        # Clean up judge names
        df['Judge_Full_Name'] = df['Judge_Full_Name'].replace(['nan', 'NaN', ''], 'Unknown')
        
        print(f"Data loaded successfully with {len(df)} rows and {len(df.columns)} columns")
        return df
        
    except Exception as e:
        print(f"ERROR loading data: {e}")
        return create_sample_data()

def create_sample_data():
    """
    Create sample data when real data can't be loaded
    """
    print("Creating sample data...")
    sample_data = {
        'CaseNumber': ['SAMPLE001', 'SAMPLE002', 'SAMPLE003', 'SAMPLE004', 'SAMPLE005'],
        'Judge_Full_Name': ['John Smith', 'Mary Johnson', 'John Smith', 'Robert Brown', 'Mary Johnson'],
        'ChargeOffenseDescription': [
            'POSSESSION OF FIREARM BY CONVICTED FELON', 
            'BATTERY ON LAW ENFORCEMENT OFFICER',
            'DRIVING UNDER THE INFLUENCE',
            'POSSESSION OF CONTROLLED SUBSTANCE',
            'THEFT OF MOTOR VEHICLE'
        ],
        'Statute': ['790.23', '784.07', '316.193', '893.13', '812.014'],
        'Statute_Description': [
            'Firearm Violations',
            'Battery',
            'DUI',
            'Drug Possession',
            'Theft'
        ],
        'Race_Tier_1': ['B', 'W', 'H', 'B', 'W'],
        'Gender': ['M', 'F', 'M', 'F', 'M'],
        'Jail_Days': [365, 0, 30, 180, 0],
        'Probation_Days_Clean': [0, 730, 365, 365, 1095],
        'CommunityControl_Days': [0, 0, 0, 180, 0],
        'CommunityService_Hours': [0, 100, 50, 40, 200],
        'DispositionDescription': ['Adjudicated Guilty', 'Adjudicated Guilty', 'Adjudicated Guilty', 'Adjudicated Guilty', 'Nolle Prosequi'],
        'Has_Sentence': [True, True, True, True, True]
    }
    return pd.DataFrame(sample_data)

# Load the data
print("Starting data load...")
df = load_data()

# Safely get unique values for dropdowns
def safe_get_unique(column_name):
    """Safely get unique values from a column"""
    if column_name in df.columns:
        try:
            unique_vals = [val for val in df[column_name].dropna().unique() if val and str(val) != 'nan']
            return sorted(unique_vals)
        except:
            return []
    return []

# Define the app layout
app.layout = html.Div([
    # Header section
    html.Div([
        html.H1("Judge and Charge Sentencing Dashboard", 
                style={
                    'textAlign': 'center',
                    'color': '#2c3e50',
                    'marginBottom': '10px',
                    'fontFamily': 'Arial, sans-serif'
                }),
        
        html.P(f"Analyzing sentencing patterns across {len(df):,} criminal cases",
               style={
                   'textAlign': 'center',
                   'color': '#7f8c8d',
                   'fontSize': '16px',
                   'marginBottom': '20px'
               })
    ], style={'padding': '15px'}),
    
    # Key metrics row
    html.Div([
        html.Div([
            html.H3(f"{len(df):,}", style={'margin': '0', 'color': '#3498db', 'fontSize': '24px'}),
            html.P("Total Cases", style={'margin': '0', 'fontSize': '12px'})
        ], style={'textAlign': 'center', 'backgroundColor': '#ecf0f1', 'padding': '15px', 'borderRadius': '8px', 'width': '19%', 'display': 'inline-block', 'margin': '0.5%'}),
        
        html.Div([
            html.H3(f"{df['Judge_Full_Name'].nunique()}", style={'margin': '0', 'color': '#e74c3c', 'fontSize': '24px'}),
            html.P("Judges", style={'margin': '0', 'fontSize': '12px'})
        ], style={'textAlign': 'center', 'backgroundColor': '#ecf0f1', 'padding': '15px', 'borderRadius': '8px', 'width': '19%', 'display': 'inline-block', 'margin': '0.5%'}),
        
        html.Div([
            html.H3(f"{len(df[df['Has_Sentence']==True]):,}", style={'margin': '0', 'color': '#27ae60', 'fontSize': '24px'}),
            html.P("Cases with Sentences", style={'margin': '0', 'fontSize': '12px'})
        ], style={'textAlign': 'center', 'backgroundColor': '#ecf0f1', 'padding': '15px', 'borderRadius': '8px', 'width': '19%', 'display': 'inline-block', 'margin': '0.5%'}),
        
        html.Div([
            html.H3(f"{df['Jail_Days'].mean():.1f}", style={'margin': '0', 'color': '#9b59b6', 'fontSize': '24px'}),
            html.P("Avg Jail Days", style={'margin': '0', 'fontSize': '12px'})
        ], style={'textAlign': 'center', 'backgroundColor': '#ecf0f1', 'padding': '15px', 'borderRadius': '8px', 'width': '19%', 'display': 'inline-block', 'margin': '0.5%'}),
        
        html.Div([
            html.H3(f"{df['Probation_Days_Clean'].mean():.1f}", style={'margin': '0', 'color': '#e67e22', 'fontSize': '24px'}),
            html.P("Avg Probation Days", style={'margin': '0', 'fontSize': '12px'})
        ], style={'textAlign': 'center', 'backgroundColor': '#ecf0f1', 'padding': '15px', 'borderRadius': '8px', 'width': '19%', 'display': 'inline-block', 'margin': '0.5%'})
    ], style={'padding': '0 15px', 'marginBottom': '20px'}),
    
    # Filter Controls
    html.Div([
        html.Div([
            html.Div([
                html.Label("Select Judge:", style={'fontWeight': 'bold', 'marginBottom': '5px', 'fontSize': '14px'}),
                dcc.Dropdown(
                    id='judge-filter',
                    options=[{'label': 'All Judges', 'value': 'all'}] + 
                            [{'label': judge, 'value': judge} for judge in safe_get_unique('Judge_Full_Name')],
                    value='all',
                    style={'marginBottom': '10px', 'fontSize': '12px'},
                    searchable=True
                )
            ], style={'width': '32%', 'display': 'inline-block', 'paddingRight': '10px'}),
            
            html.Div([
                html.Label("Select Charge:", style={'fontWeight': 'bold', 'marginBottom': '5px', 'fontSize': '14px'}),
                dcc.Dropdown(
                    id='charge-filter',
                    options=[{'label': 'All Charges', 'value': 'all'}] + 
                            [{'label': charge[:80] + '...' if len(charge) > 80 else charge, 'value': charge} 
                             for charge in safe_get_unique('ChargeOffenseDescription')],
                    value='all',
                    style={'marginBottom': '10px', 'fontSize': '12px'},
                    searchable=True
                )
            ], style={'width': '32%', 'display': 'inline-block', 'paddingLeft': '5px', 'paddingRight': '5px'}),
            
            html.Div([
                html.Label("Sentence Filter:", style={'fontWeight': 'bold', 'marginBottom': '5px', 'fontSize': '14px'}),
                dcc.Dropdown(
                    id='sentence-filter',
                    options=[
                        {'label': 'All Cases', 'value': 'all'},
                        {'label': 'With Sentence Only', 'value': 'with_sentence'},
                        {'label': 'No Sentence Only', 'value': 'no_sentence'}
                    ],
                    value='all',
                    style={'marginBottom': '10px', 'fontSize': '12px'}
                )
            ], style={'width': '32%', 'display': 'inline-block', 'paddingLeft': '10px'})
        ])
    ], style={'padding': '0 20px', 'marginBottom': '20px'}),
    
    # Summary Statistics Section
    html.Div([
        html.H3("Sentencing Summary", 
               style={'textAlign': 'center', 'marginBottom': '15px', 'color': '#2c3e50'}),
        html.Div(id='summary-stats', style={'padding': '10px'})
    ], style={'padding': '15px', 'backgroundColor': '#f8f9fa', 'marginBottom': '20px'}),
    
    # Charts Section
    html.Div([
        # Sentencing distribution charts
        html.Div([
            dcc.Graph(id='jail-distribution', style={'height': '400px'})
        ], style={'width': '50%', 'display': 'inline-block', 'padding': '10px'}),
        
        html.Div([
            dcc.Graph(id='probation-distribution', style={'height': '400px'})
        ], style={'width': '50%', 'display': 'inline-block', 'padding': '10px'}),
        
        # Additional charts
        html.Div([
            dcc.Graph(id='community-control-distribution', style={'height': '400px'})
        ], style={'width': '50%', 'display': 'inline-block', 'padding': '10px'}),
        
        html.Div([
            dcc.Graph(id='community-service-distribution', style={'height': '400px'})
        ], style={'width': '50%', 'display': 'inline-block', 'padding': '10px'}),
        
        # Comparative chart
        html.Div([
            dcc.Graph(id='sentence-comparison', style={'height': '500px'})
        ], style={'width': '100%', 'padding': '10px'})
    ]),
    
    # Detailed Sentencing Table
    html.Div([
        html.H3("Detailed Sentencing Records", 
               style={'textAlign': 'center', 'marginBottom': '15px', 'color': '#2c3e50'}),
        html.P("Click column headers to sort. Use filter boxes below headers to search.",
               style={'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '14px', 'marginBottom': '10px'}),
        dash_table.DataTable(
            id='sentencing-table',
            columns=[
                {"name": "Judge", "id": "Judge_Full_Name"},
                {"name": "Charge", "id": "ChargeOffenseDescription"},
                {"name": "Statute", "id": "Statute"},
                {"name": "Jail Days", "id": "Jail_Days", "type": "numeric"},
                {"name": "Probation Days", "id": "Probation_Days_Clean", "type": "numeric"},
                {"name": "Comm. Control Days", "id": "CommunityControl_Days", "type": "numeric"},
                {"name": "Comm. Service Hours", "id": "CommunityService_Hours", "type": "numeric"},
                {"name": "Race", "id": "Race_Tier_1"},
                {"name": "Has Sentence", "id": "Has_Sentence"}
            ],
            data=[],
            style_cell={
                'textAlign': 'left', 
                'padding': '10px', 
                'fontSize': '12px',
                'whiteSpace': 'normal',
                'height': 'auto'
            },
            style_header={
                'backgroundColor': '#3498db', 
                'color': 'white', 
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_data={
                'backgroundColor': '#ecf0f1'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'white',
                },
                {
                    'if': {'column_id': 'Has_Sentence', 'filter_query': '{Has_Sentence} = False'},
                    'backgroundColor': '#ffcccc',
                    'color': 'black',
                }
            ],
            page_size=50,
            sort_action="native",
            filter_action="native",
            export_format="csv"
        )
    ], style={'padding': '15px'})
], style={'backgroundColor': '#f8f9fa', 'minHeight': '100vh'})

# Callback for updating all components
@app.callback(
    [Output('summary-stats', 'children'),
     Output('jail-distribution', 'figure'),
     Output('probation-distribution', 'figure'),
     Output('community-control-distribution', 'figure'),
     Output('community-service-distribution', 'figure'),
     Output('sentence-comparison', 'figure'),
     Output('sentencing-table', 'data')],
    [Input('judge-filter', 'value'),
     Input('charge-filter', 'value'),
     Input('sentence-filter', 'value')]
)
def update_dashboard(selected_judge, selected_charge, selected_sentence):
    """
    Update all dashboard components based on filter selections
    """
    # Filter data based on selections
    filtered_df = df.copy()
    
    # Apply judge filter
    if selected_judge != 'all':
        filtered_df = filtered_df[filtered_df['Judge_Full_Name'] == selected_judge]
    
    # Apply charge filter
    if selected_charge != 'all':
        filtered_df = filtered_df[filtered_df['ChargeOffenseDescription'] == selected_charge]
    
    # Apply sentence filter
    if selected_sentence == 'with_sentence':
        filtered_df = filtered_df[filtered_df['Has_Sentence'] == True]
    elif selected_sentence == 'no_sentence':
        filtered_df = filtered_df[filtered_df['Has_Sentence'] == False]
    
    # Create summary statistics
    summary_stats = html.Div([
        html.Div([
            html.P(f"Cases in View: {len(filtered_df):,}", style={'margin': '5px'}),
            html.P(f"Cases with Sentences: {len(filtered_df[filtered_df['Has_Sentence']==True]):,} ({len(filtered_df[filtered_df['Has_Sentence']==True])/len(filtered_df)*100:.1f}%)" if len(filtered_df) > 0 else "No data", 
                   style={'margin': '5px'}),
            html.P(f"Average Jail Time: {filtered_df[filtered_df['Jail_Days']>0]['Jail_Days'].mean():.1f} days" if len(filtered_df[filtered_df['Jail_Days']>0]) > 0 else "No jail sentences", 
                   style={'margin': '5px'}),
            html.P(f"Average Probation: {filtered_df[filtered_df['Probation_Days_Clean']>0]['Probation_Days_Clean'].mean():.1f} days" if len(filtered_df[filtered_df['Probation_Days_Clean']>0]) > 0 else "No probation sentences", 
                   style={'margin': '5px'})
        ], style={'textAlign': 'center'})
    ])
    
    # Create jail time distribution
    jail_fig = go.Figure()
    jail_data = filtered_df[filtered_df['Jail_Days'] > 0]['Jail_Days']
    if len(jail_data) > 0:
        jail_fig.add_trace(go.Histogram(
            x=jail_data,
            nbinsx=30,
            name='Jail Days',
            marker_color='#e74c3c'
        ))
        jail_fig.update_layout(
            title=f"Jail Time Distribution (n={len(jail_data):,})",
            xaxis_title="Days in Jail",
            yaxis_title="Number of Cases",
            showlegend=False
        )
    else:
        jail_fig.add_annotation(text="No jail sentences in filtered data", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        jail_fig.update_layout(title="Jail Time Distribution")
    
    # Create probation distribution
    probation_fig = go.Figure()
    probation_data = filtered_df[filtered_df['Probation_Days_Clean'] > 0]['Probation_Days_Clean']
    if len(probation_data) > 0:
        probation_fig.add_trace(go.Histogram(
            x=probation_data,
            nbinsx=30,
            name='Probation Days',
            marker_color='#3498db'
        ))
        probation_fig.update_layout(
            title=f"Probation Time Distribution (n={len(probation_data):,})",
            xaxis_title="Days on Probation",
            yaxis_title="Number of Cases",
            showlegend=False
        )
    else:
        probation_fig.add_annotation(text="No probation sentences in filtered data", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        probation_fig.update_layout(title="Probation Time Distribution")
    
    # Create community control distribution
    cc_fig = go.Figure()
    cc_data = filtered_df[filtered_df['CommunityControl_Days'] > 0]['CommunityControl_Days']
    if len(cc_data) > 0:
        cc_fig.add_trace(go.Histogram(
            x=cc_data,
            nbinsx=20,
            name='Community Control Days',
            marker_color='#27ae60'
        ))
        cc_fig.update_layout(
            title=f"Community Control Distribution (n={len(cc_data):,})",
            xaxis_title="Days on Community Control",
            yaxis_title="Number of Cases",
            showlegend=False
        )
    else:
        cc_fig.add_annotation(text="No community control sentences in filtered data", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        cc_fig.update_layout(title="Community Control Distribution")
    
    # Create community service distribution
    cs_fig = go.Figure()
    cs_data = filtered_df[filtered_df['CommunityService_Hours'] > 0]['CommunityService_Hours']
    if len(cs_data) > 0:
        cs_fig.add_trace(go.Histogram(
            x=cs_data,
            nbinsx=20,
            name='Community Service Hours',
            marker_color='#9b59b6'
        ))
        cs_fig.update_layout(
            title=f"Community Service Distribution (n={len(cs_data):,})",
            xaxis_title="Community Service Hours",
            yaxis_title="Number of Cases",
            showlegend=False
        )
    else:
        cs_fig.add_annotation(text="No community service sentences in filtered data", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        cs_fig.update_layout(title="Community Service Distribution")
    
    # Create comparison chart
    if selected_judge != 'all' and len(filtered_df) > 0:
        # Show charge breakdown for selected judge
        charge_summary = filtered_df.groupby('ChargeOffenseDescription').agg({
            'Jail_Days': 'mean',
            'Probation_Days_Clean': 'mean',
            'CommunityControl_Days': 'mean',
            'CommunityService_Hours': 'mean',
            'CaseNumber': 'count'
        }).round(1).reset_index()
        charge_summary = charge_summary.sort_values('CaseNumber', ascending=False).head(15)
        
        comparison_fig = go.Figure()
        comparison_fig.add_trace(go.Bar(name='Jail Days', x=charge_summary['ChargeOffenseDescription'], y=charge_summary['Jail_Days'], marker_color='#e74c3c'))
        comparison_fig.add_trace(go.Bar(name='Probation Days', x=charge_summary['ChargeOffenseDescription'], y=charge_summary['Probation_Days_Clean'], marker_color='#3498db'))
        comparison_fig.add_trace(go.Bar(name='Community Control Days', x=charge_summary['ChargeOffenseDescription'], y=charge_summary['CommunityControl_Days'], marker_color='#27ae60'))
        
        comparison_fig.update_layout(
            title=f"Average Sentences by Charge for {selected_judge}",
            xaxis_title="Charge",
            yaxis_title="Average Days",
            barmode='group',
            xaxis_tickangle=-45,
            height=500
        )
    elif selected_charge != 'all' and len(filtered_df) > 0:
        # Show judge breakdown for selected charge
        judge_summary = filtered_df.groupby('Judge_Full_Name').agg({
            'Jail_Days': 'mean',
            'Probation_Days_Clean': 'mean',
            'CommunityControl_Days': 'mean',
            'CommunityService_Hours': 'mean',
            'CaseNumber': 'count'
        }).round(1).reset_index()
        judge_summary = judge_summary.sort_values('CaseNumber', ascending=False).head(15)
        
        comparison_fig = go.Figure()
        comparison_fig.add_trace(go.Bar(name='Jail Days', x=judge_summary['Judge_Full_Name'], y=judge_summary['Jail_Days'], marker_color='#e74c3c'))
        comparison_fig.add_trace(go.Bar(name='Probation Days', x=judge_summary['Judge_Full_Name'], y=judge_summary['Probation_Days_Clean'], marker_color='#3498db'))
        comparison_fig.add_trace(go.Bar(name='Community Control Days', x=judge_summary['Judge_Full_Name'], y=judge_summary['CommunityControl_Days'], marker_color='#27ae60'))
        
        comparison_fig.update_layout(
            title=f"Average Sentences by Judge for '{selected_charge[:50]}...'",
            xaxis_title="Judge",
            yaxis_title="Average Days",
            barmode='group',
            xaxis_tickangle=-45,
            height=500
        )
    else:
        # Show top judges by case count
        if len(filtered_df) > 0:
            judge_cases = filtered_df['Judge_Full_Name'].value_counts().head(20)
            comparison_fig = px.bar(
                x=judge_cases.index,
                y=judge_cases.values,
                title="Top 20 Judges by Case Count",
                labels={'x': 'Judge', 'y': 'Number of Cases'},
                color=judge_cases.values,
                color_continuous_scale='Blues'
            )
            comparison_fig.update_layout(xaxis_tickangle=-45, height=500, showlegend=False)
        else:
            comparison_fig = go.Figure()
            comparison_fig.add_annotation(text="No data to display", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            comparison_fig.update_layout(title="Sentence Comparison")
    
    # Prepare table data
    table_columns = ['Judge_Full_Name', 'ChargeOffenseDescription', 'Statute', 'Jail_Days', 
                    'Probation_Days_Clean', 'CommunityControl_Days', 'CommunityService_Hours', 
                    'Race_Tier_1', 'Has_Sentence']
    
    available_columns = [col for col in table_columns if col in filtered_df.columns]
    
    if available_columns and len(filtered_df) > 0:
        table_data = filtered_df[available_columns].round({'Jail_Days': 0, 'Probation_Days_Clean': 0, 
                                                          'CommunityControl_Days': 0, 'CommunityService_Hours': 0}).to_dict('records')
    else:
        table_data = []
    
    return (summary_stats, jail_fig, probation_fig, cc_fig, cs_fig, comparison_fig, table_data)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=False)
