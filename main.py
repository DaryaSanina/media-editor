import sys

from PyQt5 import uic
from PyQt5.QtGui import QPixmap, QFont, QKeyEvent, QKeySequence
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QInputDialog, QFileDialog, QMessageBox
from PyQt5.QtWidgets import QStackedWidget
from PyQt5.QtCore import Qt

HTML_EXTENSIONS = ['.htm', '.html']
TEXT_EXTENSIONS = ['.txt']
IMAGE_EXTENSIONS = ['.png', '.jpg', '.bmp']
AUDIO_EXTENSIONS = ['.mp3', '.wav']

filename = ''


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('designs/main_window.ui', self)
        self.initUI()

        self.create_new_btn.clicked.connect(self.choose_what_to_create)
        self.open_btn.clicked.connect(self.open)

    def initUI(self) -> None:
        # Displaying the logo in the main window
        self.title_image_pixmap = QPixmap('designs/title_image.jpg')
        self.title_image = QLabel(self)
        self.title_image.move(160, 50)
        self.title_image.resize(480, 125)
        self.title_image.setPixmap(self.title_image_pixmap)

    def choose_what_to_create(self) -> None:
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

    def open(self) -> None:
        # Getting the filename and the file extension
        global filename
        filename = QFileDialog.getOpenFileName(self, 'Choose file', '')[0]
        extension = filename[filename.rfind('.')::]

        # Guessing what editor the user wants to open
        if extension in TEXT_EXTENSIONS or extension in HTML_EXTENSIONS \
                and QMessageBox.question(self, 'File type guess',
                                         "Do you want to edit a text document?",
                                         QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            windows.setCurrentIndex(1)
            text_editing_window.filename = filename
            with open(filename, 'r', encoding='utf-8') as source_file:
                text_editing_window.text_edit.setText(source_file.read())

        elif extension in IMAGE_EXTENSIONS \
                and QMessageBox.question(self, 'File type guess', "Do you want to edit an image?",
                                         QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            windows.setCurrentIndex(2)
        elif extension in AUDIO_EXTENSIONS \
                and QMessageBox.question(self, 'File type guess',
                                         "Do you want to edit an audio file?",
                                         QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            windows.setCurrentIndex(3)

        elif extension != '':
            # If the guess isn't correct,
            # creating an input dialog to ask the user what editor to open
            file_type, ok_pressed = QInputDialog.getItem(self, "Choose media type",
                                                         "Choose what you want to edit:",
                                                         ("Image", "Text", "Audio"),
                                                         0, False)

            # Opening the editor that the user wants to open
            if ok_pressed:
                if file_type == "Text":
                    windows.setCurrentIndex(1)
                    text_editing_window.filename = filename
                    with open(filename, 'r', encoding='utf-8') as source_file:
                        text_editing_window.text_edit.setText(source_file.read())

                elif file_type == "Image":
                    windows.setCurrentIndex(2)

                elif file_type == "Audio":
                    windows.setCurrentIndex(3)


class TextEditingWindow(QMainWindow):
    def __init__(self):
        super(TextEditingWindow, self).__init__()
        uic.loadUi('designs/text_editor_window.ui', self)

        self.new_btn.clicked.connect(self.new)
        self.open_btn.clicked.connect(self.open)
        self.save_btn.clicked.connect(self.save)
        self.save_as_btn.clicked.connect(self.save_as)

        self.font_combo_box.currentFontChanged.connect(self.change_font)

        self.font_size_spin_box.valueChanged.connect(self.change_font_point_size)

        self.bold_btn.clicked.connect(self.set_bold)
        self.italic_btn.clicked.connect(self.set_italic)
        self.underline_btn.clicked.connect(self.set_underlined)
        self.strikeout_btn.clicked.connect(self.set_strikeout)

    def new(self) -> None:
        global filename

        self.text_edit.setText('')
        filename = ''

    def open(self) -> None:
        global filename

        filename = QFileDialog.getOpenFileName(self, 'Choose file', '')[0]
        with open(filename, 'r', encoding='utf-8') as source_file:
            self.text_edit.setText(source_file.read())

    def save(self) -> None:
        global filename

        if filename == '':
            # If the file is new, ask the user for the filename
            filename = QFileDialog.getSaveFileName(self, 'Save file', '')[0]
        with open(filename, 'w', encoding='utf-8') as dest_file:
            extension = filename[filename.rfind('.')::]
            # If the extension of the file the user wants to save the text to is an html extension,
            # save the text with formatting,
            # else save the text without formatting
            text = self.text_edit.toHtml() if extension in HTML_EXTENSIONS \
                else self.text_edit.toPlainText()
            dest_file.write(text)

    def save_as(self) -> None:
        global filename

        filename = QFileDialog.getSaveFileName(self, 'Save file', '')[0]
        with open(filename, 'w', encoding='utf-8') as dest_file:
            dest_file.write(self.text_edit.toPlainText())

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if int(event.modifiers()) == Qt.ControlModifier and event.key() == Qt.Key_S:
            self.save()
        elif int(event.modifiers()) == (Qt.ControlModifier + Qt.ShiftModifier) \
                and event.key() == Qt.Key_S:
            self.save_as()

    def change_font(self, font: QFont) -> None:
        self.text_edit.setCurrentFont(font)

    def change_font_point_size(self, font_point_size: int) -> None:
        self.text_edit.setFontPointSize(font_point_size)

    def set_bold(self) -> None:
        # Make the text bold if the "bold_btn" is checked, else make it not bold
        if self.sender().isChecked():
            self.text_edit.setFontWeight(QFont.Bold)
        else:
            self.text_edit.setFontWeight(QFont.NoFontMerging)

    def set_italic(self) -> None:
        # Make the text italic if the "italic_btn" is checked, else make it not italic
        if self.sender().isChecked():
            self.text_edit.setFontItalic(True)
        else:
            self.text_edit.setFontItalic(False)

    def set_underlined(self) -> None:
        # Underline the text if the "underline_btn" is checked, else make it not underlined
        if self.sender().isChecked():
            self.text_edit.setFontUnderline(True)
        else:
            self.text_edit.setFontUnderline(False)

    def set_strikeout(self) -> None:
        # Strikeout the text if the "strikeout_btn" is checked, else make it not stroke out
        font = self.text_edit.currentFont()
        if self.sender().isChecked():
            font.setStrikeOut(True)
            self.text_edit.setCurrentFont(font)
        else:
            font.setStrikeOut(False)
            self.text_edit.setCurrentFont(font)


class ImageEditingWindow(QMainWindow):
    # TODO
    pass


class AudioEditingWindow(QMainWindow):
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

    windows.setFixedHeight(600)
    windows.setFixedWidth(800)
    windows.setWindowTitle("Media Editor")

    windows.show()

    sys.exit(app.exec_())
