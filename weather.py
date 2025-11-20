from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timezone

load_dotenv()
API_KEY = os.getenv("WEATHER_API_KEY")
LOCATION = "BOSTON,MA"

def get_weatherapi_forecast():
	url = "http://api.weatherapi.com/v1/forecast.json"
	params = {
		"key": API_KEY,
		"q": LOCATION,
		"days": 2,
		"aqi": "no",
		"alerts": "no"
	}
	resp = requests.get(url, params=params)
	resp.raise_for_status()
	return resp.json()

def parse_weather():
	json_data = get_weatherapi_forecast()

	forecast = json_data["forecast"]

	today = forecast["forecastday"][0]

	rain = today['day']['daily_chance_of_rain']
	current_hour = datetime.now(timezone.utc).hour
	current_temp = today["hour"][current_hour]["temp_c"]
	max_temp = today["day"]["maxtemp_c"]
	min_temp = today["day"]["mintemp_c"]

	return {
		"rain": rain,
		"current_temp": current_temp,
		"max_temp": max_temp,
		"min_temp": min_temp,
	}
