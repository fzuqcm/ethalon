import sys
from PyQt5 import QtWidgets, QtGui
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
    Buff = ''
    Fr = []
    Am = []
    Ph = []
    ff = []
    aa = []
    polyf = []
    polya = []
    n = 0
    s = 0
    a = 0
    b = 0
    c = 0

    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)

        self.OpenButton.clicked.connect(self.OpenButtonClicked)
        self.ZoomButton.clicked.connect(self.ZoomButtonClicked)
        self.DefaultViewButton.clicked.connect(self.DefaultViewButtonClicked)
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
        
        # self.GraphB.setClipToView(True)
        # self.GraphB.setDownsampling(mode='peak')
        # self.TimeAxisB = DateAxisItem(orientation='bottom')
        # self.TimeAxisB.attachToPlotItem(self.GraphB.getPlotItem())
        self.GraphB.setLabel('bottom', 'Frequency', 'Hz', color='#000000', **{'font-size': '7pt'})
        self.GraphB.getAxis('bottom').setPen(pg.mkPen(color='#000000', width=1))
        self.GraphB.setLabel('left', 'Phase', '', color='#000000', **{'font-size': '7pt'})
        self.GraphB.getAxis('left').setPen(pg.mkPen(color='#000000', width=1))
        self.GraphB.setLimits(xMin=0)
        self.GraphB.setBackground('#FFFFFF')
        self.GraphB.showGrid(x=True,y=True)
        
    def closeEvent(self, event):
        event.accept()

    def ExportButtonClicked(self):
        QtGui.QApplication.processEvents()
        exporter = pg.exporters.ImageExporter(self.GraphA.plotItem)
        exporter.export(str(self.lineEdit.text())+'A.png')
        exporter = pg.exporters.ImageExporter(self.GraphB.plotItem)
        exporter.export(str(self.lineEdit.text())+'B.png')
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
            print('pname:',pidx,pname)
            if pname[0:10] == '/dev/ttyAC':
                qcmidx = pidx
                print(qcmidx)
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
        cmd = str(low) + ';' + str(high) + ';' + str(step) + '\n'
        print(cmd)
        self.Instrument.write(cmd.encode())
        app_encoding = "utf-8"
        buffer = ''
        while 1:
            buffer += self.Instrument.read(self.Instrument.inWaiting()).decode(app_encoding)
            if 's' in buffer:
                break
        self.Instrument.close()
        self.Buff = buffer.splitlines()
        buff = self.Buff
        print(len(buff))
        print(buff[1])
        print(buff)
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
            # print(idx, freq, str(ampl[idx]), str(phase[idx]))
            # text = pg.TextItem(html='<div style="text-align: center"><span style="color: #000000;"> %s</span></div>',anchor=(0.5, -1))
            # text.setText('%s'%str(ampl[idx]))
            idx += 1

    def plotData(self):
        self.GraphA.clear()
        self.GraphA.plot(self.Fr,self.Am, pen=pg.mkPen(color='#0000FF', width=3))
        self.GraphB.clear()
        self.GraphB.plot(self.Fr,self.Ph, pen=pg.mkPen(color='#007F00', width=3))

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
        print('DEBUG:\n',buffer)
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

    def ZoomButtonClicked(self):
        self.readData(9980000, 10020000, 100)
        maxAm = np.max(self.Am)
        idxAm = np.argmax(self.Am)
        print(maxAm, idxAm)
        for ih in range(idxAm, len(self.Am)):
            if self.Am[ih] < 0.7 * maxAm:
                break
        for il in range(idxAm, 0, -1):
            if self.Am[il] < 0.7 * maxAm:
                break
        print(il,ih,self.Fr[il], self.Fr[ih])
        self.readData(int(self.Fr[il]), int(self.Fr[ih]), 10)
        self.plotData()
        [frl, frr, fr, frq, dis] = self.readMax()
        fleft = int(self.ff[0])
        fright = int(self.ff[self.n-1])
        topam = 1000 * round(1 + np.max(self.aa) / 1000)
        print('Frl = ',frl,'Fr = ',fr,'Frr = ',frr,'Frq = ',frq,'Dis = ',dis,'F[0]=',fleft,'F[n]=',fright)
        self.GraphA.plot(self.ff,self.aa, pen=pg.mkPen(color='#00FFFF', width=2))
        self.GraphA.plot([fr,fr], [3800,topam], pen=pg.mkPen(color='#FF00FF', width=2))
        self.GraphA.plot([frq,frq], [3800,topam], pen=pg.mkPen(color='#FF0000', width=3)) #symbol='o')
        print(self.s,self.n,self.a,self.b,self.c)
        idx = 0
        self.polyf = np.empty(fright-fleft)
        self.polya = np.empty(fright-fleft)
        for fff in range(fleft,fright):
            iii = (float(fff) - self.ff[0]) / float(self.s)
            aaa = self.a * iii * iii + self.b * iii + self.c
            self.polya[idx] = aaa
            self.polyf[idx] = fff
            # if idx % 32 == 0:
            print(idx,iii,fff,aaa)
            idx += 1
        self.GraphA.plot(self.polyf,self.polya, pen=pg.mkPen(color='#808000', width=2))

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
        # [frr, frl, fr, frq] = self.readMax()
        # print('Frl = ',frl,'Fr = ',fr,'Frr = ',frr,'Frq = ',frr)
        # self.GraphA.plot([frl,frl], [0,4500], pen=pg.mkPen(color='#00FF00', width=2))
        # self.GraphA.plot([fr,fr], [0,4500], pen=pg.mkPen(color='#FF00FF', width=3))
        # self.GraphA.plot([frr,frr], [0,4500], pen=pg.mkPen(color='#00FF00', width=2))
        # self.GraphA.plot([frq,frq], [0,4500], pen=pg.mkPen(color='#FF0000', width=2)) #symbol='o')

    def OpenButtonClicked(self):
        # self.PortSelect.setEnabled(False)
        # self.Instrument.port = self.PortName
        # self.Instrument.open()
        # self.Instrument.timeout = 0

        lowF = int(self.lowLabel.text())
        highF = int(self.highLabel.text())
        stepF = int(self.stepLabel.text())
 
        # cmd = str(self.lowLabel.text()) + ';' + str(self.highLabel.text()) + ';' + str(self.stepLabel.text()) + '\n'
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

        self.readData(lowF, highF, stepF)
        self.plotData()
        # self.readMax()
        # buff = self.Buff #buffer.splitlines()
        # print(len(buff))
        # print(buff[1])
        # frequency = np.empty(len(buff)-2)
        # ampl = np.empty(len(buff)-2)
        # phase = np.empty(len(buff)-2)
        # idx = 0
        # for freq in range(lowF, highF + 1, step):
        #     if idx > 0:
        #         am, ph = buff[idx-1].split(';')
        #         frequency[idx-1] = float(freq)
        #         ampl[idx-1] = float(am)
        #         phase[idx-1] = float(ph)
            # print(idx, freq, str(ampl[idx]), str(phase[idx]))
            # text = pg.TextItem(html='<div style="text-align: center"><span style="color: #000000;"> %s</span></div>',anchor=(0.5, -1))
            # text.setText('%s'%str(ampl[idx]))
            # idx += 1

        # dialog = QtWidgets.QFileDialog(self)
        # dialog.setNameFilter('*.qcm')
        # dialog.open()
        # if dialog.exec():
        #     fname = dialog.selectedFiles()[0]
        #     F = open(fname,'rb')
            
        #     FreqShiftA = pickle.load(F)
        #     MarksXPosA = pickle.load(F)
        #     MarksYPosA = pickle.load(F)
        #     MarksTextA = pickle.load(F)

        # hour = [1,2,3,4,5,6,7,8,9,10]
        # temperature = [30,32,34,32,33,31,29,32,35,45]
        # self.GraphA.plot(hour, temperature)
        # print(frequency)

        # self.GraphA.clear()
        # self.GraphA.plot(frequency,ampl, pen=pg.mkPen(color='#0000FF', width=3))

        # self.GraphB.clear()
        # self.GraphB.plot(frequency,phase, pen=pg.mkPen(color='#007F00', width=3))
        # self.GraphB.plot(range(0,len(phase)),phase, pen=pg.mkPen(color='#00FF00', width=3))

        #     for x in range(0,len(MarksTextA)):
        #         text = pg.TextItem(html='<div style="text-align: center"><span style="color: #000000;"> %s</span></div>',anchor=(0.5, -1)) 
        #         text.setText('%s'%str(MarksTextA[x]))
        #         text.setPos(MarksXPosA[x], MarksYPosA[x])
        #         self.GraphA.addItem(text)
        #         arrow = pg.ArrowItem(angle=90,brush='000000')
        #         arrow.setPos(MarksXPosA[x], MarksYPosA[x])
        #         self.GraphA.addItem(arrow)

        #     self.GraphA.enableAutoRange('xy')

        #     FreqShiftB = pickle.load(F)
        #     MarksXPosB = pickle.load(F)
        #     MarksYPosB = pickle.load(F)
        #     MarksTextB = pickle.load(F)

        #     self.GraphB.clear()
        #     self.GraphB.plot(range(0,len(FreqShiftB)),FreqShiftB, pen=pg.mkPen(color='#00FF00', width=3))
            
        #     for x in range(0,len(MarksTextB)):
        #         text = pg.TextItem(html='<div style="text-align: center"><span style="color: #000000;"> %s</span></div>',anchor=(0.5, -1)) 
        #         text.setText('%s'%str(MarksTextB[x]))
        #         text.setPos(MarksXPosB[x], MarksYPosB[x])
        #         self.GraphB.addItem(text)
        #         arrow = pg.ArrowItem(angle=90,brush='000000')
        #         arrow.setPos(MarksXPosB[x], MarksYPosB[x])
        #         self.GraphB.addItem(arrow)

        #     self.GraphB.enableAutoRange('xy')
