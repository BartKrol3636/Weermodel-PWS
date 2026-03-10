import numpy as np
from scipy.ndimage import shift

def get_forecast(start_data, wind_directions, speed=10.0):
    forecast_data = np.empty((24, *start_data.shape), dtype=start_data.dtype)
    current_clouds = start_data.copy()

    for hour, wind_deg in enumerate(wind_directions):
        rad = np.deg2rad(wind_deg)

        dy = -speed * np.sin(rad)
        dx = speed * np.cos(rad)

        shifted = shift(current_clouds, shift=(dy, dx), order=1, mode='wrap')

        forecast_data[hour] = shifted
        current_clouds = shifted

    return forecast_data
