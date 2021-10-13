import sys

from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QInputDialog, QFileDialog, QMessageBox
from PyQt5.QtWidgets import QStackedWidget

filename = ''


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('designs/main_window.ui', self)
        self.initUI()

        self.create_new_btn.clicked.connect(self.choose_what_to_create)
        self.open_btn.clicked.connect(self.open)

    def initUI(self):
        # Displaying the logo in the main window
        self.title_image_pixmap = QPixmap('designs/title_image.jpg')
        self.title_image = QLabel(self)
        self.title_image.move(160, 50)
        self.title_image.resize(480, 125)
        self.title_image.setPixmap(self.title_image_pixmap)

    def choose_what_to_create(self):
        # Creating an input dialog to ask the user what editor to open
        file_type, ok_pressed = QInputDialog.getItem(self, "Choose media type",
                                                     "Choose what you want to create:",
                                                     ("Image", "Text"), 0, False)
        if ok_pressed:
            # Opening the editor that the user wants to open
            if file_type == "Image":
                windows.setCurrentIndex(2)
            elif file_type == "Text":
                windows.setCurrentIndex(1)

    def open(self):
        # Getting the filename and the file extension
        global filename
        filename = QFileDialog.getOpenFileName(self, 'Choose file', '')[0]
        extension = filename[filename.rfind('.')::]

        # Guessing what editor the user wants to open
        if extension == '.txt' \
                and QMessageBox.question(self, '', "Do you want to edit a text document?",
                                         QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            windows.setCurrentIndex(1)

        elif (extension == '.png' or extension == '.jpg' or extension == '.bmp') \
                and QMessageBox.question(self, '', "Do you want to edit an image?",
                                         QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            windows.setCurrentIndex(2)
        elif (extension == '.mp3' or extension == '.wav') \
                and QMessageBox.question(self, '', "Do you want to edit an audio file?",
                                         QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            windows.setCurrentIndex(3)
        elif (extension == '.mp4' or extension == '.mov' or extension == '.wmv'
                or extension == '.avi') \
                and QMessageBox.question(self, '', "Do you want to edit a video?",
                                         QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            windows.setCurrentIndex(4)

        else:
            # If the guess isn't correct,
            # creating an input dialog to ask the user what editor to open
            file_type, ok_pressed = QInputDialog.getItem(self, "Choose media type",
                                                         "Choose what you want to edit:",
                                                         ("Image", "Text", "Audio", "Video"),
                                                         0, False)

            # Opening the editor that the user wants to open
            if ok_pressed:
                if file_type == "Text":
                    windows.setCurrentIndex(1)

                elif file_type == "Image":
                    windows.setCurrentIndex(2)

                elif file_type == "Audio":
                    windows.setCurrentIndex(3)
                elif file_type == "Video":
                    windows.setCurrentIndex(4)


class TextEditingWindow(QMainWindow):
    # TODO
    pass


class ImageEditingWindow(QMainWindow):
    # TODO
    pass


class AudioEditingWindow(QMainWindow):
    # TODO
    pass


class VideoEditingWindow(QMainWindow):
    # TODO
    pass


if __name__ == '__main__':
    app = QApplication(sys.argv)

    windows = QStackedWidget()

    main_window = MainWindow()
    windows.addWidget(main_window)

    text_editing_window = TextEditingWindow()
    windows.addWidget(text_editing_window)

    image_editing_window = ImageEditingWindow()
    windows.addWidget(image_editing_window)

    audio_editing_window = AudioEditingWindow()
    windows.addWidget(audio_editing_window)

    video_editing_window = VideoEditingWindow()
    windows.addWidget(video_editing_window)

    windows.setFixedHeight(600)
    windows.setFixedWidth(800)
    windows.setWindowTitle("Media Editor")

    windows.show()

    sys.exit(app.exec_())
