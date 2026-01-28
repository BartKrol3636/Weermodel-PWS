from enum import Enum
import openmeteo_requests
import numpy as np
import requests_cache
from retry_requests import retry
from time import sleep
import ast

class MapQuality(Enum):  # (cells_per_section, section_divisor)
	LOW = (10, 1)
	MEDIUM = (10, 3)
	HIGH = (10, 5)
	ULTRA = (10, 15)

class OpenMeteoHelper:
	def grid_to_coords(self, lat_min: float, lat_max: float, lon_min: float, lon_max: float, cells: int):
		if cells < 1:
			raise ValueError("cells must be >= 1")
		
		lat_step = (lat_max - lat_min) / (cells - 1 if cells > 1 else 1)
		lon_step = (lon_max - lon_min) / (cells - 1 if cells > 1 else 1)

		latitudes = [lat_min + i * lat_step for i in range(cells)]
		longitudes = [lon_min + j * lon_step for j in range(cells)]

		return latitudes, longitudes

	def get_rain_data(self, lat_min: float, lat_max: float, lon_min: float, lon_max: float, quality: MapQuality, debug: bool = False):
		cells, divisor = quality.value

		cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
		retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
		openmeteo = openmeteo_requests.Client(session=retry_session)

		lat_sections = np.linspace(lat_min, lat_max, divisor + 1)
		lon_sections = np.linspace(lon_min, lon_max, divisor + 1)

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

				url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
				params = {
					"latitude": [lat for lat, lon in coords],
					"longitude": [lon for lat, lon in coords],
					"hourly": "rain",
					"models": "knmi_seamless",
					"end_date": "2026-01-25",
					"start_date": "2026-01-27",
				}
				
				for k in range(0, 12):
					try:
						response = openmeteo.weather_api(url, params=params)
						break
					except openmeteo_requests.OpenMeteoRequestsError as e:
						print(e)
						msg = str(e)
						data = ast.literal_eval(msg.split(": ", 1)[1])
						x = data["reason"]
						print(f'waiting 10 extra seconds ({k+1})')
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


if __name__ == "__main__":
	OMHelper = OpenMeteoHelper()
	merged_data = OMHelper.get_rain_data(
		52.67122222, 52.35077778, 6.35519444, 5.82716667,
		quality=MapQuality.MEDIUM,
		debug=True
	)
