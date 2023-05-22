from PyQt5.QtWidgets import QFrame, QPushButton, QVBoxLayout, QFileDialog, QLabel, QErrorMessage, QSlider, QCheckBox
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QPixmap
import cv2

LABEL_SIZE = QSize(100, 20)
MODEL_IMAGE_URL = "changed_im.png"
BETWEEN_RANGE_MIN = 10
BETWEEN_RANGE_MAX = 100


class LeftPanel(QFrame):
    def __init__(self, image_label: QLabel, model):
        super().__init__()

        self.setObjectName("left_panel")
        self.err_message = QErrorMessage()

        self.model = model
        self.image_label = image_label
        self.image = None
        self.coef = None

        self.inform_label = QLabel("Выбрать точки для построения линии")
        self.inform_label.setFixedSize(LABEL_SIZE)

        self.range_label = QLabel("Выбрать расстояние между краем платформы и линией")
        self.range_label.setFixedSize(LABEL_SIZE)

        self.select_im_butt = QPushButton("Выбрать изображение")
        self.select_im_butt.clicked.connect(self.select_image)

        self.calc_butt = QPushButton("Вычислить")
        self.calc_butt.clicked.connect(self.calculate)

        self.range_slider = QSlider(Qt.Orientation.Horizontal)
        self.range_slider.setMinimum(BETWEEN_RANGE_MIN)
        self.range_slider.setMaximum(BETWEEN_RANGE_MAX)
        self.range_slider.sliderMoved.connect(self.drawline)

        self.first_point = QSlider(Qt.Orientation.Horizontal)
        self.second_point = QSlider(Qt.Orientation.Horizontal)
        self.first_point.setMinimum(1)
        self.second_point.setMinimum(1)
        self.first_point.setMaximum(1)
        self.second_point.setMaximum(1)

        self.first_point.sliderMoved.connect(self.drawline)
        self.second_point.sliderMoved.connect(self.drawline)

        self.is_left_check = QCheckBox()

        layout = QVBoxLayout(self)
        layout.addWidget(self.select_im_butt)
        layout.addWidget(self.inform_label)
        layout.addWidget(self.first_point)
        layout.addWidget(self.second_point)
        layout.addWidget(self.is_left_check)
        layout.addWidget(self.range_label)
        layout.addWidget(self.range_slider)
        layout.addWidget(self.calc_butt)

    def select_image(self):
        image_file = QFileDialog.getOpenFileName(self, caption="Выберите файл", filter="*.png *.jpg *.jpeg",
                                                 directory="C:\\")
        pixmap = QPixmap(image_file[0])
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size()))
        self.image = image_file[0]
        self.first_point.setMaximum(cv2.imread(self.image).shape[1])
        self.second_point.setMaximum(cv2.imread(self.image).shape[1])

        self.first_point.setValue(1)
        self.second_point.setValue(1)

    def drawline(self):
        new_image = cv2.imread(self.image)

        max_y = new_image.shape[0]
        print(max_y)

        cv2.line(new_image, (self.first_point.value(), 0),
                 (self.second_point.value(), new_image.shape[0]), (0, 255, 0), 2)

        if self.is_left_check.checkState():
            temp1 = self.first_point.value() + self.range_slider.value()
            temp2 = self.second_point.value() + self.range_slider.value()
        else:
            temp1 = self.first_point.value() - self.range_slider.value()
            temp2 = self.second_point.value() - self.range_slider.value()

        cv2.line(new_image, (temp1, 0), (temp2, new_image.shape[0]), (255, 0, 0), 2)

        cv2.imwrite(MODEL_IMAGE_URL, new_image)
        pixmap = QPixmap(MODEL_IMAGE_URL)

        self.image_label.setPixmap(pixmap.scaled(self.image_label.size()))

        a = (self.second_point.value() - self.first_point.value()) / max_y
        b = self.first_point.value()

        self.coef = (a, b)

    def calculate(self):
        new_image = cv2.imread(MODEL_IMAGE_URL)

        results = self.model(MODEL_IMAGE_URL, conf=0.2, save=True)
        for result in results:
            boxes = result.boxes
        persons = [i for i in boxes if i.cls == 0]
        between_peoples_count = 0
        off_peoples_count = 0

        for person in persons:
            point = person.xyxy[0][2:].clone()
            if self.is_left_check.checkState():
                if 0 <= - point[0] + self.coef[0] * point[1] + self.coef[1] <= self.range_slider.value():
                    between_peoples_count += 1
                elif point[0] - self.coef[0] * point[1] + self.coef[1] > self.range_slider.value():
                    off_peoples_count += 1
            else:
                point[0] = person.xyxy[0][0]
                print(self.coef[0] * point[1] + self.coef[1] - point[0])
                if 0 <= (self.coef[0] * point[1] + self.coef[1]) - point[0] <= self.range_slider.value():
                    between_peoples_count += 1
                    pt1 = [int(i) for i in person.xyxy[0][:2].tolist()]
                    pt2 = [int(i) for i in person.xyxy[0][2:].tolist()]
                    cv2.rectangle(new_image, pt2, pt1, (255, 0, 0), 2)
                    print((self.coef[0] * point[1] + self.coef[1]) - point[0])
                elif self.coef[0] * point[1] + self.coef[1] - point[0] > self.range_slider.value():
                    off_peoples_count += 1
                    pt1 = [int(i) for i in person.xyxy[0][:2].tolist()]
                    pt2 = [int(i) for i in person.xyxy[0][2:].tolist()]
                    cv2.rectangle(new_image, pt2, pt1, (0, 0, 255), 2)

        cv2.imwrite(MODEL_IMAGE_URL, new_image)
        pixmap = QPixmap(MODEL_IMAGE_URL)
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size()))

        print(f"Количество людей {len(persons)}")
        print(f"Количество за линией {between_peoples_count}")
        print(f"Количество за перроном {off_peoples_count}")
