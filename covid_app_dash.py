"""
This plotly dash app displays the latest Covid-19 infection numbers by U.S. county.

"""
from datetime import datetime

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import pandas as pd

from stateCounties import stateCountyData

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MATERIA])
app.title = 'U.S. Counties Covid-19 Dashboard'

server = app.server

# COLOR LIST - use this color list to force county cases + death color to match
COLOR_LIST = [
	'#2E91E5', '#E15F99', '#1CA71C', '#FB0D0D', '#DA16FF', '#222A2A', '#B68100', '#750D86', '#EB663B', '#511CFB',
	'#00A08B', '#FB00D1', '#FC0080', '#B2828D', '#6C7C32', '#778AAE', '#862A16', '#A777F1', '#620042', '#1616A7',
	'#DA60CA', '#6C4516', '#0D2A63', '#AF0038'
]
COLOR_LIST_LEN = len(COLOR_LIST)

# read data
COVID_DTYPES = {'county': str, 'state': str, 'fips': str, 'cases': int, 'deaths': int}
NYT_REPO = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'

def readToDf(url, dTypes):
	'''
	read NY Times covid-19 county data into a dataframe and clear unknown counties
	:param url: string - github repo url
	:param dTypes: dict key = col, val = dtype
	:return: cleaned NYT dataframe
	'''
	df = pd.read_csv(url, dtype=dTypes, parse_dates=[0])
	df = df.loc[~(df['county']=='Unknown')]
	return df

covid = readToDf(NYT_REPO,COVID_DTYPES)


# multidropdown options for state / county selection
CITIES_NO_COUNTIES = ['New York City', 'Kansas City']

stateCounty = pd.read_json(stateCountyData, dtype=COVID_DTYPES)
options = []
for index, row in stateCounty.iterrows():
	#{'Label': 'user sees', 'Value': 'script sees')
	myDict = {}
	if (row['county'] in CITIES_NO_COUNTIES):
		myDict['label'] = row['county'] + ', ' + row['state']
	else:
		myDict['label'] = row['county'] + ' County, ' + row['state']
	myDict['value'] = row['county'] + ',' + row['state']
	options.append(myDict)

# add options for us cities: 'label': 'city, state', 'value': 'county, state'
table = pd.read_html('https://en.wikipedia.org/wiki/List_of_the_most_populous_counties_in_the_United_States')[0].dropna()
table = table[~(table['County seat'].str.contains('NYC'))]
table = table[~(table['County seat'].str.contains('Kansas City'))]
for index, row in table.iterrows():
	myDict = {}
	myDict['label'] = row['County seat'] + ', ' + row['State']
	myDict['value'] = row['County'] + ',' + row['State']
	options.append(myDict)

# LAYOUT
app.layout = html.Div(
	[
		dbc.NavbarSimple(
			children=[
				html.P('')
			],
			brand="U.S. Counties Covid-19 Dashboard",
			# style={'padding-left': 30},
			# fluid=False,
			color='primary',
			dark=True,
		),
		html.Div(
			[
				html.Div(
					[
						html.H3('County and State selection:', style={'paddingRight': '30px'}),
						dcc.Dropdown(
							id='state_county_picker',
							value=['Bergen,New Jersey', 'Hudson,New Jersey', 'Essex,New Jersey', 'Passaic,New Jersey',
								'Middlesex,New Jersey'],
							options= options,
							multi=True
						)
					], style={'display': 'inline-block', 'verticalAlign': 'top', 'width': '35%'}
				),
				html.Div(
					[
						html.H3('Select a start and end date:'),
						dcc.DatePickerRange(
							id='my_date_picker',
							min_date_allowed=datetime.strptime('2020-01-21', '%Y-%m-%d'),
							max_date_allowed=datetime.today(),
							start_date=datetime.strptime('2020-01-21', '%Y-%m-%d'),
							end_date=datetime.today())
					], style={'display': 'inline-block', 'paddingLeft': '30px'}
				),
				html.Div(
					[
						html.Button(
							id='submit-button',
							n_clicks=0,
							children='Submit',
							#style={'fontSize':24, 'marginLeft':'30px', 'marginTop': '5px'}
						)
					],
					style={'display': 'inline-block', 'paddingLeft': '30px'}
				),
				html.Div(
					[
						dcc.Graph(
							id='my_graph',
							figure = {
								'data': [{'x':[1,2], 'y':[3,1]}],
								'layout': {'title':'Default Title'}
							}
						),
					],
					style={'height':'45%'}
				),
				html.Div(
					[
						dcc.Graph(
							id='mortality_graph',
							figure= {
								'data': [{'x':[1,2], 'y':[3,1]}],
								'layout': {'title':'Default Title'}
							}
						),
					],
					style={'height':'15%'}
				),
				html.P(
					children='Last data refresh:',
					id='data-last-refresh'
				),


				# Footer
				html.P('email: ',style={'display':'inline-block'}),
				html.A('king.ethan@gmail.com', href='mailto:king.ethan@gmail.com', style={'display':'inline-block'}),
				html.P('This dashboard uses data from The New York Times, based on reports from state and local health agencies.'),

				# Hidden components
				dcc.Interval(
					id='interval-component',
					interval= 86400000,
					n_intervals=0
				),
				html.Div(
					id='saved-data',
					style={'display':'none'},
					children=''
				)

			], style={'paddingLeft': '10px', 'paddingTop': '10px'}
		),
	]
)

# refresh data daily
@app.callback(Output('data-last-refresh', 'children'), [Input('interval-component', 'n_intervals')])
def refresh_covid_data(n):
	global covid
	covid = readToDf(NYT_REPO,COVID_DTYPES)
	now = datetime.now().strftime('%Y-%m-%d %I:%M:%S %p EDT')
	status = f'Last data refresh: {now}'
	return status


# update dashboard
@app.callback(
	[
		Output('my_graph','figure'),
		Output('mortality_graph', 'figure')
	],
	[Input('submit-button','n_clicks')],
	[
		State('state_county_picker','value'),
		State('my_date_picker', 'start_date'),
		State('my_date_picker', 'end_date'),
		State('saved-data', 'children')
	]
)
def update_graph(n_clicks, state_county, start_date, end_date, saved_df_json):
	start = datetime.strptime(start_date[:10], '%Y-%m-%d')
	end = datetime.strptime(end_date[:10], '%Y-%m-%d')
	# read saved df json
	# covid = pd.read_json(saved_df_json, dtype=COVID_DTYPES)
	#create traces for each item in state_county
	#TODO: add a trendline for the past two weeks
	traces = []
	tracesMortality=[]
	tracesDelta = []
	titleNames= []
	colorTracker = 0
	for item in state_county:
		countyStateList = item.split(',')
		df = covid[(covid['date'] >= start) & (covid['date']<= end)]
		df = df[(df['state'] == countyStateList[1]) & (df['county'] == countyStateList[0])]
		df['mortality rate'] = df['deaths'] / df['cases']
		# print(df.head())
		if (countyStateList[0] in CITIES_NO_COUNTIES):
			name = countyStateList[0] + ' - ' + countyStateList[1]
		else:
			name = countyStateList[0] + ' County - ' + countyStateList[1]
		traces.append({'x':df['date'], 'y':df['cases'], 'name': name + ' Cases', 'line': dict(color=COLOR_LIST[colorTracker % COLOR_LIST_LEN])})
		traces.append({'x':df['date'], 'y':df['deaths'], 'name': name + ' Deaths', 'line': dict(color=COLOR_LIST[colorTracker % COLOR_LIST_LEN], dash='dash')})
		tracesMortality.append({'x':df['date'], 'y':df['mortality rate'], 'name': name + ' Mortality', 'line': dict(color=COLOR_LIST[colorTracker % COLOR_LIST_LEN])})
		titleNames.append(name)
		colorTracker += 1

	fig = {
		'data': traces,
		'layout': {'title': "Cases and Deaths", 'height': 400}
	}

	figMortality = {
		'data': tracesMortality,
		'layout': {'title': "Mortality Rate", 'showlegend':True, 'height': 275}

	}
	return fig, figMortality



if __name__ == '__main__':
	app.run_server()