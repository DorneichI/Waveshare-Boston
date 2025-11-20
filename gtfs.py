import requests
from google.transit import gtfs_realtime_pb2
import os
import json
from datetime import datetime, timezone


FEED_URL = "https://cdn.mbta.com/realtime/TripUpdates.pb"

def get_trip_updates():
	response = requests.get(FEED_URL)
	response.raise_for_status()

	feed = gtfs_realtime_pb2.FeedMessage()
	feed.ParseFromString(response.content)

	return feed

def get_stop_ids():
	stops_path = os.path.join(os.path.dirname(__file__), "stops.json")
	with open(stops_path, "r") as file:
		stops = json.load(file)

	stop_ids = []
	for stop in stops["stops"]:
		stop_ids.append(str(stop["id"]))

	return stop_ids

def get_next_departures():
	feed = get_trip_updates()

	stop_ids = get_stop_ids()

	departures_times = {stop_id: [] for stop_id in stop_ids}

	for entity in feed.entity:
		if entity.HasField("trip_update"):
			trip = entity.trip_update
			for stop_time_update in trip.stop_time_update:
				stop_id = stop_time_update.stop_id
				if stop_id in stop_ids:
					dep = stop_time_update.departure.time if stop_time_update.HasField("departure") else None
					if dep:
						departures_times[stop_id].append(datetime.fromtimestamp(dep))

	return departures_times

def get_departures_by_stop():
	departures = get_next_departures()

	stops_path = os.path.join(os.path.dirname(__file__), "stops.json")
	with open(stops_path, "r") as file:
		stops = json.load(file)

	stop_data = {str(stop["id"]): {"name": stop["name"], "icon": stop["icon"]} for stop in stops["stops"]}

	stations = []
	for stop_id, times in departures.items():
		if stop_id in stop_data:
			stop_info = stop_data[stop_id]
			formatted_times = [time.strftime('%H:%M') for time in sorted(times)[:2]]  # Take the next 2 departures
			stations.append({
				"stop_id": stop_id,
				"name": stop_info["name"],
				"icon": os.path.join(os.path.dirname(__file__), "icons", stop_info["icon"]),
				"departures": formatted_times
			})

	return stations
