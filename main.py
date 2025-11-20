from gtfs import get_departures_by_stop
from weather import parse_weather

def main():
	print(get_departures_by_stop())
	print(parse_weather())

if __name__ == "__main__":
	main()
