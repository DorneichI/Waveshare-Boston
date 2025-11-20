from gtfs import get_departures_by_stop
from weather import parse_weather
from display import display
import os

def main():
	print(get_departures_by_stop())
	print(parse_weather())
	icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'icons', 'Icon-green-line-b-default.svg'))
	display(icon_path)

if __name__ == "__main__":
	main()
