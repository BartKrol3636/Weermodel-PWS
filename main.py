from PySide6.QtWidgets import QApplication
from helpers.openmeteo_helper import BoundingBox
from helpers.gui_helper import WeermodelWindow
import sys

# === Belangrijke Info ===
# zwolle_kaart.png coords: N: 52.67122222, E: 6.35519444, S: 52.35077778, W: 5.82716667

# ====== OpenMeteo ======
bounding_box = BoundingBox(52.67122222, 52.35077778, 6.35519444, 5.82716667)

# ========= GUI =========
app = QApplication(sys.argv)
window = WeermodelWindow(bounding_box)
window.show()
sys.exit(app.exec())
