from gtfs import get_departures_by_stop
from weather import parse_weather
from image import create_image
from display import display
import os

def main():
	departures = get_departures_by_stop()
	weather = parse_weather()
	image_path = create_image(departures, weather)
	display(image_path)

if __name__ == "__main__":
	main()
