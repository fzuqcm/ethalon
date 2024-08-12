import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import pyqtgraph.exporters
import numpy as np
import GUI
import pickle
import numpy as np

import serial
import serial.tools.list_ports

# from scipy.stats import norm
from astropy import modeling

from datetime import datetime, timedelta
from time import mktime, localtime, strftime, time

class DateAxisItem(pg.AxisItem):
    
    # Max width in pixels reserved for each label in axis
    _pxLabelWidth = 80

    def __init__(self, *args, **kwargs):
        pg.AxisItem.__init__(self, *args, **kwargs)
        self._oldAxis = None

    def tickStrings(self, values, scale, spacing):
        """Reimplemented from PlotItem to adjust to the range"""
        ret = []

        for x in values:
            ret.append(str(timedelta(seconds=x)))
                
        return ret

    def attachToPlotItem(self, plotItem):
        """Add this axis to the given PlotItem
        :param plotItem: (PlotItem)
        """
        self.setParentItem(plotItem)
        viewBox = plotItem.getViewBox()
        self.linkToView(viewBox)
        self._oldAxis = plotItem.axes[self.orientation]['item']
        self._oldAxis.hide()
        plotItem.axes[self.orientation]['item'] = self
        pos = plotItem.axes[self.orientation]['pos']
        plotItem.layout.addItem(self, *pos)
        self.setZValue(-1000)

class MyApp(QtWidgets.QMainWindow, GUI.Ui_MainWindow):
    Instrument = serial.Serial()
    Instrument.baudrate = 115200
    Instrument.stopbits = serial.STOPBITS_ONE
    Instrument.bytesize = serial.EIGHTBITS
    PortName = ''
    hs30 = 20000000
    hs50 = 40000000
    Buff = ''
    Buff30 = ''
    Buff50 = ''
    Fr = []
    Am = []
    Ph = []
    Fr30 = []
    Am30 = []
    Ph30 = []
    Fr50 = []
    Am50 = []
    Ph50 = []
    ff = []
    aa = []
    polyf = []
    polya = []
    n = 0
    s = 0
    a = 0
    b = 0
    c = 0
    auto = 0
    zoom = 0
    inplot = 0
    topam = 0
    minam = 0
    topph = 0
    topam30 = 0
    topph30 = 0
    topam50 = 0
    topph50 = 0
    phdiff = 0
    am30diff = 0
    ph30diff = 0
    am50diff = 0
    ph50diff = 0

    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)

        self.OpenButton.clicked.connect(self.OpenButtonClicked)
        self.ZoomButton.clicked.connect(self.ZoomButtonClicked)
        self.DefaultViewButton.clicked.connect(self.DefaultViewButtonClicked)
        self.AutoButton.clicked.connect(self.AutoButtonClicked)
        self.DebugButton.clicked.connect(self.DebugButtonClicked)
        self.ExportButton.clicked.connect(self.ExportButtonClicked)

        self.PortSelect.activated[str].connect(self.onActivated)

        # self.GraphA.setClipToView(True)
        # self.GraphA.setDownsampling(mode='peak')
        # self.FreqAxisA = DateAxisItem(orientation='bottom')
        # self.FreqAxisA.attachToPlotItem(self.GraphA.getPlotItem())
        self.GraphA.setLabel('bottom', 'Frequency', 'Hz', color='#000000', **{'font-size': '7pt'})
        self.GraphA.getAxis('bottom').setPen(pg.mkPen(color='#000000', width=1))
        self.GraphA.setLabel('left', 'Amplitude', '', color='#000000', **{'font-size': '7pt'})
        self.GraphA.getAxis('left').setPen(pg.mkPen(color='#000000', width=1))
        # self.GraphA.setLimits(xMin=0)
        self.GraphA.setBackground('#FFFFFF')
        self.GraphA.showGrid(x=True,y=True)

        # self.frq_value = pg.TextItem("10000000", color='#000080', html=None, anchor=(0, 0), border=None, fill=None, angle=0, rotateAxis=None)
        self.frq_value = self.GraphA.addLegend(size=(110,0),offset=(30,15))
        # self.frq_style = {'color': '#008', 'size': '24pt', 'bold': True, 'italic': False}
        self.frq_style = pg.LegendItem(labelTextSize='24pt',pen=pg.mkPen(color='#0000FF', width=3))
        self.frq_value.addItem(self.frq_style, 'Frekvence')
        # self.frq_value.setFont(QtGui.QFont('Arial', 48))
        # self.GraphA.addItem(self.frq_value)
        # self.frq_value.setPos(QtCore.QPointF(10000000,5000))
        # self.frq_value.setPos(10000000,5000)

        # self.GraphB.setClipToView(True)
        # self.GraphB.setDownsampling(mode='peak')
        # self.TimeAxisB = DateAxisItem(orientation='bottom')
        # self.TimeAxisB.attachToPlotItem(self.GraphB.getPlotItem())

        # self.GraphB.setLabel('bottom', 'Frequency', 'Hz', color='#000000', **{'font-size': '7pt'})
        # self.GraphB.getAxis('bottom').setPen(pg.mkPen(color='#000000', width=1))
        # self.GraphB.setLabel('left', 'Phase', '', color='#000000', **{'font-size': '7pt'})
        # self.GraphB.getAxis('left').setPen(pg.mkPen(color='#000000', width=1))
        # self.GraphB.setLimits(xMin=0)
        # self.GraphB.setBackground('#FFFFFF')
        # self.GraphB.showGrid(x=True,y=True)

        # self.autoTimer = pg.QtCore.QTimer(singleShot = False, timeout = 100)
        self.autoTimer = pg.QtCore.QTimer()
        self.autoTimer.timeout.connect(self.showPlot)
        self.autoTimer.start(100)
        
    def closeEvent(self, event):
        event.accept()

    def ExportButtonClicked(self):
        QtGui.QApplication.processEvents()
        exporter = pg.exporters.ImageExporter(self.GraphA.plotItem)
        exporter.export(str(self.lineEdit.text())+'A.png')
        # exporter = pg.exporters.ImageExporter(self.GraphB.plotItem)
        # exporter.export(str(self.lineEdit.text())+'B.png')
        self.lineEdit.clear()

    def DefaultViewButtonClicked(self):
        # self.GraphA.enableAutoRange('xy')
        # self.GraphB.enableAutoRange('xy')
        self.Instrument.port = self.PortName
        self.Instrument.open()
        self.Instrument.timeout = 0
        cmd = 'R' + str(self.potLabel.text()) + '\n'
        print(cmd)
        self.Instrument.write(cmd.encode())
        # app_encoding = "utf-8"
        # buffer = ''
        # while 1:
        #     buffer += self.Instrument.read(self.Instrument.inWaiting()).decode(app_encoding)
        #     if 's' in buffer:
        #         break
        # print(buffer)
        self.Instrument.close()

    def ScanButtonClicked(self):
        self.ports = list(serial.tools.list_ports.comports())
        self.coms = []
        pidx = 0
        qcmidx = 0
        for ports in self.ports:
            self.coms.append(str(ports).split()[0])
            pname = self.coms[pidx]
            # print('pname:',pidx,pname)
            if pname[0:10] == '/dev/ttyAC':
                qcmidx = pidx
                # print(qcmidx)
            pidx += 1
        self.PortSelect.clear()
        self.PortSelect.addItems(self.coms)
        self.PortSelect.setCurrentIndex(qcmidx)
        self.PortName = self.coms[qcmidx]

    def onActivated(self, text):
        self.PortName = text

    def readData(self, low, high, step):
        self.Instrument.port = self.PortName
        self.Instrument.open()
        self.Instrument.timeout = 0
        app_encoding = "utf-8"
        if self.checkbox_10.isChecked():
            cmd = str(low) + ';' + str(high) + ';' + str(step) + '\n'
            print(cmd)
            self.Instrument.write(cmd.encode())
            buffer = ''
            while 1:
                buffer += self.Instrument.read(self.Instrument.inWaiting()).decode(app_encoding)
                if 's' in buffer:
                    break
            self.Buff = buffer.splitlines()
        if self.checkbox_30.isChecked():
            cmd = str(low + self.hs30) + ';' + str(low + self.hs30 + 3*(high-low)) + ';' + str(3*step) + '\n'
            print(cmd)
            self.Instrument.write(cmd.encode())
            buffer = ''
            while 1:
                buffer += self.Instrument.read(self.Instrument.inWaiting()).decode(app_encoding)
                if 's' in buffer:
                    break
            self.Buff30 = buffer.splitlines()
        if self.checkbox_50.isChecked():
            cmd = str(low + self.hs50) + ';' + str(low + self.hs50 + 5*(high - low)) + ';' + str(5*step) + '\n'
            print(cmd)
            self.Instrument.write(cmd.encode())
            buffer = ''
            while 1:
                buffer += self.Instrument.read(self.Instrument.inWaiting()).decode(app_encoding)
                if 's' in buffer:
                    break
            self.Buff50 = buffer.splitlines()        
        self.Instrument.close()
        if self.checkbox_10.isChecked():
            buff = self.Buff
            # print(len(buff))
            # print(buff[1])
            # print(buff)
            self.Fr = np.empty(len(buff)-2)
            self.Am = np.empty(len(buff)-2)
            self.Ph = np.empty(len(buff)-2)
            idx = 0
            for freq in range(low, high + 1, step):
                if idx > 0:
                    am, ph = buff[idx-1].split(';')
                    self.Fr[idx-1] = float(freq)
                    self.Am[idx-1] = float(am)
                    self.Ph[idx-1] = float(ph)
                    # print(self.Fr[idx-1],self.Am[idx-1])
                # print(idx, freq, str(ampl[idx]), str(phase[idx]))
                # text = pg.TextItem(html='<div style="text-align: center"><span style="color: #000000;"> %s</span></div>',anchor=(0.5, -1))
                # text.setText('%s'%str(ampl[idx]))
                idx += 1
        if self.checkbox_30.isChecked():
            buff = self.Buff30
            self.Fr30 = np.empty(len(buff)-2)
            self.Am30 = np.empty(len(buff)-2)
            self.Ph30 = np.empty(len(buff)-2)
            idx = 0
            for freq in range(low, high + 1, step):
                if idx > 0:
                    am, ph = buff[idx-1].split(';')
                    self.Fr30[idx-1] = float(freq)
                    self.Am30[idx-1] = float(am)
                    self.Ph30[idx-1] = float(ph)
                idx += 1
        if self.checkbox_50.isChecked():
            buff = self.Buff50
            self.Fr50 = np.empty(len(buff)-2)
            self.Am50 = np.empty(len(buff)-2)
            self.Ph50 = np.empty(len(buff)-2)
            idx = 0
            for freq in range(low, high + 1, step):
                if idx > 0:
                    am, ph = buff[idx-1].split(';')
                    self.Fr50[idx-1] = float(freq)
                    self.Am50[idx-1] = float(am)
                    self.Ph50[idx-1] = float(ph)
                idx += 1

    def plotData(self):
        self.GraphA.clear()
        if self.checkbox_10.isChecked():
            self.topam = np.max(self.Am)
            self.minam = np.min(self.Am)
            self.topph = np.max(self.Ph)
            self.phdiff = self.topam - self.topph
            self.GraphA.plot(self.Fr,self.Am, pen=pg.mkPen(color='#0000FF', width=3))
            # self.GraphB.clear()
            # self.GraphB.plot(self.Fr,self.Ph, pen=pg.mkPen(color='#007F00', width=3))
            self.GraphA.plot(self.Fr,self.Ph + self.phdiff, pen=pg.mkPen(color='#007F00', width=3))
        if self.checkbox_30.isChecked():
            self.topam30 = np.max(self.Am30)
            self.topph30 = np.max(self.Ph30)
            self.am30diff = self.topam - self.topam30
            self.ph30diff = self.topam - self.topph30
            self.GraphA.plot(self.Fr30,self.Am30 + self.am30diff, pen=pg.mkPen(color='#00BFFF', width=2))
            self.GraphA.plot(self.Fr30,self.Ph30 + self.ph30diff, pen=pg.mkPen(color='#00BF00', width=2))
        if self.checkbox_50.isChecked():
            self.topam50 = np.max(self.Am50)
            self.topph50 = np.max(self.Ph50)
            self.am50diff = self.topam - self.topam50
            self.ph50diff = self.topam - self.topph50
            self.GraphA.plot(self.Fr50,self.Am50 + self.am50diff, pen=pg.mkPen(color='#00DFFF', width=1))
            self.GraphA.plot(self.Fr50,self.Ph50 + self.ph50diff, pen=pg.mkPen(color='#00DF00', width=1))

    def readMax(self):
        self.Instrument.port = self.PortName
        self.Instrument.open()
        self.Instrument.timeout = 0
        cmd = 'D64\n'
        print(cmd)
        self.Instrument.write(cmd.encode())
        app_encoding = "utf-8"
        buffer = ''
        while 1:
            buffer += self.Instrument.read(self.Instrument.inWaiting()).decode(app_encoding)
            if 's' in buffer:
                break
        self.Instrument.close()
        Buff = buffer.splitlines()
        frl = int(Buff[0])                          # calib_freq - DIRTY_RANGE
        frr = int(Buff[1])                          # calib_freq + DIRTY_RANGE
        fr = int(Buff[2])                           # f - raw maximum in frequency
        self.n = int(Buff[3])                       # SWEEP_COUNT
        self.s = int(Buff[4])                       # SWEEP_STEP
        dis = float(Buff[5])                        # Dissipation dis = maxf / (drf - dlf);
        self.ff = np.empty(self.n)
        self.aa = np.empty(self.n)
        # print('DEBUG:\n',buffer)
        for idx in range(0,self.n):
            # print(n,idx)
            self.ff[idx] = float(Buff[6+(2*idx)])   # frequency
            self.aa[idx] = float(Buff[7+(2*idx)])   # magnitude
            # print(idx,self.ff[idx],self.aa[idx])
        self.a = float(Buff[6 + 2 * self.n])        # coeffs(0)
        self.b = float(Buff[7 + 2 * self.n])        # coeffs(1)
        self.c = float(Buff[8 + 2 * self.n])        # coeffs(2)
        frq = float(Buff[9 + 2 * self.n])           # fitted resonance frequency
        self.wait_us = float(Buff[10 + 2 * self.n]) # Wait before analog read [µsec]
        self.av_sample = float(Buff[11 + 2 * self.n]) # Wait before analog read [µsec]
        return([frl, frr, fr, frq, dis])

    def measureZoom(self):
        self.readData(9980000, 10020000, 50)
        maxAm = np.max(self.Am)
        minAm = np.min(self.Am)
        idxAm = np.argmax(self.Am)
        frAm = self.Fr[idxAm]
        GFR = self.Fr[idxAm-20:idxAm+20]
        GAM = self.Am[idxAm-20:idxAm+20]
        print(maxAm, idxAm)
        print("kuna 0");
        il = idxAm - 10
        ih = idxAm + 9
        # for ih in range(idxAm, len(self.Am)):
        #     # if self.Am[ih] < 0.7 * maxAm:
        #     if self.Am[ih] < minAm + 0.6 * (maxAm - minAm):
        #         break
        # for il in range(idxAm, 0, -1):
        #     # if self.Am[il] < 0.7 * maxAm:
        #     if self.Am[il] < minAm + 0.3 * (maxAm - minAm):
        #         break
        print('il = ',il,'ih = ',ih,'Fr[il] = ',self.Fr[il],'Fr[ih] = ',self.Fr[ih])
        print("kuna 1");
        self.readData(int(self.Fr[il]), int(self.Fr[ih]), 10)
        print("kuna 2");
        self.plotData()
        # self.GraphA.plot(GFR[idxAm-20,idxAm+20],GAM[idxAm-20,idxAm+20], pen=pg.mkPen(color='#7F7F7F', width=2))
        self.GraphA.plot(GFR,GAM, pen=pg.mkPen(color='#7F7F7F', width=2))
        print("kuna 3");
        [frl, frr, fr, frq, dis] = self.readMax()
        print("kuna 4");
        fleft = int(self.ff[0])
        fright = int(self.ff[self.n-1])

        minam = self.minam #3800
        topam = self.topam #1000 * round(1 + np.max(self.aa) / 1000)
        print('Frl = ',frl,'Fr = ',fr,'Frr = ',frr,'Frq = ',frq,'Dis = ',dis,'F[0]=',fleft,'F[n]=',fright)
        print("kuna 5");
        self.GraphA.plot(self.ff,self.aa, pen=pg.mkPen(color='#00FFFF', width=2))
        self.GraphA.plot([fr,fr], [minam,topam], pen=pg.mkPen(color='#FF00FF', width=2))
        self.GraphA.plot([frq,frq], [minam,topam], pen=pg.mkPen(color='#FF0000', width=3)) #symbol='o')
        self.GraphA.plot([frAm,frAm], [minam,topam], pen=pg.mkPen(color='#DFDF7F', width=2))
        # text = self.GraphA.TextItem(str(xLabel[i]), anchor=(0.3,-0.5), angle=90)
        # self.frq_value.setPos(QtCore.QPointF(frq+1000,maxAm))
        # self.frq_value.setPos(QtCore.QPointF(10003400,6000))
        # self.frq_value.setText(str(frq))
        frq_labelitem = self.frq_value.getLabel(self.frq_style)
        frq_labelitem.setText(str(frq))
        # for item in self.GraphA.legend.items:
        #     for single_item in item:
        #         if isinstance(single_item, pg.graphicsItems.LabelItem.LabelItem):
        #             single_item.setText(str(frq), **self.frq_style)

        print(self.s,self.n,self.a,self.b,self.c)
        idx = 0
        self.polyf = np.empty(fright-fleft)
        self.polya = np.empty(fright-fleft)
        print("kuna 6");
        for fff in range(fleft,fright):
            iii = (float(fff) - self.ff[0]) / float(self.s)
            aaa = self.a * iii * iii + self.b * iii + self.c
            self.polya[idx] = aaa
            self.polyf[idx] = fff
            # if idx % 32 == 0:
            # print(idx,iii,fff,aaa)
            idx += 1
        print("kuna 7");
        self.GraphA.plot(self.polyf,self.polya, pen=pg.mkPen(color='#808000', width=2))
        print("kuna 8");


    def measurePlot(self):
        lowF = int(self.lowLabel.text())
        highF = int(self.highLabel.text())
        stepF = int(self.stepLabel.text())
        self.readData(lowF, highF, stepF)
        self.plotData()
        
    def OpenButtonClicked(self):
        self.zoom = 0
        self.measurePlot()
    
    def ZoomButtonClicked(self):
        self.zoom = 1
        self.measureZoom()

    def showPlot(self):
        if self.inplot or self.auto == 0:
            return
        self.inplot = 1
        if self.zoom:
            self.measureZoom()
        else:
            self.measurePlot()
        self.inplot = 0

    def AutoButtonClicked(self):
        if self.auto:
            self.auto = 0
            self.AutoButton.setStyleSheet("background-color: none")
            self.ZoomButton.setStyleSheet("background-color: none")
            self.OpenButton.setStyleSheet("background-color: none")
            font = QtGui.QFont()
            font.setPointSize(7)
            self.AutoButton.setFont(font)
            self.ZoomButton.setFont(font)
            self.OpenButton.setFont(font)
        else:
            self.auto = 1
            self.AutoButton.setStyleSheet("background-color: green")
            font = QtGui.QFont()
            font.setPointSize(7)
            self.AutoButton.setFont(font)
            if self.zoom:
                self.ZoomButton.setStyleSheet("background-color: yellow")
                font = QtGui.QFont()
                font.setPointSize(7)
                self.ZoomButton.setFont(font)
            else:
                self.OpenButton.setStyleSheet("background-color: yellow")
                font = QtGui.QFont()
                font.setPointSize(7)
                self.OpenButton.setFont(font)

        # self.measurePlot()
        # lowF = int(self.lowLabel.text())
        # highF = int(self.highLabel.text())
        # stepF = int(self.stepLabel.text())
        # self.readData(lowF, highF, stepF)
        # self.plotData()

    def DebugButtonClicked(self):
        self.Instrument.port = self.PortName
        self.Instrument.open()
        self.Instrument.timeout = 0
        cmd = 'M0\n'
        print(cmd)
        self.Instrument.write(cmd.encode())
        app_encoding = "utf-8"
        buffer = ''
        while 1:
            buffer += self.Instrument.read(self.Instrument.inWaiting()).decode(app_encoding)
            if 's' in buffer:
                break
        self.Instrument.close()
        Buff = buffer.splitlines()
        print('DEBUG:\n',buffer)
