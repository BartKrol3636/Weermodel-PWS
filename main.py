from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout
from PySide6.QtGui import QPixmap, QFont, QPainter, QColor
from PySide6.QtCore import QRect, Qt
import sys
import numpy as np

# Weermodel

def regen_kleur(waarde):
    if waarde <= 2:
        return QColor(255, 255, 255, 200)
    elif waarde <= 5:
        return QColor(77, 93, 255, 200)
    elif waarde <= 10:
        return QColor(0, 7, 112, 200)
    elif waarde <= 100:
        return QColor(254, 22, 0, 200)
    else:
        return QColor(192, 28, 196, 200)

regen = np.zeros((150, 150))
regen[70:90, 60:80] = 5.0
regen[40:60, 100:120] = 12.0
regen[100:120, 30:50] = 0.5
regen[90:100, 80:90] = 150.0

# GUI

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("Weermodel")
window.setGeometry(25, 50, 750, 850)

central_widget = QWidget()
window.setCentralWidget(central_widget)

layout = QVBoxLayout()
central_widget.setLayout(layout)

pixmap = QPixmap("zwolle_kaart.png")
pixmap_overlay = QPixmap(pixmap)
painter = QPainter(pixmap_overlay)
painter.setRenderHint(QPainter.Antialiasing)

for y in range(150):
    for x in range(150):
        waarde = regen[y, x]
        if waarde > 0:
            painter.fillRect(x * 5, y * 5, 5, 5, regen_kleur(waarde))

painter.end()

pixmap_label = QLabel()
pixmap_label.setPixmap(pixmap_overlay)
layout.addWidget(pixmap_label, 0 , Qt.AlignmentFlag.AlignTop)

t = 0
label_text = QLabel(f"tijdstap: {t}")
label_text.setFont(QFont("Arial", 20))
label_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
layout.addWidget(label_text, 0, Qt.AlignmentFlag.AlignBottom)

window.show()
sys.exit(app.exec())
