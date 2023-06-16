from PyQt5.QtWidgets import QFrame, QPushButton, QVBoxLayout, QFileDialog, QLabel, QErrorMessage, QSlider, QCheckBox
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QPixmap
import cv2

LABEL_SIZE = QSize(300, 20)
MODEL_IMAGE_URL = "changed_im.png"
BETWEEN_RANGE_MIN = 10
BETWEEN_RANGE_MAX = 400


class LeftPanel(QFrame):
    def __init__(self, image_label: QLabel, model):
        super().__init__()

        self.setObjectName("left_panel")
        self.err_message = QErrorMessage()

        self.model = model
        self.image_label = image_label
        self.image = None
        self.coef_platform = None
        self.coef_edge = None

        self.inform_label = QLabel("Настроить ограничительную линию платформы")
        self.inform_label.setFixedSize(LABEL_SIZE)

        self.edge_label = QLabel("Настроить линию края платформы")
        self.edge_label.setFixedSize(LABEL_SIZE)

        self.select_im_butt = QPushButton("Выбрать изображение")
        self.select_im_butt.clicked.connect(self.select_image)

        self.calc_butt = QPushButton("Вычислить")
        self.calc_butt.clicked.connect(self.calculate)

        self.first_point_edge = QSlider(Qt.Orientation.Horizontal)
        self.first_point_edge.setMinimum(BETWEEN_RANGE_MIN)
        self.first_point_edge.setMaximum(BETWEEN_RANGE_MAX)
        self.first_point_edge.sliderMoved.connect(self.drawline)

        self.second_point_edge = QSlider(Qt.Orientation.Horizontal)
        self.second_point_edge.setMinimum(BETWEEN_RANGE_MIN)
        self.second_point_edge.setMaximum(BETWEEN_RANGE_MAX)
        self.second_point_edge.sliderMoved.connect(self.drawline)

        self.first_point_platform = QSlider(Qt.Orientation.Horizontal)
        self.second_point_platform = QSlider(Qt.Orientation.Horizontal)
        self.first_point_platform.setMinimum(1)
        self.second_point_platform.setMinimum(1)
        self.first_point_platform.setMaximum(1)
        self.second_point_platform.setMaximum(1)

        self.first_point_platform.sliderMoved.connect(self.drawline)
        self.second_point_platform.sliderMoved.connect(self.drawline)

        self.is_left_check = QCheckBox("Платформа слева")
        self.is_left_check.stateChanged.connect(self.drawline)

        layout = QVBoxLayout(self)
        layout.addWidget(self.select_im_butt)
        layout.addWidget(self.inform_label)
        layout.addWidget(self.first_point_platform)
        layout.addWidget(self.second_point_platform)
        layout.addWidget(self.is_left_check)
        layout.addWidget(self.edge_label)
        layout.addWidget(self.first_point_edge)
        layout.addWidget(self.second_point_edge)
        layout.addWidget(self.calc_butt)

    def select_image(self):
        image_file = QFileDialog.getOpenFileName(self, caption="Выберите файл", filter="*.png *.jpg *.jpeg",
                                                 directory="C:\\")
        pixmap = QPixmap(image_file[0])
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size()))
        self.image = image_file[0]
        self.first_point_platform.setMaximum(cv2.imread(self.image).shape[1])
        self.second_point_platform.setMaximum(cv2.imread(self.image).shape[1])

        self.first_point_platform.setValue(1)
        self.second_point_platform.setValue(1)

    def drawline(self):
        new_image = cv2.imread(self.image)

        max_y = new_image.shape[0]

        cv2.line(new_image, (self.first_point_platform.value(), 0),
                 (self.second_point_platform.value(), new_image.shape[0]), (0, 255, 0), 2)

        if self.is_left_check.checkState():
            temp1 = self.first_point_platform.value() + self.first_point_edge.value()
            temp2 = self.second_point_platform.value() + self.second_point_edge.value()
            
        else:
            temp1 = self.first_point_platform.value() - self.first_point_edge.value()
            temp2 = self.second_point_platform.value() - self.second_point_edge.value()

        cv2.line(new_image, (temp1, 0), (temp2, new_image.shape[0]), (255, 0, 0), 2)

        cv2.imwrite(MODEL_IMAGE_URL, new_image)
        pixmap = QPixmap(MODEL_IMAGE_URL)

        self.image_label.setPixmap(pixmap.scaled(self.image_label.size()))

        k = (self.second_point_platform.value() - self.first_point_platform.value()) / max_y
        b = self.first_point_platform.value()

        self.coef_platform = (k, b)

        k = (temp2 - temp1) / max_y
        b = temp1

        self.coef_edge = (k, b)

    def calculate(self):
        new_image = cv2.imread(MODEL_IMAGE_URL)

        results = self.model(MODEL_IMAGE_URL, conf=0.2, save=True)
        for result in results:
            boxes = result.boxes
        persons = [i for i in boxes if i.cls == 0]
        between_peoples_count = 0
        off_peoples_count = 0

        for person in persons:
            platform_point = self.coef_platform[0] * person.xyxy[0][3] + self.coef_platform[1]
            edge_point = self.coef_edge[0] * person.xyxy[0][3] + self.coef_edge[1]
            range = abs(platform_point - edge_point)
            if self.is_left_check.checkState():
                diff = person.xyxy[0][2] - platform_point
                if 0 <= diff <= range:
                    between_peoples_count += 1
                    self.rectangle_drawing(new_image, person, (255, 0, 0))
                elif diff > range:
                    off_peoples_count += 1
                    self.rectangle_drawing(new_image, person, (0, 0, 255))
            else:
                diff = platform_point - person.xyxy[0][0]
                if 0 <= diff <= range:
                    between_peoples_count += 1
                    self.rectangle_drawing(new_image, person, (255, 0, 0))
                elif diff > range:
                    off_peoples_count += 1
                    self.rectangle_drawing(new_image, person, (0, 0, 255))

        cv2.imwrite(MODEL_IMAGE_URL, new_image)
        pixmap = QPixmap(MODEL_IMAGE_URL)
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size()))

        print(f"Количество людей {len(persons)}")
        print(f"Количество за линией {between_peoples_count}")
        print(f"Количество за перроном {off_peoples_count}")

    @staticmethod
    def rectangle_drawing(image, points, color):
        pt1 = [int(i) for i in points.xyxy[0][:2].tolist()]
        pt2 = [int(i) for i in points.xyxy[0][2:].tolist()]
        cv2.rectangle(image, pt2, pt1, color, 2)