from PySide6.QtWidgets import (
    QMainWindow, QLabel, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton
)
from PySide6.QtGui import QPixmap, QFont, QPainter, QColor
from PySide6.QtCore import Qt


class WeermodelWindow(QMainWindow):
    def __init__(self, rain_forecast_data, map_path="assets/zwolle_kaart.png"):
        super().__init__()

        self.rain_forecast_data = rain_forecast_data
        self.max_hours, self.height, self.width = rain_forecast_data.shape
        self.t = 0

        self.setWindowTitle("Weermodel")
        self.setGeometry(25, 50, 750, 850)
        self.setFixedSize(750, 850)

        self._setup_ui(map_path)
        self.draw_map()

    # ---------- UI ----------

    def _setup_ui(self, map_path):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        self.pixmap = QPixmap(map_path)

        self.pixmap_label = QLabel()
        layout.addWidget(self.pixmap_label, 0, Qt.AlignmentFlag.AlignTop)

        controls_layout = QHBoxLayout()

        self.btn_prev = QPushButton("<")
        self.btn_prev.setFixedSize(50, 50)

        self.label_text = QLabel()
        self.label_text.setFont(QFont("Arial", 20))
        self.label_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_next = QPushButton(">")
        self.btn_next.setFixedSize(50, 50)

        controls_layout.addWidget(self.btn_prev)
        controls_layout.addWidget(self.label_text, 1)
        controls_layout.addWidget(self.btn_next)

        layout.addLayout(controls_layout)

        self.btn_prev.clicked.connect(self.prev_t)
        self.btn_next.clicked.connect(self.next_t)

    # ---------- Logic ----------

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
        self.label_text.setText(f"tijdstap: {self.t}")

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
    import numpy as np
    import sys

    method = 1

    if method == 1:
        rain_forecast_data = np.random.rand(24, 10, 10) * 10
    if method == 2:
        rain_forecast_data = np.zeros((48, 10, 10))
        for t in range(24):
            rain_forecast_data[t] = t * 2
        for t in range(24):
            rain_forecast_data[t + 24] = 48 + t * 6

    app = QApplication(sys.argv)
    window = WeermodelWindow(rain_forecast_data)
    window.show()
    sys.exit(app.exec())