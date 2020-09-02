from __future__ import absolute_import

import sys
import os

from functools import partial

from pathlib import Path

# GUI
from PyQt5.QtWidgets import (QWidget, QTabWidget, QLabel, QLineEdit, QPushButton,QComboBox, QSizePolicy, QSpacerItem,
                             QGridLayout, QVBoxLayout, QFileDialog, QProgressBar, QApplication, QScrollArea, QDesktopWidget)

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont, QIcon
# Image utils
from .biomedical_image_utils import generate_dataset, generate_training_data, nd2_converter, tiff_converter, roi_to_mask

# Predict
from .predict import predict_image, predict_folder
    

class ImageLabel(QLabel):
    
    def __init__(self, results, window):
        super().__init__()
        self.setAcceptDrops(True)

        self.results = results
        self.window = window
    

    def dragEnterEvent(self, event):
        accept = True
        for elem in event.mimeData().urls():
            file_path = elem.toLocalFile()
            tab1_imageExtension = file_path.lower().split(".")[-1].lower()

            if not (tab1_imageExtension == "nd2" or tab1_imageExtension == "tiff" or tab1_imageExtension == "tif" or tab1_imageExtension == "png" or tab1_imageExtension == "jpg"):
                accept = False
        if accept:
            event.accept()
        else:
            event.ignore()


    def dragMoveEvent(self, event):
        accept = True
        for elem in event.mimeData().urls():
            file_path = elem.toLocalFile()
            tab1_imageExtension = file_path.lower().split(".")[-1].lower()

            if not (tab1_imageExtension == "nd2" or tab1_imageExtension == "tiff" or tab1_imageExtension == "tif" or tab1_imageExtension == "png" or tab1_imageExtension == "jpg"):
                accept = False
        if accept:
            event.accept()
        else:
            event.ignore()


    def dropEvent(self, event):
        accept = True
        for elem in event.mimeData().urls():

            file_path = elem.toLocalFile()
            tab1_imageExtension = file_path.lower().split(".")[-1].lower()

            if tab1_imageExtension == "nd2" or tab1_imageExtension == "tiff" or tab1_imageExtension == "tif" or tab1_imageExtension == "png" or tab1_imageExtension == "jpg":

                if tab1_imageExtension == "nd2":
                    nd2_converter(file_path, os.path.dirname(file_path),"png")
                #    predict_image(file_path.replace("."+tab1_imageExtension,".png"),os.path.dirname(file_path))

                elif tab1_imageExtension == "tiff" or tab1_imageExtension == "tif":
                    tiff_converter(file_path,os.path.dirname(file_path),"png")
                #     predict_image(file_path.replace("."+tab1_imageExtension,".png"),os.path.dirname(file_path))
                    
                # else:
                #     predict_image(file_path,os.path.dirname(file_path))

                predict_image(file_path,os.path.dirname(file_path)+os.sep)

                # Create row for result
                grid = QWidget()

                grid_layout = QGridLayout()
                grid_layout.setSpacing(10)

                font=QFont()
                font.setBold(True)
                folder_name = QLabel()
                folder_name.setText(f"Folder path: {os.path.dirname(file_path)}")
                folder_name.setFont(font)
                folder_name.setAlignment(Qt.AlignCenter)

                input_name = QLabel()
                output_name = QLabel()
                input_name.setText(f"Input image: {os.path.basename(file_path)}")
                output_name.setText(f"Predicted Tumour (Blue): {os.path.basename(file_path.replace('.'+tab1_imageExtension,'_blend.png'))}")
                input_name.setFont(font)
                output_name.setFont(font)

                input_name.setAlignment(Qt.AlignCenter)
                output_name.setAlignment(Qt.AlignCenter)

                image_width = 600
                image_height = 600
                input_image = QLabel()
                output_image = QLabel()
                input_image.setPixmap(QPixmap(file_path.replace("."+tab1_imageExtension,".png")))
                output_image.setPixmap(QPixmap(file_path.replace("."+tab1_imageExtension,"_blend.png")))

                input_image.setScaledContents(True)
                output_image.setScaledContents(True)

                input_image.setMaximumWidth(image_width)
                input_image.setMaximumHeight(image_height)
                output_image.setMaximumWidth(image_width)
                output_image.setMaximumHeight(image_height)


                button_prediction = QPushButton("Delete")
                
                button_prediction.setIcon(QIcon.fromTheme("edit-delete")) 
                button_prediction.setStyleSheet('''

                        QPushButton{

                            width: auto;

                        }

                ''')
                def delete_prediction():
                    self.results.removeWidget(grid)
                    grid.hide()
                    self.results.update()

                button_prediction.clicked.connect(delete_prediction)

                grid_layout.addWidget(folder_name, 0, 0, 1, 3)
                grid_layout.addWidget(button_prediction, 0, 3, 1, 1)
                grid_layout.addWidget(input_image, 1, 0, 1, 2)
                grid_layout.addWidget(output_image, 1, 2, 1, 2)
                grid_layout.addWidget(input_name, 2, 0, 1, 2)
                grid_layout.addWidget(output_name, 2, 2, 1, 2)

                grid_layout.setColumnStretch(0, 2)
                grid_layout.setColumnStretch(1, 2)
                grid_layout.setColumnStretch(2, 2)
                grid_layout.setColumnStretch(3, 1)

                grid.setLayout(grid_layout)
                self.results.addWidget(grid)
                self.results.insertStretch(-1)

                self.window.resize(self.window.width(),
                                   self.window.height() + grid.sizeHint().height())
            else:
                accept = False

        if accept:
            event.accept()
        else:
            event.ignore()


def show_gui():
    app = QApplication([])

    window = QWidget()
    window.setWindowTitle("Deep-Tumour-Spheroid")
    tabs = QTabWidget()

    outputType="png"

    # ------------------------------------TAB 1---------------------------------------
    tab1 = QWidget()
    tabs.addTab(tab1, "Predict Tumour")

    verticalLayout_tab1 = QVBoxLayout()
    #verticalLayout_tab1.setSpacing(10)


    results_tab1 = QWidget()
    results_tab1_layout = QVBoxLayout()
    results_tab1.setLayout(results_tab1_layout)

    labelTab1_dropImage = ImageLabel(results_tab1_layout, window)
    labelTab1_dropImage.setText('\n\n Drop Image Here \n\n')
    labelTab1_dropImage.setStyleSheet('''

            QLabel{

                border: 4px dashed #aaa

            }

    ''')
    labelTab1_dropImage.setAlignment(Qt.AlignCenter)
    #labelTab1_dropImage.setMaximumHeight(100)

    # Adding Widgets
    verticalLayout_tab1.addWidget(labelTab1_dropImage)
    #verticalLayout_tab1.insertStretch(-1)

    scroll = QScrollArea()
    scroll.setWidget(results_tab1)
    scroll.setWidgetResizable(True)
    # scroll.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
    scroll.setVerticalScrollBarPolicy( Qt.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy( Qt.ScrollBarAsNeeded)
    #scroll.setMaximumHeight(800)
    scroll.setMaximumWidth(1350)
    scroll.setMinimumHeight(0)
    verticalLayout_tab1.addWidget(scroll)
    #verticalLayout_tab1.addStretch()
    #verticalLayout_tab1.addWidget(inputTab1_image, 2, 0)
    #verticalLayout_tab1.addWidget(outputputTab1_image, 2, 1)
    verticalLayout_tab1.setStretch(0, 0)
    verticalLayout_tab1.setStretch(1, 1)
    tab1.setMaximumWidth(1350)
    tab1.setLayout(verticalLayout_tab1)

    # ------------------------------------TAB 2---------------------------------------
    tab2 = QWidget()
    tabs.addTab(tab2, "Generate Dataset")

    grid_tab2 = QGridLayout()
    grid_tab2.setSpacing(10)

    labelTab2_inputFolder = QLabel("Input folder")
    labelTab2_outputFolder = QLabel("Output folder")
    grid_tab2.addWidget(labelTab2_inputFolder, 1, 0)
    grid_tab2.addWidget(labelTab2_outputFolder, 2, 0)

    lineEditTab2_inputFolder = QLineEdit(str(Path.home()))
    lineEditTab2_outputFolder = QLineEdit(str(Path.home()))
    grid_tab2.addWidget(lineEditTab2_inputFolder, 1, 1)
    grid_tab2.addWidget(lineEditTab2_outputFolder, 2, 1)

    buttonTab2_inputFolder = QPushButton("Select")

    def openInputFolderTab2():
        fname = QFileDialog.getExistingDirectory(
            tab2, 'Select Directory', lineEditTab2_inputFolder.text())
        lineEditTab2_inputFolder.setText(fname)

    buttonTab2_inputFolder.clicked.connect(openInputFolderTab2)

    buttonTab2_outputFolder = QPushButton("Select")

    def openOutputFolderTab2():
        fname = QFileDialog.getExistingDirectory(
            tab2, 'Select Directory', lineEditTab2_outputFolder.text())
        lineEditTab2_outputFolder.setText(fname)

    buttonTab2_outputFolder.clicked.connect(openOutputFolderTab2)

    grid_tab2.addWidget(buttonTab2_inputFolder, 1, 2)
    grid_tab2.addWidget(buttonTab2_outputFolder, 2, 2)

    label_progress = QLabel("Progress:")
    progress = QProgressBar(tab2)
    progress.setGeometry(0, 0, 300, 25)
    progress.setMaximum(100)
    grid_tab2.addWidget(label_progress, 3, 0)
    grid_tab2.addWidget(progress, 3, 1, 1, 2)

    buttonTab2_process = QPushButton("Generate")

    def processTab2():
        if lineEditTab2_inputFolder.text() != "" and lineEditTab2_outputFolder.text() != "":
            if comboBoxTab2_dataTransformation.currentText() == "Yes":
                generate_dataset(lineEditTab2_inputFolder.text(),
                            lineEditTab2_outputFolder.text(), outputType, progress)
            else:
                progress.setValue(0)
                generate_training_data(lineEditTab2_inputFolder.text(),
                            lineEditTab2_outputFolder.text(), outputType)
                progress.setValue(100)

    buttonTab2_process.clicked.connect(processTab2)

    buttonTab2_cancel = QPushButton("Cancel")
    buttonTab2_cancel.clicked.connect(lambda: app.quit())

    grid_tab2.addWidget(buttonTab2_cancel, 5, 0)
    grid_tab2.addWidget(buttonTab2_process, 5, 1, 1, 2)

    labelTab2_dataTransformation = QLabel("Data conversion")
    comboBoxTab2_dataTransformation = QComboBox()
    comboBoxTab2_dataTransformation.addItems(["Yes","No"])

    grid_tab2.addWidget(labelTab2_dataTransformation, 4, 0)
    grid_tab2.addWidget(comboBoxTab2_dataTransformation, 4, 1, 1, 2)

    grid_tab2.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding), 6, 0, 1, 3)

    tab2.setLayout(grid_tab2)
    tab2.setWindowTitle("Generate Dataset")

    
    # ------------------------------------TAB 3---------------------------------------
    tab3 = QWidget()
    tabs.addTab(tab3, "Transform image")

    grid_tab3 = QGridLayout()
    grid_tab3.setSpacing(10)

    labelTab3_inputFile = QLabel("Input File")
    labelTab3_outputFolder = QLabel("Output folder")
    grid_tab3.addWidget(labelTab3_inputFile, 1, 0)
    grid_tab3.addWidget(labelTab3_outputFolder, 2, 0)

    lineEditTab3_inputFile = QLineEdit(str(Path.home()))
    lineEditTab3_outputFolder = QLineEdit(str(Path.home()))
    grid_tab3.addWidget(lineEditTab3_inputFile, 1, 1)
    grid_tab3.addWidget(lineEditTab3_outputFolder, 2, 1)

    buttonTab3_inputFile = QPushButton("Select")

    def openInputFileTab3():
        fname, _ = QFileDialog.getOpenFileName(
            tab3, 'Select File', lineEditTab3_inputFile.text())
        lineEditTab3_inputFile.setText(fname)

    buttonTab3_inputFile.clicked.connect(openInputFileTab3)

    buttonTab3_outputFolder = QPushButton("Select")

    def openOutputFolderTab3():
        fname = QFileDialog.getExistingDirectory(
            tab3, 'Select Directory', lineEditTab3_outputFolder.text())
        lineEditTab3_outputFolder.setText(fname)

    buttonTab3_outputFolder.clicked.connect(openOutputFolderTab3)

    grid_tab3.addWidget(buttonTab3_inputFile, 1, 2)
    grid_tab3.addWidget(buttonTab3_outputFolder, 2, 2)

    buttonTab3_process = QPushButton("Generate")

    def processTab3():
        if lineEditTab3_inputFile.text() != "" and lineEditTab3_outputFolder.text() != "":
            if lineEditTab3_inputFile.text().endswith(".nd2"):
                nd2_converter(lineEditTab3_inputFile.text(), lineEditTab3_outputFolder.text(), outputType)
            elif lineEditTab3_inputFile.text().endswith(".tiff") or lineEditTab3_inputFile.text().endswith(".tif"):
                tiff_converter(lineEditTab3_inputFile.text(), lineEditTab3_outputFolder.text(), outputType)

    buttonTab3_process.clicked.connect(processTab3)

    buttonTab3_cancel = QPushButton("Cancel")
    buttonTab3_cancel.clicked.connect(lambda: app.quit())

    grid_tab3.addWidget(buttonTab3_cancel, 3, 0)
    grid_tab3.addWidget(buttonTab3_process, 3, 1, 1, 2)

    grid_tab3.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding), 4, 0, 1, 3)

    tab3.setLayout(grid_tab3)

    # ------------------------------------TAB 4---------------------------------------
    tab4 = QWidget()
    tabs.addTab(tab4, "Convert ROI to Mask")

    grid_tab4 = QGridLayout()
    grid_tab4.setSpacing(10)

    labelTab4_inputFile = QLabel("Input File")
    labelTab4_outputFolder = QLabel("Output folder")
    grid_tab4.addWidget(labelTab4_inputFile, 0, 0)
    grid_tab4.addWidget(labelTab4_outputFolder, 1, 0)

    lineEditTab4_inputFile = QLineEdit(str(Path.home()))
    lineEditTab4_outputFolder = QLineEdit(str(Path.home()))
    grid_tab4.addWidget(lineEditTab4_inputFile, 0, 1)
    grid_tab4.addWidget(lineEditTab4_outputFolder, 1, 1)

    buttonTab4_inputFile = QPushButton("Select")

    def openInputFileTab4():
        fname, _ = QFileDialog.getOpenFileName(
            tab4, 'Select File', lineEditTab4_inputFile.text())
        lineEditTab4_inputFile.setText(fname)

    buttonTab4_inputFile.clicked.connect(openInputFileTab4)

    buttonTab4_outputFolder = QPushButton("Select")

    def openOutputFolderTab4():
        fname = QFileDialog.getExistingDirectory(
            tab4, 'Select Directory', lineEditTab4_outputFolder.text())
        lineEditTab4_outputFolder.setText(fname)

    buttonTab4_outputFolder.clicked.connect(openOutputFolderTab4)

    grid_tab4.addWidget(buttonTab4_inputFile, 0, 2)
    grid_tab4.addWidget(buttonTab4_outputFolder, 1, 2)

    buttonTab4_process = QPushButton("Generate")

    def processTab4():
        if lineEditTab4_inputFile.text() != "" and lineEditTab4_outputFolder.text() != "":
            if lineEditTab4_inputFile.text().endswith(".roi") or lineEditTab4_inputFile.text().endswith(".zip"):
                roi_to_mask(lineEditTab4_inputFile.text(),
                             lineEditTab4_outputFolder.text(),outputType)

    buttonTab4_process.clicked.connect(processTab4)

    buttonTab4_cancel = QPushButton("Cancel")
    buttonTab4_cancel.clicked.connect(lambda: app.quit())

    grid_tab4.addWidget(buttonTab4_cancel, 2, 0)
    grid_tab4.addWidget(buttonTab4_process, 2, 1, 1, 2)
    grid_tab4.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding), 3, 0, 1, 3)

    tab4.setLayout(grid_tab4)

    window_layout = QVBoxLayout()
    window_layout.addWidget(tabs)
    window.setLayout(window_layout)
    window.setMaximumWidth(1350)
    window.resize(1350, 200)

    def centerOnScreen (self):
        '''centerOnScreen()
Centers the window on the screen.'''
        resolution = QDesktopWidget().screenGeometry()
        self.move((resolution.width() / 2) - (self.frameSize().width() / 2),
                  (resolution.height() / 2) - (self.frameSize().height() / 2))


    window.centerOnScreen = partial(centerOnScreen, window)
    window.centerOnScreen()

    window.show()

    app.exec_()