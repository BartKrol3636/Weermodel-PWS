from PySide6.QtWidgets import QApplication
import sys
from helpers.openmeteo_helper import OpenMeteoHelper, MapQuality
from helpers.gui_helper import WeermodelWindow
import numpy as np

# zwolle_kaart.png coords: N: 52.67122222, E: 6.35519444, S: 52.35077778, W: 5.82716667

# == OpenMeteo ==
om_helper = OpenMeteoHelper()
rain_forecast_data = om_helper.get_rain_data(
    52.67122222, 52.35077778, 6.35519444, 5.82716667,
    quality=MapQuality.MEDIUM, debug=True
)

# == GUI ==
app = QApplication(sys.argv)
window = WeermodelWindow(rain_forecast_data)
window.show()
sys.exit(app.exec())
