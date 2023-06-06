from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QSize
from leftpanel import LeftPanel
from ultralytics import YOLO

MAIN_WINDOW_SIZE = QSize(1200, 800)
LABEL_WIDGET_SIZE = QSize(800, 700)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setFixedSize(MAIN_WINDOW_SIZE)

        self.model = YOLO('yolov8n.pt')

        self.image_label = QLabel()
        self.image_label.setFixedSize(LABEL_WIDGET_SIZE)

        self.left_panel = LeftPanel(self.image_label, self.model)

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.left_panel)
        self.layout.addWidget(self.image_label)

        self.widget = QWidget()
        self.widget.setLayout(self.layout)

        self.setCentralWidget(self.widget)
