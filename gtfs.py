"""GTFS helper: fetch MBTA TripUpdates and map them to configured stops."""

import requests
from google.transit import gtfs_realtime_pb2
import os
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from dotenv import load_dotenv


FEED_URL = "https://cdn.mbta.com/realtime/TripUpdates.pb"
load_dotenv()
# default to America/New_York when TZ not set
TIME_ZONE = os.getenv("TZ") or "America/New_York"


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


def _get_next_departures(stop_ids, max_per_stop=2):
	"""Return a mapping of stop_id -> list of upcoming datetimes."""
	feed = _get_trip_updates()

	stop_ids_set = set(stop_ids)
	departures_epochs = {stop_id: [] for stop_id in stop_ids_set}
	remaining = set(stop_ids_set)

	local_tz = ZoneInfo(TIME_ZONE)

	done = False
	for entity in feed.entity:
		if entity.HasField("trip_update"):
			for stop_time_update in entity.trip_update.stop_time_update:
				stop_id = stop_time_update.stop_id
				if stop_id not in remaining:
					continue
				if stop_time_update.HasField("departure") and stop_time_update.departure.time:
					departures_epochs[stop_id].append(stop_time_update.departure.time)
					if len(departures_epochs[stop_id]) >= max_per_stop:
						remaining.discard(stop_id)
						if not remaining:
							done = True
							break
		if done:
			break

	# Convert kept epoch seconds to timezone-aware datetimes and sort
	departures_times = {}
	for stop_id, epochs in departures_epochs.items():
		if not epochs:
			departures_times[stop_id] = []
			continue
		selected = sorted(epochs)[:max_per_stop]
		departures_times[stop_id] = [datetime.fromtimestamp(e, tz=timezone.utc).astimezone(local_tz) for e in selected]

	return departures_times


def get_departures_by_stop():
	"""Return a list of station dicts with next departures for display.

	Each station dict contains: ``stop_id``, ``name``, ``icon`` (absolute
	path within the `icons/` directory), and ``departures`` (list of formatted
	time strings). The function limits the returned departure times to the
	next two times per stop.
	"""
	# Load stops once and pass stop IDs into the optimized collector
	stops_path = os.path.join(os.path.dirname(__file__), "stops.json")
	with open(stops_path, "r") as file:
		stops = json.load(file)

	stop_data = {str(stop["id"]): {"name": stop["name"], "icon": stop["icon"]} for stop in stops["stops"]}
	stop_ids = list(stop_data.keys())

	departures = _get_next_departures(stop_ids, max_per_stop=2)

	stations = []
	for stop_id, times in departures.items():
		if stop_id in stop_data:
			stop_info = stop_data[stop_id]
			formatted_times = [t.strftime('%H:%M') for t in times]
			stations.append({
				"stop_id": stop_id,
				"name": stop_info["name"],
				"icon": os.path.join(os.path.dirname(__file__), "icons", stop_info["icon"]),
				"departures": formatted_times,
			})

	return stations
