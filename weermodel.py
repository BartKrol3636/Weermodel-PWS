try:
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    from PySide6.QtWidgets import QApplication
    from helpers.openmeteo_helper import BoundingBox
    from helpers.gui_helper import WeermodelWindow
    import sys

    # === Belangrijke Info ===
    # zwolle-kaart-klein.png coords: N: 52.6685322, E: 6.3574107, S: 52.3494906, W: 5.8324192
    # zwolle-kaart-groot.png: 4x zo groot

    # ====== OpenMeteo ======
    bounding_box = BoundingBox(52.67122222, 52.35077778, 6.35519444, 5.82716667)

    # ========= GUI =========
    app = QApplication(sys.argv)
    window = WeermodelWindow(bounding_box)
    window.show()
    sys.exit(app.exec())
except Exception as e:
    import traceback
    traceback.print_exc()
    input("An error occurred. Press Enter to exit...")