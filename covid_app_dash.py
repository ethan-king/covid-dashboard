"""
This plotly dash app displays the latest Covid-19 infection numbers.

"""
from datetime import datetime

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)



# COLOR LIST - use this color list to force county cases + death color to match
COLOR_LIST = [
	'#2E91E5', '#E15F99', '#1CA71C', '#FB0D0D', '#DA16FF', '#222A2A', '#B68100', '#750D86', '#EB663B', '#511CFB',
	'#00A08B', '#FB00D1', '#FC0080', '#B2828D', '#6C7C32', '#778AAE', '#862A16', '#A777F1', '#620042', '#1616A7',
	'#DA60CA', '#6C4516', '#0D2A63', '#AF0038'
]
COLOR_LIST_LEN = len(COLOR_LIST)

# read data
dTypes = {'county': str, 'state': str, 'fips': str, 'cases': int, 'deaths': int}
covid = pd.read_csv('https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv', dtype= dTypes, parse_dates=[0])
# covid = covid.sort_values(by=['date', 'fips'], ascending=True)
COVID_DATE_MIN = covid['date'].min()
COVID_DATE_MAX = covid['date'].max()

# clean covid data
covid = covid.loc[~(covid['county']=='Unknown')]
CITIES_NO_COUNTIES = ['New York City', 'Kansas City']


# options for state / county selection TODO: add options for major U.S. cities in multi select dropdown
stateCounty = covid.groupby(['state', 'county']).min().reset_index().drop(columns=['fips', 'cases', 'deaths']).dropna()
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
app.layout = html.Div([
	html.H1('U.S. Counties Covid-19 Tracker'),
	html.Div(
		[
			html.H3('Select your county:', style={'paddingRight': '30px'}),
			dcc.Dropdown(
				id='state_county_picker',
				value=['New York City,New York'],
				options= options,
				multi=True
			)
		], style={'display': 'inline-block', 'verticalAlign': 'top', 'width': '30%'}
	),
	html.Div(
		[
			html.H3('Select a start and end date:'),
			dcc.DatePickerRange(
				id='my_date_picker',
				min_date_allowed=COVID_DATE_MIN,
				max_date_allowed=COVID_DATE_MAX,
				start_date=COVID_DATE_MIN,
				end_date=COVID_DATE_MAX)
		], style={'display': 'inline-block', 'paddingLeft': '30px'}
	),
	html.Div(
		[
			html.Button(
				id='submit-button',
				n_clicks=0,
				children='Submit',
				style={'fontSize':24, 'marginLeft':'30px', 'marginTop': '5px'}
			)
		],
		style={'display': 'inline-block'}
	),
	dcc.Graph(
		id='my_graph',
		figure = {
			'data': [{'x':[1,2], 'y':[3,1]}],
			'layout': {'title':'Default Title'}
		}
	),
])

# TODO: create a density map of covid cases to use for timeseries input selection for counties


# update dashboard
@app.callback(
	Output('my_graph','figure'),
	[Input('submit-button','n_clicks')],
	[
		State('state_county_picker','value'),
		State('my_date_picker', 'start_date'),
		State('my_date_picker', 'end_date')
	]
)
def update_graph(n_clicks, state_county, start_date, end_date):
	start = datetime.strptime(start_date[:10], '%Y-%m-%d')
	end = datetime.strptime(end_date[:10], '%Y-%m-%d')

	#create traces for each item in state_county
	#TODO: add a trendline for the past two weeks
	traces = []
	titleNames= []
	colorTracker = 0
	for item in state_county:
		countyStateList = item.split(',')
		df = covid[(covid['date'] >= start) & (covid['date']<= end)]
		df = df[(df['state'] == countyStateList[1]) & (df['county'] == countyStateList[0])]
		# print(df.head())
		if (countyStateList[0] in CITIES_NO_COUNTIES):
			name = countyStateList[0] + ' - ' + countyStateList[1]
		else:
			name = countyStateList[0] + ' County - ' + countyStateList[1]
		traces.append({'x':df['date'], 'y':df['cases'], 'name': name + ' Cases', 'line': dict(color=COLOR_LIST[colorTracker % COLOR_LIST_LEN])})
		traces.append({'x':df['date'], 'y':df['deaths'], 'name': name + ' Deaths', 'line': dict(color=COLOR_LIST[colorTracker % COLOR_LIST_LEN], dash='dash')})
		titleNames.append(name)
		colorTracker += 1

	fig = {
		'data': traces,
		'layout': {'title': ", ".join(titleNames)}
	}
	return fig

if __name__ == '__main__':
	app.run_server()