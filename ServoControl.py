#!/usr/bin/env python3

import sys
import os
from time import sleep
from PyQt5 import QtWidgets, Qt
from pyqtgraph.Qt import *
from PyQt5.QtGui import *
import serial
import threading

#index vars
temp_1 = 1
temp_2 = 2
t = 3

Data = []

serialPortWorks=True
ser=None
f=None
users={'drew':['/dev/cu.usbserial-1410','/dev/cu.usbserial-1420'],
        'aaron':['COM3','COM6','COM7']}


lock=threading.Lock()
def GetData():
    global ser
    global Data
    with lock:
        while True:
            while (ser.in_waiting < 1):
                pass
            line = ser.readline().decode('utf-8')[:-1]
            print(line)
            strData = line.split()
            if len(strData)<3 or not strData[0]=="Sending":
                continue
            try:
                strData[0]="0"
                Data=[float(i) for i in strData]
            except:
                continue



def window():
    global Data
    app = QtGui.QApplication(sys.argv)

    #initialize main window, mainLayout
    w = QtGui.QWidget()
    mainLayout = QtWidgets.QGridLayout(w)

    #set background color for w
    w.setStyleSheet("background-color: #e8e8e8")

    #initialize dataLayout
    data = QtGui.QWidget()
    dataLayout = QtWidgets.QGridLayout(data)

    #initialize style sheet for data
    style='''
color: #80fc75;
background-color: black;
border: 4px inset grey;
max-height: 50px;
font-size:25px;'''

    #add logo
    logo = QtGui.QLabel(w)
    pixmap= QPixmap('logo.png')
    logo.setPixmap(pixmap)
    logo.setFixedHeight(pixmap.height())
    dataLayout.addWidget(logo,0,0)


    #add temp1 monitor
    temp1 = QtGui.QLabel(w)
    temp1.setText("waiting for data...")
    temp1.setStyleSheet(style)
    #currAlt.setFont("digital-7")
    dataLayout.addWidget(temp1,1,0)

    #add GPS_LA monitor
    currGPS_LA = QtGui.QLabel(w)
    currGPS_LA.setText("waiting for data...")
    currGPS_LA.setStyleSheet(style)
    dataLayout.addWidget(currGPS_LA,2,0)

    #add GPS_LO monitor
    currGPS_LO = QtGui.QLabel(w)
    currGPS_LO.setText("waiting for data...")
    currGPS_LO.setStyleSheet(style)
    dataLayout.addWidget(currGPS_LO,3,0)



    #create end program button, add to dataLayout
    endButton = QtGui.QPushButton(w)
    endButton.setText("End Program")
    endButton.setStyleSheet("background-color:white;")
    endButton.clicked.connect(lambda: os._exit(0))
    dataLayout.addWidget(endButton,4,0)

    #add data to mainLayout
    mainLayout.addWidget(data,0,0)

    #add dial
    def sliderMoved():
        print(ServoDial.value())
    
    ServoDial = QtGui.QDial(w)
    ServoDial.setMinimum(0)
    ServoDial.setMaximum(360)
    ServoDial.setValue(40)
    ServoDial.valueChanged.connect(sliderMoved)
    mainLayout.addWidget(ServoDial,0,1)



    def update():
        try:
            temp1.setText("Temp A: "+str(Data[temp_1])+" F")
        except:
            pass
        try:
            currGPS_LA.setText("Temp B: "+str(Data[temp_2])+" F")
        except:
            pass
        try:
            currGPS_LO.setText("Time: "+str(Data[t]))
        except:
            pass

    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(100)

    #start showing window
    #w.setGeometry(app.desktop().availableGeometry())
    w.setWindowTitle("RRPL Servo Control")
    w.show()
    sys.exit(app.exec_())

#checks whether data will be gotten from an input file or a serial port
def FindData():
    global ser
    global f
    global serialPortWorks
    try:
        user=sys.argv[1]
    except:
        print ('Error: No user given, cannot check serial ports. ')
        sys.exit()


    if user in users.keys() and len(sys.argv)<3:
        for port in users.get(user):
            try:
                ser=serial.Serial(port,115200)
                return
            except:
                pass

    if ser==None:
        print("Error: Unable to find serial input in any ports. Exiting...")
        sys.exit()

if __name__ == '__main__':
    f=FindData()
    if not ser == None:
        getData = threading.Thread(name='GetData',target=GetData)
        getData.start()
    window()
