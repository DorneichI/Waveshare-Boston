"""GTFS helper: fetch MBTA TripUpdates and map them to configured stops."""

import requests
from google.transit import gtfs_realtime_pb2
import os
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


FEED_URL = "https://cdn.mbta.com/realtime/TripUpdates.pb"


def _get_trip_updates():
	"""Download and parse the GTFS-realtime TripUpdates feed."""
	response = requests.get(FEED_URL)
	response.raise_for_status()

	feed = gtfs_realtime_pb2.FeedMessage()
	feed.ParseFromString(response.content)

	return feed


def _get_stop_ids():
	"""Read `stops.json` and return a list of stop ID strings."""
	stops_path = os.path.join(os.path.dirname(__file__), "stops.json")
	with open(stops_path, "r") as file:
		stops = json.load(file)

	stop_ids = []
	for stop in stops["stops"]:
		stop_ids.append(str(stop["id"]))

	return stop_ids


def _get_next_departures():
	"""Return a mapping of stop_id -> list of upcoming datetimes."""
	feed = _get_trip_updates()

	stop_ids = _get_stop_ids()

	departures_times = {stop_id: [] for stop_id in stop_ids}

	tz_boston = ZoneInfo("America/New_York")

	for entity in feed.entity:
		if entity.HasField("trip_update"):
			trip = entity.trip_update
			for stop_time_update in trip.stop_time_update:
				stop_id = stop_time_update.stop_id
				if stop_id in stop_ids:
					dep = stop_time_update.departure.time if stop_time_update.HasField("departure") else None
					if dep:
						dt_utc = datetime.fromtimestamp(dep, tz=timezone.utc)
						dt_boston = dt_utc.astimezone(tz_boston)
						departures_times[stop_id].append(dt_boston)

	return departures_times


def get_departures_by_stop():
	"""Return a list of station dicts with next departures for display.

	Each station dict contains: ``stop_id``, ``name``, ``icon`` (absolute
	path within the `icons/` directory), and ``departures`` (list of formatted
	time strings). The function limits the returned departure times to the
	next two times per stop.
	"""
	departures = _get_next_departures()

	stops_path = os.path.join(os.path.dirname(__file__), "stops.json")
	with open(stops_path, "r") as file:
		stops = json.load(file)

	stop_data = {str(stop["id"]): {"name": stop["name"], "icon": stop["icon"]} for stop in stops["stops"]}

	stations = []
	for stop_id, times in departures.items():
		if stop_id in stop_data:
			stop_info = stop_data[stop_id]
			formatted_times = [time.strftime('%H:%M') for time in sorted(times)[:2]]
			stations.append({
				"stop_id": stop_id,
				"name": stop_info["name"],
				"icon": os.path.join(os.path.dirname(__file__), "icons", stop_info["icon"]),
				"departures": formatted_times,
			})

	return stations
