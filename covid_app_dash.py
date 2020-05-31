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

app = dash.Dash()

# read data
covid = pd.read_csv('https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv', parse_dates=[0])

# options for state / county selection TODO: add options for major U.S. cities in multi select dropdown
stateCounty = covid.groupby(['state', 'county']).min().reset_index().drop(columns=['fips', 'cases', 'deaths']).dropna()
options = []
for index, row in stateCounty.iterrows():
	#{'Label': 'user sees', 'Value': 'script sees')
	myDict = {}
	myDict['label'] = row['county'] + ' County, ' + row['state']
	myDict['value'] = row['county'] + ',' + row['state']
	options.append(myDict)

# LAYOUT # TODO: Incorporate death numbers in plots
app.layout = html.Div([
	html.H1('U.S. Counties Covid-19 Tracker'),
	html.Div(
		[
			html.H3('Select your county:', style={'paddingRight': '30px'}),
			dcc.Dropdown(
				id='state_county_picker',
				value=['Bergen,New Jersey'],
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
				min_date_allowed=datetime(2000, 1, 1),
				max_date_allowed=datetime.today(),
				start_date=datetime(2020, 3, 1),
				end_date=datetime.today())
		], style={'display': 'inline-block'}
	),
	html.Div(
		[
			html.Button(
				id='submit-button',
				n_clicks=0,
				children='Submit',
				style={'fontSize':24, 'marginLeft':'30px'}
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

# update
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

	#create traces for each ticker in option list
	#TODO: add a trendline for the past two weeks
	traces = []
	titleNames= []
	for item in state_county:
		countyStateList = item.split(',')
		df = covid[(covid['date'] >= start) & (covid['date']<= end)]
		df = df[(df['state'] == countyStateList[1]) & (df['county'] == countyStateList[0])]
		print(df.head())
		name = countyStateList[0] + ' County - ' + countyStateList[1]
		traces.append({'x':df['date'], 'y':df['cases'], 'name': name})
		titleNames.append(name)

	fig = {
		'data': traces,
		'layout': {'title': ", ".join(titleNames)}
	}
	return fig

if __name__ == '__main__':
	app.run_server()