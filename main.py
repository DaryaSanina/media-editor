import os
import sys
from tempfile import NamedTemporaryFile

from PIL import Image
from PIL.ImageQt import ImageQt
import pilgram

import librosa
import soundfile as sf
from numpy import array as np_array

from PyQt5 import uic
from PyQt5.QtGui import QPixmap, QFont, QKeyEvent, QIcon, QPainter, QPaintEvent, QMouseEvent, QPen
from PyQt5.QtGui import QColor, QCloseEvent
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QInputDialog, QFileDialog, QMessageBox
from PyQt5.QtWidgets import QStackedWidget, QDialog, QRubberBand, QColorDialog, QErrorMessage
from PyQt5.QtCore import Qt, QRect, QSize, QPoint, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

HTML_EXTENSIONS = ['.htm', '.html']
TEXT_EXTENSIONS = ['.txt']
IMAGE_EXTENSIONS = ['.png', '.jpg', '.bmp', '.gif', '.jpeg', '.pbm', '.tiff', '.svg', '.xbm']
AUDIO_EXTENSIONS = ['.mp3', '.wav']

filename = ''


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi(os.path.abspath('designs/main_window.ui'), self)

        self.create_new_btn.clicked.connect(self.choose_what_to_create)
        self.open_btn.clicked.connect(self.open)

        # Displaying the logo in the main window
        self.title_image_pixmap = QPixmap('designs/title_image.jpg')
        self.title_image = QLabel(self)
        self.title_image.move(160, 50)
        self.title_image.resize(480, 125)
        self.title_image.setPixmap(self.title_image_pixmap)

        self.loading_label.hide()

    def closeEvent(self, event: QCloseEvent) -> None:
        answer = QMessageBox.question(self, "Confirm exit", "Are you sure you want to exit?",
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer == QMessageBox.Yes:
            image_editing_window.delete_temporary_files()
            audio_editing_window.delete_temporary_files()
            event.accept()
        else:
            event.ignore()

    def choose_what_to_create(self) -> None:
        # Creating an input dialog to ask the user what editor to open
        file_type, ok_pressed = QInputDialog.getItem(self, "Choose media type",
                                                     "Choose what you want to create:",
                                                     ("Image", "Text"), 0, False)
        if ok_pressed:
            # Opening the editor that the user wants to open
            if file_type == "Image":
                windows.setCurrentIndex(2)
                image_editing_window.new()
            elif file_type == "Text":
                windows.setCurrentIndex(1)

    def open(self) -> None:
        # Getting the filename and the file extension
        global filename
        filename = QFileDialog.getOpenFileName(self, "Choose file", '',
                                               'Text Document (*.txt);;HTML Document (*.html);;'
                                               'HTML Document (*.htm);;Image (*.png);;'
                                               'Image (*.jpg);;Image (*.bmp);;Image (*.gif);;'
                                               'Image (*.jpeg);;Image (*.pbm);;Image (*.tiff);;'
                                               'Image (*.svg);;Image (*.xbm);;Audio File (*.mp3);;'
                                               'Audio File (*.wav);;All Files (*)')[0]
        extension = filename[filename.rfind('.')::]

        self.loading_label.show()

        # Guessing what editor the user wants to open
        if extension in TEXT_EXTENSIONS or extension in HTML_EXTENSIONS \
                and QMessageBox.question(self, "File type guess",
                                         "Do you want to edit a text document?",
                                         QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            # Reading the text from the file
            with open(filename, 'r', encoding='utf-8') as source_file:
                text_editing_window.text_edit.setText(source_file.read())

            self.loading_label.hide()

            windows.setCurrentIndex(1)

        elif extension in IMAGE_EXTENSIONS \
                and QMessageBox.question(self, 'File type guess', "Do you want to edit an image?",
                                         QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            # Displaying the image from the opened file
            image_editing_window.image.setPixmap(QPixmap(filename)
                                                 .scaled(620, 470, Qt.KeepAspectRatio))
            image_editing_window.is_saved = True

            # Creating a temporary file with the opened image for the unsaved changes
            image_editing_window.cur_temporary_file = NamedTemporaryFile(suffix='.jpg', delete=False)
            temporary_file_name = image_editing_window.cur_temporary_file.name
            temporary_file_extension = temporary_file_name[
                                       temporary_file_name.rfind('.')::][1::].upper()
            image_editing_window.image.pixmap().save(temporary_file_name,
                                                     temporary_file_extension)
            image_editing_window.temporary_file_names.append(temporary_file_name)

            self.loading_label.hide()

            windows.setCurrentIndex(2)

        elif extension in AUDIO_EXTENSIONS \
                and QMessageBox.question(self, 'File type guess',
                                         "Do you want to edit an audio file?",
                                         QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            # Loading the audio
            url = QUrl.fromLocalFile(filename)
            content = QMediaContent(url)
            audio_editing_window.player.setMedia(content)

            try:
                audio_editing_window.cur_waveform, \
                    audio_editing_window.original_stream_rate = librosa.load(filename)
                audio_editing_window.cur_stream_rate \
                    = audio_editing_window.original_stream_rate

                # Creating a temporary file with the audio for the unsaved changes
                audio_editing_window.delete_temporary_files()

                audio_editing_window.cur_temporary_file = NamedTemporaryFile(suffix='.wav',
                                                                             delete=False)
                temporary_file_name = audio_editing_window.cur_temporary_file.name
                sf.write(temporary_file_name, audio_editing_window.cur_waveform,
                         audio_editing_window.cur_stream_rate, 'PCM_24')

                audio_editing_window.temporary_file_names = [temporary_file_name]
                audio_editing_window.waveforms = [audio_editing_window.cur_waveform]
                audio_editing_window.stream_rates = [audio_editing_window.cur_stream_rate]
                audio_editing_window.temporary_file_index = 0

                windows.setCurrentIndex(3)
            except:
                error_message = QErrorMessage(self)
                error_message.showMessage("Current format is not supported by ffmpeg\n"
                                          "or you haven't installed ffmpeg.")
            self.loading_label.hide()

        elif extension != '':
            # If the guess isn't correct,
            # creating an input dialog to ask the user what editor to open
            file_type, ok_pressed = QInputDialog.getItem(self, "Choose media type",
                                                         "Choose what you want to edit:",
                                                         ("Image", "Text", "Audio"),
                                                         0, False)

            # Opening the editor that the user wants to open
            self.loading_label.hide()

            if ok_pressed:
                self.loading_label.show()
                try:
                    if file_type == "Text":
                        # Reading the text from the file
                        with open(filename, 'r', encoding='utf-8') as source_file:
                            text_editing_window.text_edit.setText(source_file.read())

                        windows.setCurrentIndex(1)

                    elif file_type == "Image":
                        # Displaying the image from the opened file
                        image_editing_window.image.setPixmap(QPixmap(filename)
                                                             .scaled(620, 470, Qt.KeepAspectRatio))
                        image_editing_window.is_saved = True

                        # Creating a temporary file with the opened image for the unsaved changes
                        image_editing_window.cur_temporary_file = NamedTemporaryFile(suffix='.jpg',
                                                                                     delete=False)
                        temporary_file_name = image_editing_window.cur_temporary_file.name
                        temporary_file_extension = temporary_file_name[
                                                   temporary_file_name.rfind('.')::][1::].upper()
                        image_editing_window.image.pixmap().save(temporary_file_name,
                                                                 temporary_file_extension)
                        image_editing_window.temporary_file_names.append(temporary_file_name)

                        windows.setCurrentIndex(2)

                    elif file_type == "Audio":
                        # Loading the audio
                        url = QUrl.fromLocalFile(filename)
                        content = QMediaContent(url)
                        audio_editing_window.player.setMedia(content)

                        try:
                            audio_editing_window.cur_waveform, \
                            audio_editing_window.original_stream_rate = librosa.load(filename)
                            audio_editing_window.cur_stream_rate \
                                = audio_editing_window.original_stream_rate

                            # Creating a temporary file with the audio for the unsaved changes
                            audio_editing_window.delete_temporary_files()

                            audio_editing_window.cur_temporary_file = NamedTemporaryFile(
                                suffix='.wav',
                                delete=False)
                            temporary_file_name = audio_editing_window.cur_temporary_file.name
                            sf.write(temporary_file_name, audio_editing_window.cur_waveform,
                                     audio_editing_window.cur_stream_rate, 'PCM_24')

                            audio_editing_window.temporary_file_names = [temporary_file_name]
                            audio_editing_window.waveforms = [audio_editing_window.cur_waveform]
                            audio_editing_window.stream_rates = [
                                audio_editing_window.cur_stream_rate]
                            audio_editing_window.temporary_file_index = 0

                            windows.setCurrentIndex(3)

                        except:
                            error_message = QErrorMessage(self)
                            error_message.showMessage("Current format is not supported by ffmpeg\n"
                                                      "or you haven't installed ffmpeg.")
                except:
                    error_message = QErrorMessage(self)
                    error_message.showMessage("Can't read the file")

                self.loading_label.hide()
        else:
            self.loading_label.hide()


class TextEditingWindow(QMainWindow):
    def __init__(self):
        super(TextEditingWindow, self).__init__()
        uic.loadUi(os.path.abspath('designs/text_editor_window.ui'), self)

        self.new_btn.clicked.connect(self.new)
        self.open_btn.clicked.connect(self.open)
        self.save_btn.clicked.connect(self.save)
        self.save_as_btn.clicked.connect(self.save_as)
        self.home_btn.clicked.connect(self.return_home)

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

        new_filename = QFileDialog.getOpenFileName(self, 'Choose file', '',
                                                   'Text Document (*.txt);;HTML Document (*.html);;'
                                                   'HTML Document (*.htm);;All Files (*)')[0]
        if new_filename:
            # If the user didn't click "Cancel":
            filename = new_filename
            with open(filename, 'r', encoding='utf-8') as source_file:
                self.text_edit.setText(source_file.read())

    def save(self) -> None:
        if not filename:
            # If the file is new:
            self.save_as()
        with open(filename, 'w', encoding='utf-8') as dest_file:
            extension = filename[filename.rfind('.')::]
            # If the extension of the file the user wants to save the text to is an html extension,
            # saving the text with formatting,
            # else saving the text without formatting
            text = self.text_edit.toHtml() if extension in HTML_EXTENSIONS \
                else self.text_edit.toPlainText()
            dest_file.write(text)

    def save_as(self) -> None:
        global filename

        new_filename = QFileDialog.getSaveFileName(self, 'Save file', '',
                                                   'Text Document (*.txt);;HTML Document (*.html);;'
                                                   'HTML Document (*.htm);;All Files (*)')[0]
        if new_filename:
            filename = new_filename
            # If the user didn't click "Cancel":
            with open(filename, 'w', encoding='utf-8') as dest_file:
                dest_file.write(self.text_edit.toPlainText())

    def return_home(self) -> None:
        global filename

        answer = QMessageBox.question(self, "Confirm exit",
                                      "Are you sure you want to exit the text editor?",
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer == QMessageBox.Yes:
            filename = ''
            windows.setCurrentIndex(0)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if int(event.modifiers()) == Qt.ControlModifier and event.key() == Qt.Key_S:
            # "Ctrl" + "S" shortcut to save the file
            self.save()
        elif int(event.modifiers()) == (Qt.ControlModifier + Qt.ShiftModifier) \
                and event.key() == Qt.Key_S:
            # "Ctrl" + "Shift" + "S" shortcut to save the file
            self.save_as()

    def change_font(self, font: QFont) -> None:
        if self.strikeout_btn.isChecked():
            font.setStrikeOut(True)
        self.text_edit.setCurrentFont(font)
        if self.bold_btn.isChecked():
            self.text_edit.setFontWeight(QFont.Bold)
        if self.italic_btn.isChecked():
            self.text_edit.setFontItalic(True)
        if self.underline_btn.isChecked():
            self.text_edit.setFontUnderline(True)
        self.text_edit.setFontPointSize(self.font_size_spin_box.value())

    def change_font_point_size(self, font_point_size: int) -> None:
        self.text_edit.setFontPointSize(font_point_size)

    def set_bold(self) -> None:
        # Making the text bold if the "bold_btn" is checked, else making it not bold
        if self.sender().isChecked():
            self.text_edit.setFontWeight(QFont.Bold)
        else:
            self.text_edit.setFontWeight(QFont.NoFontMerging)

    def set_italic(self) -> None:
        # Making the text italic if the "italic_btn" is checked, else making it not italic
        if self.sender().isChecked():
            self.text_edit.setFontItalic(True)
        else:
            self.text_edit.setFontItalic(False)

    def set_underlined(self) -> None:
        # Underlining the text if the "underline_btn" is checked, else making it not underlined
        if self.sender().isChecked():
            self.text_edit.setFontUnderline(True)
        else:
            self.text_edit.setFontUnderline(False)

    def set_strikeout(self) -> None:
        # Striking out the text if the "strikeout_btn" is checked, else making it not stroke out
        font = self.text_edit.currentFont()
        if self.sender().isChecked():
            font.setStrikeOut(True)
            self.text_edit.setCurrentFont(font)
        else:
            font.setStrikeOut(False)
            self.text_edit.setCurrentFont(font)
        if self.bold_btn.isChecked():
            self.text_edit.setFontWeight(QFont.Bold)
        if self.italic_btn.isChecked():
            self.text_edit.setFontItalic(True)
        if self.underline_btn.isChecked():
            self.text_edit.setFontUnderline(True)
        self.text_edit.setFontPointSize(self.font_size_spin_box.value())


class ImageEditingWindow(QMainWindow):
    def __init__(self):
        super(ImageEditingWindow, self).__init__()
        uic.loadUi(os.path.abspath('designs/image_editor_window.ui'), self)

        # Creating a label that will display the opened image or a new white image
        self.image = QLabel(self)
        self.image.move(170, 80)
        self.image.setAlignment(Qt.AlignLeft)

        # Assigning the width and the height of the image to 0
        self.image_width = 0
        self.image_height = 0

        self.is_saved = False
        self.cur_temporary_file = None
        self.temporary_file_names = list()
        self.temporary_file_index = 0

        self.pixmap_without_filters = None

        self.rubber_band = None
        self.rubber_band_origin = QPoint()

        self.new_btn.clicked.connect(self.new)
        self.open_btn.clicked.connect(self.open)
        self.save_btn.clicked.connect(self.save)
        self.save_as_btn.clicked.connect(self.save_as)
        self.home_btn.clicked.connect(self.return_home)
        self.undo_btn.clicked.connect(self.undo)
        self.redo_btn.clicked.connect(self.redo)

        self.filter_combo_box.currentTextChanged.connect(self.change_filter)
        self.brush_size_spin_box.valueChanged.connect(self.change_brush_size)
        self.brush_opacity_spin_box.valueChanged.connect(self.change_brush_opacity)
        self.change_color_btn.clicked.connect(self.change_brush_color)

        self.is_drawing = False
        self.is_erasing = False
        self.is_drawing_line = False
        self.is_drawing_rectangle = False
        self.is_drawing_ellipse = False
        self.last_pen_point = QPoint()
        self.brush_size = 5
        self.brush_color = QColor(0, 0, 0, 255)  # (0, 0, 0, 255) is black color

    def new(self) -> None:
        global filename

        # Creating a dialog
        # to ask the user about the width and the height of the picture to create
        dialog = ChooseImageSizeDialog()
        dialog.exec_()
        if dialog.result() == 1:
            # If the user has clicked "OK", changing the window to the image editor
            windows.setCurrentIndex(2)
            if dialog.unit_combo_box.currentText() == "in":
                # If the user has chosen inches as units of the size:

                # Getting the dots per inch value of current screen
                dpi = app.screens()[0].physicalDotsPerInch()

                # Calculating the width and the height of the image in pixels
                self.image_width = int(dialog.width_spin_box.value() * dpi)
                self.image_height = int(dialog.height_spin_box.value() * dpi)
            elif dialog.unit_combo_box.currentText() == "cm":
                # If the user has chosen centimeters as units of the size:

                # Calculating the width and the height of the image in inches
                image_width_inches = dialog.width_spin_box.value() / 2.54
                image_height_inches = dialog.height_spin_box.value() / 2.54

                # Getting the dots per inch value of current screen
                dpi = app.screens()[0].physicalDotsPerInch()

                # Calculating the width and the height of the image in pixels
                self.image_width = int(image_width_inches * dpi)
                self.image_height = int(image_height_inches * dpi)
            elif dialog.unit_combo_box.currentText() == "px":
                # If the user has chosen pixels as units of the size,
                # setting the width and the height of the image to the data the user has entered
                self.image_width = dialog.width_spin_box.value()
                self.image_height = dialog.height_spin_box.value()

        pixmap = QPixmap(self.image_width, self.image_height).scaled(620, 470, Qt.KeepAspectRatio)
        pixmap.fill(Qt.white)
        self.image.setPixmap(pixmap)

        self.pixmap_without_filters = QPixmap(self.image_width, self.image_height)
        self.pixmap_without_filters.fill(Qt.white)

        self.is_saved = False

        # Create a temporary file in the main.py's directory
        self.cur_temporary_file = NamedTemporaryFile(suffix='.jpg', delete=False)
        self.image.pixmap().save(self.cur_temporary_file.name)
        self.temporary_file_names = [self.cur_temporary_file.name]
        self.temporary_file_index = 0

        filename = ''

    def open(self) -> None:
        global filename

        # Getting the filename
        new_filename = QFileDialog.getOpenFileName(self, 'Choose file', '',
                                                   'Image (*.jpg);;Image (*.bmp);;Image (*.gif);;'
                                                   'Image (*.jpeg);;Image (*.pbm);;Image (*.tiff);;'
                                                   'Image (*.svg);;Image (*.xbm);;All Files (*)')[0]

        if new_filename:
            # If the user didn't click "Cancel":
            # Creating a temporary file with the opened image for the unsaved changes
            image_editing_window.cur_temporary_file = NamedTemporaryFile(suffix='.jpg',
                                                                         delete=False)
            temporary_file_name = image_editing_window.cur_temporary_file.name
            temporary_file_extension = temporary_file_name[
                                       temporary_file_name.rfind('.')::][1::].upper()
            image_editing_window.image.pixmap().save(temporary_file_name,
                                                     temporary_file_extension)
            self.temporary_file_names = [self.cur_temporary_file.name]
            self.temporary_file_index = 0

            # Displaying the image from the opened file
            filename = new_filename
            image_editing_window.image.setPixmap(QPixmap(filename)
                                                 .scaled(620, 470, Qt.KeepAspectRatio))
            image_editing_window.is_saved = True

    def save(self) -> None:
        if not filename:
            # If the file is new:
            self.save_as()

        else:
            extension = filename[filename.rfind('.')::][1::].upper()
            self.image.pixmap().save(filename, extension)
            self.is_saved = True

            # Deleting the created temporary file
            if self.cur_temporary_file is not None:
                self.cur_temporary_file.close()
                os.unlink(self.cur_temporary_file.name)
                self.cur_temporary_file = None

    def save_as(self) -> None:
        global filename

        new_filename = QFileDialog.getSaveFileName(self, 'Save the file', '',
                                                   'Image (*.jpg);;Image (*.bmp);;Image (*.gif);;'
                                                   'Image (*.jpeg);;Image (*.pbm);;Image (*.tiff);;'
                                                   'Image (*.svg);;Image (*.xbm);;All Files (*)')[0]

        if new_filename:
            # If the user didn't click "Cancel":
            filename = new_filename
            extension = filename[filename.rfind('.')::][1::].upper()
            self.image.pixmap().save(filename, extension)
            self.is_saved = True

            # Deleting the created temporary file
            if self.cur_temporary_file is not None:
                self.cur_temporary_file.close()
                os.unlink(self.cur_temporary_file.name)
                self.cur_temporary_file = None

    def return_home(self) -> None:
        global filename

        answer = QMessageBox.question(self, "Confirm exit",
                                      "Are you sure you want to exit the image editor?",
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer == QMessageBox.Yes:
            filename = ''

            self.delete_temporary_files()

            windows.setCurrentIndex(0)

    def delete_temporary_files(self):
        if self.cur_temporary_file is not None:
            self.cur_temporary_file.close()
            for temporary_file_name in self.temporary_file_names:
                os.unlink(temporary_file_name)
            self.cur_temporary_file = None

    def undo(self) -> None:
        self.temporary_file_index -= 1

        # Updating the pixmap
        self.cur_temporary_file.close()
        temporary_file_name = self.temporary_file_names[self.temporary_file_index]
        self.image.setPixmap(QPixmap(temporary_file_name).scaled(620, 470, Qt.KeepAspectRatio))

        # Updating cur_temporary_file
        self.cur_temporary_file = open(self.temporary_file_names[self.temporary_file_index])
        self.cur_temporary_file.close()

        if self.temporary_file_index <= 0:
            self.undo_btn.setEnabled(False)
        if self.temporary_file_index < len(self.temporary_file_names):
            self.redo_btn.setEnabled(True)

    def redo(self) -> None:
        self.temporary_file_index += 1

        # Updating the pixmap
        self.cur_temporary_file.close()
        temporary_file_name = self.temporary_file_names[self.temporary_file_index]
        self.image.setPixmap(QPixmap(temporary_file_name).scaled(620, 470, Qt.KeepAspectRatio))

        # Updating cur_temporary_file
        self.cur_temporary_file = open(self.temporary_file_names[self.temporary_file_index])
        self.cur_temporary_file.close()

        if self.temporary_file_index >= len(self.temporary_file_names) - 1:
            self.redo_btn.setEnabled(False)
        if self.temporary_file_index > 0:
            self.undo_btn.setEnabled(True)

    def update_temporary_files(self):
        # Deleting all the temporary files after current index
        if self.temporary_file_index < len(self.temporary_file_names) - 1:
            if self.cur_temporary_file is not None:
                for temporary_file_name in \
                        self.temporary_file_names[self.temporary_file_index + 1::]:
                    try:
                        os.unlink(temporary_file_name)
                    except PermissionError:
                        self.cur_temporary_file.close()
                        os.unlink(temporary_file_name)
            self.temporary_file_names = self.temporary_file_names[:self.temporary_file_index + 1:]

        # Creating a new temporary file
        self.cur_temporary_file = NamedTemporaryFile(suffix='.jpg', delete=False)
        self.image.pixmap().save(self.cur_temporary_file.name, 'JPG')
        self.temporary_file_names.append(self.cur_temporary_file.name)
        self.temporary_file_index += 1
        self.cur_temporary_file.close()

        if not self.undo_btn.isEnabled():
            self.undo_btn.setEnabled(True)

        if self.redo_btn.isEnabled() \
                and self.temporary_file_index == len(self.temporary_file_names) - 1:
            self.redo_btn.setEnabled(False)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if int(event.modifiers()) == Qt.ControlModifier and event.key() == Qt.Key_S:
            # "Ctrl" + "S" shortcut to save the file
            self.save()
        elif int(event.modifiers()) == (Qt.ControlModifier + Qt.ShiftModifier) \
                and event.key() == Qt.Key_S:
            # "Ctrl" + "Shift" + "S" shortcut to save the file
            self.save_as()
        elif int(event.modifiers()) == Qt.ControlModifier and event.key() == Qt.Key_Z:
            # "Ctrl" + "Z" shortcut to undo the changes
            self.undo()
        elif int(event.modifiers()) == (Qt.ControlModifier + Qt.ShiftModifier) \
                and event.key() == Qt.Key_Z:
            # "Ctrl" + "Shift" + "Z" shortcut to redo the changes
            self.redo()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if (self.select_btn.isChecked() or self.crop_btn.isChecked()) \
                and event.button() == Qt.LeftButton:
            # If only button "Crop" or "Select" is checked,
            # start creating the rubber band
            if 170 <= event.pos().x() <= 170 + self.image.pixmap().width() \
                    and 80 <= event.pos().y() <= 80 + self.image.pixmap().height():
                # If the user has clicked inside the image:
                if self.rubber_band is None:
                    # If the selection is for the first time, creating a new rubber band:
                    self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)

                # Setting the origin of the rubber band to the position of the cursor
                self.rubber_band_origin = event.pos()
                self.rubber_band.setGeometry(QRect(self.rubber_band_origin, QSize()))

                self.rubber_band.show()

        elif self.brush_btn.isChecked() and event.button() == Qt.LeftButton:
            self.is_drawing = True
            self.last_pen_point = QPoint(event.pos().x() - 170, event.pos().y() - 80)
        elif self.eraser_btn.isChecked() and event.button() == Qt.LeftButton:
            self.is_erasing = True
            self.last_pen_point = QPoint(event.pos().x() - 170, event.pos().y() - 80)
        elif self.line_btn.isChecked() and event.button() == Qt.LeftButton:
            self.is_drawing_line = True
            self.last_pen_point = QPoint(event.pos().x() - 170, event.pos().y() - 80)
        elif self.rectangle_btn.isChecked() and event.button() == Qt.LeftButton:
            self.is_drawing_rectangle = True
            self.last_pen_point = QPoint(event.pos().x() - 170, event.pos().y() - 80)
        elif self.ellipse_btn.isChecked() and event.button() == Qt.LeftButton:
            self.is_drawing_ellipse = True
            self.last_pen_point = QPoint(event.pos().x() - 170, event.pos().y() - 80)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self.is_drawing and not self.is_erasing and not self.is_drawing_line \
                and not self.is_drawing_rectangle and not self.is_drawing_ellipse \
                and self.rubber_band_origin is not None:
            # If the left button of the mouse was pressed inside the image,
            # selecting the part of the image that the user wants to select

            selection_horizontal_end_point = event.pos().x()
            # If the cursor is outside the image, setting selection_horizontal_end_point
            # to the nearest to the cursor possible spot
            if selection_horizontal_end_point < 170:
                selection_horizontal_end_point = 170
            elif selection_horizontal_end_point > 170 + self.image.pixmap().width():
                selection_horizontal_end_point = 170 + self.image.pixmap().width()

            selection_vertical_end_point = event.pos().y()
            # If the cursor is outside the image, setting selection_vertical_end_point
            # to the nearest to the cursor possible spot
            if selection_vertical_end_point < 80:
                selection_vertical_end_point = 80
            elif selection_vertical_end_point > 80 + self.image.pixmap().height():
                selection_vertical_end_point = 80 + self.image.pixmap().height()

            # Updating the rubber band
            self.rubber_band.setGeometry(QRect(self.rubber_band_origin,
                                               QPoint(selection_horizontal_end_point,
                                                      selection_vertical_end_point)).normalized())

        elif self.is_drawing or self.is_erasing:
            # Creating a QPainter object with the opened image
            painter = QPainter(self.image.pixmap())
            if self.is_drawing:
                color = self.brush_color
            else:  # if self.is_erasing
                color = QColor(255, 255, 255, 255)  # (255, 255, 255, 255) is white color
            painter.setPen(QPen(color, self.brush_size, Qt.SolidLine, Qt.RoundCap,
                                Qt.RoundJoin))
            painter.drawLine(self.last_pen_point,
                             QPoint(event.pos().x() - 170,
                                    event.pos().y() - 80))
            self.last_pen_point = QPoint(event.pos().x() - 170,
                                         event.pos().y() - 80)
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.select_btn.isChecked() and self.rubber_band is not None:
            # If the user is selecting a part of an image:
            self.rubber_band.hide()

        elif self.crop_btn.isChecked() and self.rubber_band is not None:
            # If the user is cropping the image:

            # Getting the selected part of the image as a QRect
            selection_q_rect = self.rubber_band.geometry()
            selection_q_rect.setX(selection_q_rect.x() - 170)
            selection_q_rect.setY(selection_q_rect.y() - 80)
            selection_q_rect.setWidth(selection_q_rect.width() - 170)
            selection_q_rect.setHeight(selection_q_rect.height() - 80)

            # Updating the image
            self.image.setPixmap(self.image.pixmap().copy(selection_q_rect)
                                 .scaled(620, 470, Qt.KeepAspectRatio))
            self.pixmap_without_filters = self.image.pixmap()
            self.image_width = self.image.pixmap().width()
            self.image_height = self.image.pixmap().height()

            self.is_saved = False
            self.update_temporary_files()

            self.rubber_band.hide()

        elif self.is_drawing:
            self.is_drawing = False
            self.is_saved = False
            self.update_temporary_files()

        elif self.is_erasing:
            self.is_erasing = False
            self.is_saved = False
            self.update_temporary_files()

        elif self.is_drawing_line:
            # Creating a QPainter object with the opened image
            painter = QPainter(self.image.pixmap())
            painter.setPen(QPen(self.brush_color, self.brush_size, Qt.SolidLine, Qt.RoundCap,
                                Qt.RoundJoin))
            painter.drawLine(self.last_pen_point,
                             QPoint(event.pos().x() - 170, event.pos().y() - 80))
            self.update()
            self.is_drawing_line = False
            self.is_saved = False
            self.update_temporary_files()

        elif self.is_drawing_rectangle:
            # Creating a QPainter object with the opened image
            painter = QPainter(self.image.pixmap())
            painter.setPen(QPen(self.brush_color, self.brush_size, Qt.SolidLine, Qt.RoundCap,
                                Qt.RoundJoin))
            painter.drawRect(QRect(self.last_pen_point,
                                   QPoint(event.pos().x() - 170,
                                          event.pos().y() - 80)).normalized())
            self.update()
            self.is_drawing_rectangle = False
            self.is_saved = False
            self.update_temporary_files()

        elif self.is_drawing_ellipse:
            # Creating a QPainter object with the opened image
            painter = QPainter(self.image.pixmap())
            painter.setPen(QPen(self.brush_color, self.brush_size, Qt.SolidLine, Qt.RoundCap,
                                Qt.RoundJoin))
            painter.drawEllipse(QRect(self.last_pen_point,
                                      QPoint(event.pos().x() - 170,
                                             event.pos().y() - 80)).normalized())
            self.update()
            self.is_drawing_ellipse = False
            self.is_saved = False
            self.update_temporary_files()

    def paintEvent(self, event: QPaintEvent) -> None:
        self.image.resize(620, 470)
        if self.image.pixmap() is not None:
            # If the user has opened an image:
            self.image_width = self.image.pixmap().width()
            self.image_height = self.image.pixmap().height()

            self.pixmap_without_filters = QPixmap(filename).scaled(620, 470, Qt.KeepAspectRatio)
        else:
            # If the user has created a new image, filling it with white color
            pixmap = QPixmap(self.image_width, self.image_height)
            pixmap.fill(Qt.white)
            self.image.setPixmap(pixmap)

            self.pixmap_without_filters = QPixmap(self.image_width, self.image_height)
            self.pixmap_without_filters.fill(Qt.white)

    def change_filter(self, image_filter: str) -> None:
        if image_filter == "Original":
            # Removing all the applied filters from the image
            self.image.setPixmap(self.pixmap_without_filters)
        else:
            if self.is_saved:
                pil_image = Image.open(filename)
            else:
                pil_image = Image.open(self.cur_temporary_file.name)

            # Applying the chosen filter
            if image_filter == "Clarendon":
                pil_image = pilgram.clarendon(pil_image).convert('RGBA')
            elif image_filter == "Gingham":
                pil_image = pilgram.gingham(pil_image).convert('RGBA')
            elif image_filter == "Reyes":
                pil_image = pilgram.reyes(pil_image).convert('RGBA')
            elif image_filter == "Mayfair":
                pil_image = pilgram.mayfair(pil_image).convert('RGBA')
            else:
                # If the filter is not from Instagram
                self.image_width, self.image_height = pil_image.size

                # For each pixel getting its red, green and blue component if the mode is 'RGB'
                # and red, green, blue and alpha component if the mode is 'RGBA'
                pixels = pil_image.load()

                for i in range(self.image_width):
                    for j in range(self.image_height):
                        # The mode is 'RGB', getting the pixel's red, green and blue component
                        r, g, b = pixels[i, j]
                        if image_filter == "Only red":
                            # Leaving only red pixel's component
                            g, b = 0, 0
                        elif image_filter == "Only green":
                            # Leaving only green pixel's component
                            r, b = 0, 0
                        elif image_filter == "Only blue":
                            # Leaving only blue pixel's component
                            r, g = 0, 0
                        elif image_filter == "Red and green":
                            # Leaving only red and green pixel's components
                            b = 0
                        elif image_filter == "Red and blue":
                            # Leaving only red and blue pixel's components
                            g = 0
                        elif image_filter == "Green and blue":
                            # Leaving only green and blue pixel's components
                            r = 0
                        elif image_filter == "Negative":
                            # Inverting red, green and blue pixel's components
                            r = 255 - r
                            g = 255 - g
                            b = 255 - b
                        elif image_filter == "Black and white":
                            # Setting red, green and blue pixel's components to their middle value
                            middle_color = (r + g + b) // 3
                            r = middle_color
                            g = middle_color
                            b = middle_color

                        # Updating the pixel
                        pil_image.putpixel((i, j), (r, g, b))

            # Converting the updated PIL Image image to QPixmap format
            # and applying it to the image label
            pil_image = pil_image.convert('RGBA')
            image_qt_image = ImageQt(pil_image)
            pixmap = QPixmap.fromImage(image_qt_image).scaled(620, 470, Qt.KeepAspectRatio)
            self.image_width = pixmap.width()
            self.image_height = pixmap.height()
            self.image.setPixmap(pixmap)

            self.update_temporary_files()

    def change_brush_size(self, size: float) -> None:
        self.brush_size = size

    def change_brush_opacity(self, opacity_percent: float) -> None:
        self.brush_color.setAlpha(int(250 * (opacity_percent / 100)))

    def change_brush_color(self) -> None:
        color = QColorDialog().getColor(self.brush_color)
        if color.isValid():
            self.brush_color = color

            # Change the background color of the color changing button (change_color_btn)
            self.sender().setStyleSheet(f"background-color: {color.name()}")


class AudioEditingWindow(QMainWindow):
    def __init__(self):
        super(AudioEditingWindow, self).__init__()
        uic.loadUi(os.path.abspath('designs/audio_editor_window.ui'), self)

        self.player = QMediaPlayer()
        self.automatically_changed_player_position = False
        self.player.positionChanged.connect(self.player_position_changed)

        self.open_btn.clicked.connect(self.open)
        self.save_btn.clicked.connect(self.save)
        self.save_as_btn.clicked.connect(self.save_as)
        self.home_btn.clicked.connect(self.return_home)
        self.undo_btn.clicked.connect(self.undo)
        self.redo_btn.clicked.connect(self.redo)
        self.loading_label.hide()

        self.play_pause_btn.clicked.connect(self.play)
        self.stop_btn.clicked.connect(self.stop)
        self.rewind_slider.valueChanged.connect(self.rewind)
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.pace_slider.valueChanged.connect(self.change_pace)
        self.automatically_changed_pace_slider_position = False
        self.crop_btn.clicked.connect(self.crop)

        self.temporary_file_names = list()
        self.waveforms = list()
        self.stream_rates = list()
        self.temporary_file_index = 0

        self.cur_temporary_file = None
        self.cur_waveform = None
        self.cur_stream_rate = None

    def open(self) -> None:
        global filename

        self.loading_label.show()

        # Getting the filename
        new_filename = QFileDialog.getOpenFileName(self, 'Choose file', '',
                                                   'Audio File (*.mp3);;Audio File (*.wav)'
                                                   ';;All Files (*)')[0]

        if new_filename:
            # If the user didn't click "Cancel":
            filename = new_filename

            # Loading the audio
            url = QUrl.fromLocalFile(filename)
            content = QMediaContent(url)
            self.player.setMedia(content)

            try:
                self.cur_waveform, \
                    self.cur_stream_rate = librosa.load(filename)

                # Creating a temporary file
                self.delete_temporary_files()

                self.cur_temporary_file = NamedTemporaryFile(suffix='.wav', delete=False)
                sf.write(self.cur_temporary_file.name, self.cur_waveform, self.cur_stream_rate,
                         'PCM_24')

                self.temporary_file_names = [self.cur_temporary_file.name]
                self.waveforms = [self.cur_waveform]
                self.stream_rates = [self.cur_stream_rate]
                self.temporary_file_index = 0

                self.undo_btn.setEnabled(False)
                self.redo_btn.setEnabled(False)
            except:
                error_message = QErrorMessage(self)
                error_message.showMessage("Current format is not supported by ffmpeg\n"
                                          "or you haven't installed ffmpeg.")

        self.loading_label.hide()

    def save(self) -> None:
        global filename

        if not filename:  # if the file is new:
            self.save_as()

        else:
            extension = filename[filename.rfind('.')::][1::].upper()
            if extension in sf.available_formats() \
                    and filename[filename.rfind('.')::] in AUDIO_EXTENSIONS:
                # If current format is available to save with soundfile:
                sf.write(filename, self.cur_waveform, self.cur_stream_rate, 'PCM_24',
                         format=extension)
            else:
                error_message = QErrorMessage(self)
                error_message.showMessage("""Couldn't save the file in the chosen format.
                            It'll be saved in '.wav' format.""")
                filename = filename[:filename.rfind('.'):] + ".wav"
                sf.write(filename, self.cur_waveform, self.cur_stream_rate, 'PCM_24')

    def save_as(self) -> None:
        global filename

        # Getting the filename
        new_filename = QFileDialog.getSaveFileName(self, 'Choose file', '',
                                                   'Audio File (*.wav);;All Files (*)')[0]

        if new_filename:  # if the user didn't click "Cancel":
            filename = new_filename
            extension = filename[filename.rfind('.')::][1::].upper()
            if extension in sf.available_formats() \
                    and filename[filename.rfind('.')::] in AUDIO_EXTENSIONS:
                # If current format is available to save with soundfile:
                sf.write(filename, self.cur_waveform, self.cur_stream_rate, 'PCM_24',
                         format=extension)
            else:
                error_message = QErrorMessage(self)
                error_message.showMessage("""Couldn't save the file in the chosen format.
                It'll be saved in '.wav' format.""")
                filename = filename[:filename.rfind('.'):] + ".wav"
                sf.write(filename, self.cur_waveform, self.cur_stream_rate, 'PCM_24')

    def return_home(self) -> None:
        global filename

        answer = QMessageBox.question(self, "Confirm exit",
                                      "Are you sure you want to exit the audio editor?",
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer == QMessageBox.Yes:
            self.player.stop()
            filename = ''
            self.delete_temporary_files()
            self.temporary_file_names = list()
            self.waveforms = list()
            self.stream_rates = list()
            windows.setCurrentIndex(0)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if int(event.modifiers()) == Qt.ControlModifier and event.key() == Qt.Key_S:
            # "Ctrl" + "S" shortcut to save the file
            self.save()
        elif int(event.modifiers()) == (Qt.ControlModifier + Qt.ShiftModifier) \
                and event.key() == Qt.Key_S:
            # "Ctrl" + "Shift" + "S" shortcut to save the file
            self.save_as()
        elif int(event.modifiers()) == Qt.ControlModifier and event.key() == Qt.Key_Z:
            # "Ctrl" + "Z" shortcut to undo the changes
            self.undo()
        elif int(event.modifiers()) == (Qt.ControlModifier + Qt.ShiftModifier) \
                and event.key() == Qt.Key_Z:
            # "Ctrl" + "Shift" + "Z" shortcut to redo the changes
            self.redo()

    def delete_temporary_files(self) -> None:
        if self.cur_temporary_file is not None:
            self.cur_temporary_file.close()
            for temporary_file_name in self.temporary_file_names:
                os.unlink(temporary_file_name)
            self.cur_temporary_file = None

    def play(self) -> None:
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def stop(self) -> None:
        self.player.stop()
        self.rewind_slider.setValue(0)

    def rewind(self, rewind_slider_position: int) -> None:
        if not self.automatically_changed_player_position:
            self.player.setPosition(int(self.player.duration() * (rewind_slider_position / 1000)))

    def player_position_changed(self):
        if self.player.position() != 0:
            self.automatically_changed_player_position = True
            self.rewind_slider.setValue(round(1000 *
                                              (self.player.position() / self.player.duration())))
            self.automatically_changed_player_position = False

    def change_volume(self, volume_slider_position: int) -> None:
        self.player.setVolume(volume_slider_position)

    def undo(self) -> None:
        self.temporary_file_index -= 1

        # Updating the player
        self.cur_temporary_file.close()
        url = QUrl.fromLocalFile(self.temporary_file_names[self.temporary_file_index])
        content = QMediaContent(url)
        self.player.setMedia(content)

        # Updating cur_temporary_file, cur_waveform and cur_stream_rate
        self.cur_temporary_file = open(self.temporary_file_names[self.temporary_file_index])
        self.cur_temporary_file.close()
        self.cur_waveform = self.waveforms[self.temporary_file_index]
        self.cur_stream_rate = self.stream_rates[self.temporary_file_index]

        self.automatically_changed_pace_slider_position = True
        self.pace_slider.setValue(int(
            self.stream_rates[self.temporary_file_index] / self.stream_rates[0] * 50))
        self.automatically_changed_pace_slider_position = False

        if self.temporary_file_index <= 0:
            self.undo_btn.setEnabled(False)
        if self.temporary_file_index < len(self.temporary_file_names):
            self.redo_btn.setEnabled(True)

    def redo(self) -> None:
        self.temporary_file_index += 1

        # Updating the player
        self.cur_temporary_file.close()
        url = QUrl.fromLocalFile(self.temporary_file_names[self.temporary_file_index])
        content = QMediaContent(url)
        self.player.setMedia(content)

        # Updating cur_temporary_file, cur_waveform and cur_stream_rate
        self.cur_temporary_file = open(self.temporary_file_names[self.temporary_file_index])
        self.cur_temporary_file.close()
        self.cur_waveform = self.waveforms[self.temporary_file_index]
        self.cur_stream_rate = self.stream_rates[self.temporary_file_index]

        self.automatically_changed_pace_slider_position = True
        self.pace_slider.setValue(int(
            self.stream_rates[self.temporary_file_index] / self.stream_rates[0] * 50))
        self.automatically_changed_pace_slider_position = False

        if self.temporary_file_index >= len(self.temporary_file_names) - 1:
            self.redo_btn.setEnabled(False)
        if self.temporary_file_index > 0:
            self.undo_btn.setEnabled(True)

    def update_player_and_temporary_files(self) -> None:
        # Deleting all the temporary files after current index
        if self.temporary_file_index < len(self.temporary_file_names) - 1:
            if self.cur_temporary_file is not None:
                for temporary_file_name in \
                        self.temporary_file_names[self.temporary_file_index + 1::]:
                    try:
                        os.unlink(temporary_file_name)
                    except PermissionError:
                        self.cur_temporary_file.close()
                        os.unlink(temporary_file_name)
            self.temporary_file_names = self.temporary_file_names[:self.temporary_file_index + 1:]
            self.waveforms = self.waveforms[:self.temporary_file_index + 1:]
            self.stream_rates = self.stream_rates[:self.temporary_file_index + 1:]

        # Creating a new temporary file
        self.cur_temporary_file = NamedTemporaryFile(suffix='.wav', delete=False)
        sf.write(self.cur_temporary_file.name, self.cur_waveform, self.cur_stream_rate, 'PCM_24')
        self.temporary_file_names.append(self.cur_temporary_file.name)
        self.waveforms.append(self.cur_waveform)
        self.stream_rates.append(self.cur_stream_rate)
        self.cur_temporary_file.close()

        # Updating the player
        url = QUrl.fromLocalFile(self.cur_temporary_file.name)
        content = QMediaContent(url)
        self.player.setMedia(content)

        self.temporary_file_index += 1

        if not self.undo_btn.isEnabled():
            self.undo_btn.setEnabled(True)

        if self.redo_btn.isEnabled() \
                and self.temporary_file_index == len(self.temporary_file_names) - 1:
            self.redo_btn.setEnabled(False)

    def change_pace(self, pace_slider_position: int) -> None:
        if not self.automatically_changed_pace_slider_position:
            # Updating the stream rate
            self.cur_stream_rate = int(self.stream_rates[0] * (pace_slider_position / 50))

            self.update_player_and_temporary_files()

    def crop(self) -> None:
        # Creating a dialog to ask the user about the positions of the start and the end of the song
        dialog = CropAudioDialog(duration=self.player.duration())
        dialog.exec_()

        if dialog.result() == 1:
            # If the user has clicked "OK":
            start_slider_pos = dialog.start_slider.value()
            end_slider_pos = dialog.end_slider.value()
            if start_slider_pos >= end_slider_pos:
                # If the position of the end is less than the position of the start:
                error_message = QErrorMessage(self)
                error_message.showMessage("The audio file ends earlier than starts")
            else:
                # Updating the waveform
                start_waveform_pos = int(len(self.cur_waveform) * (start_slider_pos / 100))
                end_waveform_pos = int(len(self.cur_waveform) * (end_slider_pos / 100))
                self.cur_waveform = np_array(list(self.cur_waveform)
                                             [start_waveform_pos:end_waveform_pos + 1:])

                self.update_player_and_temporary_files()


class ChooseImageSizeDialog(QDialog):
    def __init__(self):
        super(ChooseImageSizeDialog, self).__init__()
        uic.loadUi(os.path.abspath('designs/choose_size_dialog.ui'), self)

        self.unit_combo_box.currentTextChanged.connect(self.set_default_width_and_height)

    def set_default_width_and_height(self):
        if self.sender().currentText() == "in":
            self.width_spin_box.setValue(7)
            self.height_spin_box.setValue(5)
        elif self.sender().currentText() == "px":
            self.width_spin_box.setValue(2100)
            self.height_spin_box.setValue(1500)
        elif self.sender().currentText() == "cm":
            self.width_spin_box.setValue(18)
            self.height_spin_box.setValue(13)


class CropAudioDialog(QDialog):
    def __init__(self, duration):
        super(CropAudioDialog, self).__init__()
        uic.loadUi(os.path.abspath('designs/crop_audio_dialog.ui'), self)

        self.duration = duration

        self.start_slider.valueChanged.connect(self.change_time_label)
        self.end_slider.valueChanged.connect(self.change_time_label)
        self.end_slider.setValue(1000)

    def change_time_label(self):
        total = self.duration * (self.sender().value() / 1000)

        hours = str(int(total / 1000 / 60 / 60))

        minutes = int(total / 1000 / 60 % 60)
        if minutes < 10:
            minutes = '0' + str(minutes)
        else:
            minutes = str(minutes)

        seconds = int(total / 1000 % 60)
        if seconds < 10:
            seconds = '0' + str(seconds)
        else:
            seconds = str(seconds)

        milliseconds = int(total % 1000)
        if milliseconds < 10:
            milliseconds = '00' + str(milliseconds)
        elif milliseconds < 100:
            milliseconds = '0' + str(milliseconds)
        else:
            milliseconds = str(milliseconds)

        if self.sender() == self.start_slider:
            self.current_start_label.setText(f'{hours}:{minutes}:{seconds}.{milliseconds}')
        elif self.sender() == self.end_slider:
            self.current_end_label.setText(f'{hours}:{minutes}:{seconds}.{milliseconds}')


if __name__ == '__main__':
    filename = ''

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
    windows.setWindowIcon(QIcon('designs/icons/window_icon.jpg'))
    windows.closeEvent = main_window.closeEvent

    windows.show()
    app.installEventFilter(image_editing_window)
    sys.exit(app.exec_())
