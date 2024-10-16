# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GUI.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1600, 1200)
        MainWindow.setMinimumSize(QtCore.QSize(800, 600))
        font = QtGui.QFont()
        font.setPointSize(7)
        MainWindow.setFont(font)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setTitle("")
        self.groupBox.setAlignment(QtCore.Qt.AlignCenter)
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.groupBox)
        self.horizontalLayout.setObjectName("horizontalLayout")

        # spacerItem0 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        # self.horizontalLayout.addItem(spacerItem0)
        # lowSlider = QtWidgets.QSlider(self)
        # self.horizontalLayout.addItem(lowSlider)

        self.lowLabel = QtWidgets.QLabel(self.groupBox)
        self.lowLabel.setObjectName("lowLabel")
        # self.lowLabel.setText("10001400")
        self.lowLabel.setText("9980000")

        self.lowSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.lowSlider.setGeometry(30, 40, 1000, 30)
        self.lowSlider.valueChanged[int].connect(self.changeLowValue)
        self.lowSlider.setMinimum(9950000)
        self.lowSlider.setMaximum(10005000)
        # self.lowSlider.setValue(10001400)
        self.lowSlider.setValue(9980000)
        self.horizontalLayout.addWidget(self.lowSlider)
        self.horizontalLayout.addWidget(self.lowLabel)

        self.highLabel = QtWidgets.QLabel(self.groupBox)
        self.highLabel.setObjectName("highLabel")
        # self.highLabel.setText("10002850")
        self.highLabel.setText("10020000")

        self.highSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.highSlider.setGeometry(30, 40, 1000, 30)
        self.highSlider.valueChanged[int].connect(self.changeHighValue)
        self.highSlider.setMinimum(9995000)
        self.highSlider.setMaximum(10050000)
        # self.highSlider.setValue(10002850)
        self.highSlider.setValue(10020000)
        self.horizontalLayout.addWidget(self.highSlider)
        self.horizontalLayout.addWidget(self.highLabel)

        self.stepLabel = QtWidgets.QLabel(self.groupBox)
        self.stepLabel.setObjectName("stepLabel")
        self.stepLabel.setText("100")

        self.stepSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.stepSlider.setGeometry(30, 40, 1000, 30)
        self.stepSlider.valueChanged[int].connect(self.changeStepValue)
        self.stepSlider.setMinimum(2)
        self.stepSlider.setMaximum(100)
        self.stepSlider.setValue(100)
        self.stepSlider.setPageStep(2)
        self.horizontalLayout.addWidget(self.stepSlider)
        self.horizontalLayout.addWidget(self.stepLabel)

        self.ScanButton = QtWidgets.QPushButton(self.groupBox)
        self.ScanButton.setObjectName("ScanButton")
        self.horizontalLayout.addWidget(self.ScanButton)
        self.PortSelect = QtWidgets.QComboBox(self.groupBox)
        self.PortSelect.setEnabled(True)
        self.PortSelect.setObjectName("PortSelect")
        self.horizontalLayout.addWidget(self.PortSelect)

        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)

        self.OpenButton = QtWidgets.QPushButton(self.groupBox)
        self.OpenButton.setObjectName("OpenButton")
        self.horizontalLayout.addWidget(self.OpenButton)

        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)

        self.ZoomButton = QtWidgets.QPushButton(self.groupBox)
        self.ZoomButton.setObjectName("ZoomButton")
        self.horizontalLayout.addWidget(self.ZoomButton)

        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem4)

        self.potLabel = QtWidgets.QLabel(self.groupBox)
        self.potLabel.setObjectName("potLabel")
        self.potLabel.setText("240")

        self.potSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.potSlider.setGeometry(30, 40, 1000, 30)
        self.potSlider.valueChanged[int].connect(self.changePotValue)
        self.potSlider.setMinimum(0)
        self.potSlider.setMaximum(255)
        self.potSlider.setValue(240)
        self.horizontalLayout.addWidget(self.potSlider)
        self.horizontalLayout.addWidget(self.potLabel)

        self.DefaultViewButton = QtWidgets.QPushButton(self.groupBox)
        self.DefaultViewButton.setObjectName("DefaultViewButton")
        self.horizontalLayout.addWidget(self.DefaultViewButton)

        spacerItem6 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem6)

        self.AutoButton = QtWidgets.QPushButton(self.groupBox)
        self.AutoButton.setObjectName("AutoButton")
        self.horizontalLayout.addWidget(self.AutoButton)

        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)

        self.DebugButton = QtWidgets.QPushButton(self.groupBox)
        self.DebugButton.setObjectName("DebugButton")
        self.horizontalLayout.addWidget(self.DebugButton)

        spacerItem5 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem5)

        self.checkbox_10 = QtWidgets.QCheckBox("10", self.groupBox)
        self.checkbox_10.setChecked(True)
        self.horizontalLayout.addWidget(self.checkbox_10)

        self.checkbox_30 = QtWidgets.QCheckBox("30", self.groupBox)
        self.horizontalLayout.addWidget(self.checkbox_30)

        self.checkbox_50 = QtWidgets.QCheckBox("50", self.groupBox)
        self.horizontalLayout.addWidget(self.checkbox_50)

        self.checkbox_Norm = QtWidgets.QCheckBox("Norm", self.groupBox)
        self.checkbox_Norm.setChecked(True)
        self.horizontalLayout.addWidget(self.checkbox_Norm)

        spacerItem7 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem7)

        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)

        self.lineEdit = QtWidgets.QLineEdit(self.groupBox)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout.addWidget(self.lineEdit)
        self.ExportButton = QtWidgets.QPushButton(self.groupBox)
        self.ExportButton.setObjectName("ExportButton")
        self.horizontalLayout.addWidget(self.ExportButton)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem3)
        self.verticalLayout.addWidget(self.groupBox)

        self.GraphA = PlotWidget(self.centralwidget)
        self.GraphA.setObjectName("GraphA")
        self.verticalLayout.addWidget(self.GraphA)
        # self.GraphB = PlotWidget(self.centralwidget)
        # self.GraphB.setObjectName("GraphB")
        # self.verticalLayout.addWidget(self.GraphB)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def changeLowValue(self, value):
        self.lowLabel.setText(str(value))
        # print(value)

    def changeHighValue(self, value):
        self.highLabel.setText(str(value))
        # print(value)

    def changeStepValue(self, value):
        self.stepLabel.setText(str(value))
        # print(value)

    def changePotValue(self, value):
        self.potLabel.setText(str(value))
        # print(value)
        # self.Instrument.port = self.PortName
        # self.Instrument.open()
        # self.Instrument.timeout = 0
        # cmd = 'R' + str(self.potLabel.text()) + '\n'
        # print(cmd)
        # self.Instrument.write(cmd.encode())
        # app_encoding = "utf-8"
        # buffer = ''
        # while 1:
        #     buffer += self.Instrument.read(self.Instrument.inWaiting()).decode(app_encoding)
        #     if 's' in buffer:
        #         break
        # print(buffer)
        # self.Instrument.close()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.ScanButton.setText(_translate("MainWindow", "Scan"))
        self.OpenButton.setText(_translate("MainWindow", "Show spectrum"))
        self.ZoomButton.setText(_translate("MainWindow", "Zoom"))
        self.DefaultViewButton.setText(_translate("MainWindow", "Set Pot"))
        self.AutoButton.setText(_translate("MainWindow", "Auto"))
        self.DebugButton.setText(_translate("MainWindow", "Debug"))
        self.label.setText(_translate("MainWindow", "File name"))
        self.ExportButton.setText(_translate("MainWindow", "Save as fig."))
from pyqtgraph import PlotWidget
