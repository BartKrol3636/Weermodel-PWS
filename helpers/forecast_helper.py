import numpy as np

def get_forecast(start_data, wind_direction):
    forecast_data = np.repeat(start_data[np.newaxis, :, :], 24, axis=0)

    return forecast_data
