from helpers.settings import MapQuality
import openmeteo_requests
import numpy as np
import requests_cache
from retry_requests import retry
from time import sleep
from dataclasses import dataclass

@dataclass(frozen=True)
class BoundingBox:
	lat_min: float
	lat_max: float
	lon_min: float
	lon_max: float

	def __getitem__(self, idx):
		return (self.lat_min, self.lat_max, self.lon_min, self.lon_max)[idx]
	
	def get_centre(self) -> tuple[float, float]:
		lat_center = (self.lat_min + self.lat_max) / 2
		lon_center = (self.lon_min + self.lon_max) / 2
		return lat_center, lon_center

	def scale(self, factor: float) -> "BoundingBox":
		if factor <= 0:
			raise ValueError("zoom factor must be > 0")

		lat_center = (self.lat_min + self.lat_max) / 2
		lon_center = (self.lon_min + self.lon_max) / 2

		lat_half = (self.lat_max - self.lat_min) / 2 * factor
		lon_half = (self.lon_max - self.lon_min) / 2 * factor

		return BoundingBox(
			lat_center - lat_half,
			lat_center + lat_half,
			lon_center - lon_half,
			lon_center + lon_half,
		)

class DebugCachedSession(requests_cache.CachedSession):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.section = None
		self.used_cache = False

	def set_section(self, i, j):
		self.section = (i, j)
		self.used_cache = False

	def request(self, *args, **kwargs):
		response = super().request(*args, **kwargs)

		if hasattr(response, "from_cache"):
			i, j = self.section if self.section else ("?", "?")
			print(
				f"{'Using cache' if response.from_cache else 'Requesting new data'} "
				f"for section ({i}, {j})"
			)
			self.used_cache = response.from_cache

		return response

class OpenMeteoHelper:
	def grid_to_coords(self, lat_min: float, lat_max: float, lon_min: float, lon_max: float, cells: int):
		if cells < 1:
			raise ValueError("cells must be >= 1")
		
		lat_step = (lat_max - lat_min) / (cells - 1 if cells > 1 else 1)
		lon_step = (lon_max - lon_min) / (cells - 1 if cells > 1 else 1)

		latitudes = [lat_min + i * lat_step for i in range(cells)]
		longitudes = [lon_min + j * lon_step for j in range(cells)]

		return latitudes, longitudes

	def get_rain_data(self, bounding_box: BoundingBox, quality: MapQuality, debug: bool = False):
		cells = 10
		divisor = quality.value

		cache_session = DebugCachedSession(".cache")
		retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
		openmeteo = openmeteo_requests.Client(session=retry_session)

		lat_sections = np.linspace(bounding_box[0], bounding_box[1], divisor + 1)
		lon_sections = np.linspace(bounding_box[2], bounding_box[3], divisor + 1)

		merged_rain = None

		for i in range(divisor):
			for j in range(divisor):
				sec_lat_min = lat_sections[i]
				sec_lat_max = lat_sections[i + 1]
				sec_lon_min = lon_sections[j]
				sec_lon_max = lon_sections[j + 1]

				latitudes, longitudes = self.grid_to_coords(
					sec_lat_min, sec_lat_max, sec_lon_min, sec_lon_max, cells
				)

				coords = [(lat, lon) for lat in latitudes for lon in longitudes]

				url = "https://api.open-meteo.com/v1/forecast"
				# url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
				params = {
					"latitude": [lat for lat, lon in coords],
					"longitude": [lon for lat, lon in coords],
					"hourly": "precipitation",
					"models": "knmi_seamless",
					"start_date": "2026-02-22",
					"end_date": "2026-02-22",
				}
				
				for k in range(0, 12):
					try:
						cache_session.set_section(i, j)
						response = openmeteo.weather_api(url, params=params)
						break
					except openmeteo_requests.OpenMeteoRequestsError as e:
						print(e)
						print(f'waiting 10 seconds ({k+1})')
						sleep(10)

				n_hours = len(response[0].Hourly().Variables(0).ValuesAsNumpy())

				section_rain = np.zeros((n_hours, cells, cells))

				for idx, resp in enumerate(response):
					hourly = resp.Hourly()
					hourly_rain = hourly.Variables(0).ValuesAsNumpy()
					
					row = idx // cells
					col = idx % cells
					section_rain[:, row, col] = hourly_rain

				if merged_rain is None:
					merged_rain = np.zeros((n_hours, cells * divisor, cells * divisor))

				x_start = i * cells
				x_end = (i + 1) * cells
				y_start = j * cells
				y_end = (j + 1) * cells
				merged_rain[:, x_start:x_end, y_start:y_end] = section_rain

				if debug:
					print(f"Section ({i},{j}) merged into indices x:{x_start}-{x_end}, y:{y_start}-{y_end}")

		if debug:
			print("Merged rain shape (hours, lat, lon):", merged_rain.shape)

		return merged_rain
	
	def get_wind_direction(self, bounding_box: BoundingBox):
		cache_session = DebugCachedSession(".cache")
		retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
		openmeteo = openmeteo_requests.Client(session=retry_session)

		lat, lon = bounding_box.get_centre()

		url = "https://api.open-meteo.com/v1/forecast"
		params = {
			"latitude": lat,
			"longitude": lon,
			"hourly": "wind_direction_180m",
			"start_date": "2026-02-03",
			"end_date": "2026-02-03",
		}
		responses = openmeteo.weather_api(url, params=params)
		response = responses[0]

		hourly = response.Hourly()
		hourly_wind_direction_180m = hourly.Variables(0).ValuesAsNumpy()

		wind_direction_list = hourly_wind_direction_180m.tolist()

		print("Hourly wind directions:", wind_direction_list)

		return wind_direction_list
