from PySide6.QtWidgets import (
    QMainWindow, QLabel, QWidget, QComboBox,
    QVBoxLayout, QHBoxLayout, QPushButton
)
from PySide6.QtGui import QPixmap, QFont, QPainter, QColor
from PySide6.QtCore import Qt
from openmeteo_helper import OpenMeteoHelper, MapQuality, BoundingBox
import numpy as np
from enum import Enum

class RainMode(Enum):
    EIGEN = 0
    KNMI = 1


class WeermodelWindow(QMainWindow):
    def __init__(self, bounding_box: BoundingBox, map_path="assets/zwolle_kaart.png"):
        super().__init__()

        self.bounding_box = bounding_box
        self.map_quality = MapQuality.LOW
        self.rain_mode = RainMode.KNMI

        self.rain_forecast_data = np.zeros((1, 1, 1))
        self.max_hours, self.height, self.width = self.rain_forecast_data.shape
        self.t = 0

        self.get_rain()

        self.setWindowTitle("Weermodel")
        self.setFixedSize(1000, 880)

        self._setup_ui(map_path)
        self.draw_map()

    # ---------- UI ----------
    # widget.setStyleSheet("background-color: red;")

    def _setup_ui(self, map_path):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        left_widget = QWidget()
        left_widget.setFixedSize(768, 854)
        left_layout = QVBoxLayout(left_widget)

        # Pixmap
        self.pixmap = QPixmap(map_path)

        self.pixmap_label = QLabel()
        self.pixmap_label.setFixedSize(750, 750)
        left_layout.addWidget(self.pixmap_label, 0, Qt.AlignmentFlag.AlignTop)

        # Bottom Controls
        bottom_controls_widget = QWidget()
        bottom_controls_widget.setFixedSize(750, 75)
        bottom_controls_layout = QHBoxLayout(bottom_controls_widget)

        self.btn_prev = QPushButton("<")
        self.btn_prev.setFixedSize(50, 50)

        self.label_text = QLabel()
        self.label_text.setFont(QFont("Arial", 20))
        self.label_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_next = QPushButton(">")
        self.btn_next.setFixedSize(50, 50)

        bottom_controls_layout.addWidget(self.btn_prev)
        bottom_controls_layout.addWidget(self.label_text, 1)
        bottom_controls_layout.addWidget(self.btn_next)

        self.btn_prev.clicked.connect(self.prev_t)
        self.btn_next.clicked.connect(self.next_t)

        left_layout.addWidget(bottom_controls_widget)

        main_layout.addWidget(left_widget)

        # Right Controls
        right_controls_widget = QWidget()
        right_controls_widget.setFixedSize(204, 854)
        right_controls_layout = QVBoxLayout(right_controls_widget)

        dropdown_label = QLabel("Regen Kwaliteit:")
        right_controls_layout.addWidget(dropdown_label)
        
        quality_dropdown = QComboBox()
        quality_dropdown.addItems([e.name for e in MapQuality])
        quality_dropdown.currentIndexChanged.connect(self.on_quality_dropdown_change)
        right_controls_layout.addWidget(quality_dropdown, 1, Qt.AlignmentFlag.AlignTop)

        main_layout.addWidget(right_controls_widget, 1, Qt.AlignmentFlag.AlignRight)

    # ---------- Logic ----------

    def change_rain_mode(self, mode: RainMode):
        self.rain_mode = mode

    def get_rain(self):
        om_helper = OpenMeteoHelper()
        rain_forecast_data = om_helper.get_rain_data(self.bounding_box, quality=self.map_quality, debug=False)
        self.rain_forecast_data = rain_forecast_data
        self.max_hours, self.height, self.width = rain_forecast_data.shape

    def on_quality_dropdown_change(self, index):
        print(f"Changing Quality to {list(MapQuality)[index].name}")
        self.map_quality = list(MapQuality)[index]
        self.get_rain()
        self.draw_map()

    def get_rain_color(self, rain):
        gradient = [
            (255, 255, 255), 
            (77, 93, 255),
            (0, 7, 112),
            (254, 22, 0),
            (192, 28, 196)
        ]
        thresholds = [2, 5, 10, 100, 200]

        base_alpha = 191 # 75%

        rain = max(0, rain)
        if rain > thresholds[-1]:
            rain = thresholds[-1]

        if rain <= thresholds[0]:
            alpha = int((rain / thresholds[0]) * base_alpha)
            r, g, b = gradient[0]
            return QColor(r, g, b, alpha)

        for i in range(1, len(thresholds)):
            if rain <= thresholds[i]:
                t = (rain - thresholds[i-1]) / (thresholds[i] - thresholds[i-1])
                r0, g0, b0 = gradient[i-1]
                r1, g1, b1 = gradient[i]
                r = int(r0 + (r1 - r0) * t)
                g = int(g0 + (g1 - g0) * t)
                b = int(b0 + (b1 - b0) * t)
                return QColor(r, g, b, base_alpha)

        # fallback
        r, g, b, base_alpha = 0, 0, 0, 255
        return QColor(r, g, b, base_alpha)

    def draw_map(self):
        pixmap_overlay = QPixmap(self.pixmap)
        painter = QPainter(pixmap_overlay)
        painter.setRenderHint(QPainter.Antialiasing)

        for y in range(self.height):
            for x in range(self.width):
                rain = self.rain_forecast_data[self.t][y, x]
                if rain > 0:
                    painter.fillRect(
                        x * (750 // self.width),
                        y * (750 // self.height),
                        750 // self.width,
                        750 // self.height,
                        self.get_rain_color(rain)
                    )

        painter.end()
        self.pixmap_label.setPixmap(pixmap_overlay)
        self.label_text.setText(f"Tijdstap: {self.t}")

    def prev_t(self):
        if self.t > 0:
            self.t -= 1
            self.draw_map()

    def next_t(self):
        if self.t < self.max_hours - 1:
            self.t += 1
            self.draw_map()

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    bounding_box = BoundingBox(52.67122222, 52.35077778, 6.35519444, 5.82716667)

    app = QApplication(sys.argv)
    window = WeermodelWindow(bounding_box)
    window.show()
    sys.exit(app.exec())