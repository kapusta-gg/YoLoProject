from PyQt5.QtWidgets import QApplication
from mainwindow import MainWindow
import sys


#TODO: почистиь код
#TODO: заменить коэффиценты прямых на лямбда-функции?
#TODO: заменить слайдеры на что-то другое?
#TODO: (не обязательно) сдлеать защиту от неверных вводов

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    app.exec()