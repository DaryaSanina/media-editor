import sys

from PIL import Image
from PIL.ImageQt import ImageQt
import pilgram

import librosa
import soundfile as sf
import numpy as np

from PyQt5 import uic
from PyQt5.QtGui import QPixmap, QFont, QKeyEvent, QIcon, QPainter, QPaintEvent, QMouseEvent, QPen
from PyQt5.QtGui import QColor
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
        uic.loadUi('designs/main_window.ui', self)

        self.create_new_btn.clicked.connect(self.choose_what_to_create)
        self.open_btn.clicked.connect(self.open)

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
                image_editing_window.new()
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

            # Reading the text from the file
            with open(filename, 'r', encoding='utf-8') as source_file:
                text_editing_window.text_edit.setText(source_file.read())

        elif extension in IMAGE_EXTENSIONS \
                and QMessageBox.question(self, 'File type guess', "Do you want to edit an image?",
                                         QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            windows.setCurrentIndex(2)

            # Displaying the image from the opened file
            image_editing_window.image.setPixmap(QPixmap(filename)
                                                 .scaled(620, 470, Qt.KeepAspectRatio))
            image_editing_window.is_saved = True
        elif extension in AUDIO_EXTENSIONS \
                and QMessageBox.question(self, 'File type guess',
                                         "Do you want to edit an audio file?",
                                         QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            # Loading the audio
            url = QUrl.fromLocalFile(filename)
            content = QMediaContent(url)
            audio_editing_window.player.setMedia(content)

            try:
                audio_editing_window.waveform, \
                audio_editing_window.sample_rate = librosa.load(filename)
                windows.setCurrentIndex(3)
            except:
                error_message = QErrorMessage(self)
                error_message.showMessage("Please install ffmpeg")

        elif extension != '':
            # If the guess isn't correct,
            # creating an input dialog to ask the user what editor to open
            file_type, ok_pressed = QInputDialog.getItem(self, "Choose media type",
                                                         "Choose what you want to edit:",
                                                         ("Image", "Text", "Audio"),
                                                         0, False)

            # Opening the editor that the user wants to open
            if ok_pressed:
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
                        windows.setCurrentIndex(2)

                    elif file_type == "Audio":
                        # Loading the audio
                        url = QUrl.fromLocalFile(filename)
                        content = QMediaContent(url)
                        audio_editing_window.player.setMedia(content)

                        try:
                            audio_editing_window.waveform, \
                            audio_editing_window.sample_rate = librosa.load(filename)
                            windows.setCurrentIndex(3)

                        except:
                            error_message = QErrorMessage(self)
                            error_message.showMessage("Please install ffmpeg")
                except:
                    error_message = QErrorMessage(self)
                    error_message.showMessage("Can't read the file")


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

        new_filename = QFileDialog.getOpenFileName(self, 'Choose file', '')[0]
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

        new_filename = QFileDialog.getSaveFileName(self, 'Save file', '')[0]
        if new_filename:
            filename = new_filename
            # If the user didn't click "Cancel":
            with open(filename, 'w', encoding='utf-8') as dest_file:
                dest_file.write(self.text_edit.toPlainText())

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if int(event.modifiers()) == Qt.ControlModifier and event.key() == Qt.Key_S:
            # "Ctrl" + "S" shortcut to save the file
            self.save()
        elif int(event.modifiers()) == (Qt.ControlModifier + Qt.ShiftModifier) \
                and event.key() == Qt.Key_S:
            # "Ctrl" + "Shift" + "S" shortcut to save the file
            self.save_as()

    def change_font(self, font: QFont) -> None:
        self.text_edit.setCurrentFont(font)

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


class ChooseImageSizeDialog(QDialog):
    def __init__(self):
        super(ChooseImageSizeDialog, self).__init__()
        uic.loadUi('designs/choose_size_dialog.ui', self)

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


class ImageEditingWindow(QMainWindow):
    def __init__(self):
        super(ImageEditingWindow, self).__init__()
        uic.loadUi('designs/image_editor_window.ui', self)

        # Creating a label that will display the opened image or a new white image
        self.image = QLabel(self)
        self.image.move(170, 80)
        self.image.setAlignment(Qt.AlignLeft)

        # Assigning the width and the height of the image to 0
        self.image_width = 0
        self.image_height = 0

        self.is_saved = False

        self.pixmap_without_filters = None

        self.rubber_band = None
        self.rubber_band_origin = QPoint()

        self.new_btn.clicked.connect(self.new)
        self.open_btn.clicked.connect(self.open)
        self.save_btn.clicked.connect(self.save)
        self.save_as_btn.clicked.connect(self.save_as)
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

        pixmap = QPixmap(self.image_width, self.image_height)
        pixmap.fill(Qt.white)
        self.image.setPixmap(pixmap)

        self.pixmap_without_filters = QPixmap(self.image_width, self.image_height)
        self.pixmap_without_filters.fill(Qt.white)

        self.is_saved = False

    def open(self) -> None:
        global filename

        # Getting the filename
        new_filename = QFileDialog.getOpenFileName(self, 'Choose file', '')[0]

        if new_filename:
            # If the user didn't click "Cancel", displaying the image from the opened file
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

    def save_as(self) -> None:
        global filename

        new_filename = QFileDialog.getSaveFileName(self, 'Save the file', '')[0]

        if new_filename:
            # If the user didn't click "Cancel":
            filename = new_filename
            extension = filename[filename.rfind('.')::][1::].upper()
            self.image.pixmap().save(filename, extension)
            self.is_saved = True

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

            self.rubber_band.hide()

        elif self.is_drawing:
            self.is_drawing = False
            self.is_saved = False

        elif self.is_erasing:
            self.is_erasing = False
            self.is_saved = False

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
                # Converting the opened QPixmap image to PIL Image format
                image_qt_image = self.image.pixmap().toImage()
                data = image_qt_image.constBits().asstring(image_qt_image.byteCount())
                pil_image = Image.frombuffer('RGBA', (self.image_width, self.image_height), data,
                                             'raw', 'RGBA', 0, 1)

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
                        if self.is_saved:
                            # The mode is 'RGB', getting the pixel's red, green and blue component
                            r, g, b = pixels[i, j]
                        else:
                            # The mode is 'RGBA', getting the pixel's red, green, blue
                            # and alpha component
                            r, g, b, a = pixels[i, j]
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
                        if self.is_saved:
                            pil_image.putpixel((i, j), (r, g, b))
                        else:
                            pil_image.putpixel((i, j), (r, g, b, a))

            # Converting the updated PIL Image image to QPixmap format
            # and applying it to the image label
            pil_image = pil_image.convert('RGBA')
            image_qt_image = ImageQt(pil_image)
            pixmap = QPixmap.fromImage(image_qt_image).scaled(620, 470, Qt.KeepAspectRatio)
            self.image_width = pixmap.width()
            self.image_height = pixmap.height()
            self.image.setPixmap(pixmap)

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


class CropAudioDialog(QDialog):
    def __init__(self):
        super(CropAudioDialog, self).__init__()
        uic.loadUi('designs/crop_audio_dialog.ui', self)


class AudioEditingWindow(QMainWindow):
    def __init__(self):
        super(AudioEditingWindow, self).__init__()
        uic.loadUi('designs/audio_editor_window.ui', self)
        self.player = QMediaPlayer()

        self.open_btn.clicked.connect(self.open)
        self.save_btn.clicked.connect(self.save)
        self.save_as_btn.clicked.connect(self.save_as)

        self.play_pause_btn.clicked.connect(self.play)
        self.stop_btn.clicked.connect(self.stop)
        self.rewind_slider.valueChanged.connect(self.rewind)
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.pace_slider.valueChanged.connect(self.change_pace)
        self.crop_btn.clicked.connect(self.crop)

        self.waveform = None
        self.sample_rate = None

    def open(self):
        global filename

        # Getting the filename
        new_filename = QFileDialog.getOpenFileName(self, 'Choose file', '')[0]

        if new_filename:
            # If the user didn't click "Cancel":
            filename = new_filename

            # Loading the audio
            url = QUrl.fromLocalFile(filename)
            content = QMediaContent(url)
            self.player.setMedia(content)

            try:
                self.waveform, \
                self.sample_rate = librosa.load(filename)
            except:
                error_message = QErrorMessage(self)
                error_message.showMessage("Please install ffmpeg")

    def save(self):
        global filename

        if not filename:
            # If the file is new:
            self.save_as()

        else:
            try:
                sf.write(filename, self.waveform, self.sample_rate, 'PCM_24')
            except TypeError:
                error_message = QErrorMessage(self)
                error_message.showMessage("""Couldn't save the file in it's original format.
                It'll be saved in '.wav' format.""")
                filename = filename[:filename.rfind('.'):] + ".wav"
                sf.write(filename, self.waveform, self.sample_rate, 'PCM_24')

    def save_as(self):
        global filename

        # Getting the filename
        new_filename = QFileDialog.getSaveFileName(self, 'Choose file', '')[0]

        if new_filename:
            # If the user didn't click "Cancel":
            filename = new_filename
            sf.write(filename, self.waveform, self.sample_rate, 'PCM_24')

    def play(self) -> None:
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def stop(self) -> None:
        self.player.stop()
        self.rewind_slider.setValue(0)

    def rewind(self, rewind_slider_position: int) -> None:
        self.player.setPosition(int(self.player.duration() * (rewind_slider_position / 100)))

    def change_volume(self, volume_slider_position: int) -> None:
        self.player.setVolume(volume_slider_position)

    def change_pace(self, pace_slider_position: int) -> None:
        # Updating the stream rate
        if self.player.playbackRate() != 0:
            self.sample_rate /= self.player.playbackRate()
        self.sample_rate *= (pace_slider_position / 50)
        self.sample_rate = int(self.sample_rate)

        # Updating the player
        self.player.setPlaybackRate(pace_slider_position / 50)

    def crop(self):
        # Creating a dialog to ask the user about the positions of the start and the end of the song
        dialog = CropAudioDialog()
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
                start_waveform_pos = int(len(self.waveform) * (start_slider_pos / 100))
                end_waveform_pos = int(len(self.waveform) * (end_slider_pos / 100))
                self.waveform = np.array(list(self.waveform)
                                         [start_waveform_pos:end_waveform_pos + 1:])

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
    windows.setWindowIcon(QIcon('designs/icons/window_icon.jpg'))

    windows.show()
    app.installEventFilter(image_editing_window)
    sys.exit(app.exec_())
