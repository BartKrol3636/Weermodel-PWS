import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

class OpenMeteoHelper():
	def make_lat_lon_grid(self, lat_min, lat_max, lon_min, lon_max, cells):
		if cells < 1:
			raise ValueError("cells must be >= 1")
	
		lat_step = (lat_max - lat_min) / (cells - 1 if cells > 1 else 1)
		lon_step = (lon_max - lon_min) / (cells - 1 if cells > 1 else 1)

		latitudes = []
		longitudes = []

		for i in range(cells):
			for j in range(cells):
				latitudes.append(lat_min + i * lat_step)
				longitudes.append(lon_min + j * lon_step)

		return {
			"latitude": latitudes,
			"longitude": longitudes,
		}
	
	def get_rain_data(self, lat_min, lat_max, lon_min, lon_max, cells):
		cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
		retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
		openmeteo = openmeteo_requests.Client(session=retry_session)

		# Make sure all required weather variables are listed here
		# The order of variables in hourly or daily is important to assign them correctly below
		latitudes, longitudes = self.make_lat_lon_grid(lat_min, lat_max, lon_min, lon_max, cells).values()
		url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
		params = {
			"latitude": latitudes,
			"longitude": longitudes,
			"hourly": "rain",
			"past_days": 1,
			"forecast_days": 1,
		}
		responses = openmeteo.weather_api(url, params=params)

		# Process locations
		for response in responses:
			print(f"\nCoordinates: {response.Latitude()}°N {response.Longitude()}°E")
			print(f"Elevation: {response.Elevation()} m asl")
			print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")
			
			# Process hourly data. The order of variables needs to be the same as requested.
			hourly = response.Hourly()
			hourly_rain = hourly.Variables(0).ValuesAsNumpy()
			
			hourly_data = {"date": pd.date_range(
				start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
				end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
				freq = pd.Timedelta(seconds = hourly.Interval()),
				inclusive = "left"
			)}
			
			hourly_data["rain"] = hourly_rain
			
			hourly_dataframe = pd.DataFrame(data = hourly_data)
			print("\nHourly data\n", hourly_dataframe)
			
		print(len(responses), "responses processed.")