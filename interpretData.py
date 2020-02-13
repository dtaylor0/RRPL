#!/usr/bin/env python3

import sys
import os
from time import sleep
import pyqtgraph as pg
from PyQt5 import QtWidgets, Qt
from pyqtgraph.Qt import *
from PyQt5.QtGui import *
import serial
import threading
from playsound import playsound

'''
alt=0
barom=1
#GPS
GPS_LA=2
GPS_LO=3
#gyroscope
Gx=4
Gy=5
Gz=6
#accelerometer
Ax=7
Ay=8
Az=9
#magnemometer
Mx=10
My=11
Mz=12
#time
t=13
'''

alt=0
#gyroscope
Gx=1
Gy=2
Gz=3
#accelerometer
Ax=4
Ay=5
Az=6
#magnemometer
#Mx=8
#My=9
#Mz=10
#time
t=7
#GPS
GPS_LA=2
GPS_LO=3

x_vals=[]
y_vals=[]

#launch vars
TOL_Launch=10
hasLaunched=False

#motor burnout vars
mbo=False

#apogee vars
apogeeConfidence=0
minCertaintyApogee=2
apogeeReached=False
apogeeHeight=0

#main deployed vars
TOL_Main=4
mainConfidence=0
minCertaintyMain=50
mainDeployed=False

#landed vars
hasLanded=False
TOL_Landed=0.5
TOL_Height=100
heightAtLaunch=0

#list of last 10 data readings
recentData=[]


timeLaunched=0
timeLanded=0

serialPortWorks=True
ser=None
f=None
users={'drew':['/dev/cu.usbserial-1410','/dev/cu.usbserial-1420'],
        'aaron':['COM3','COM6','COM7']}

def Sound(name):
    playsound(name,False)

def AddDataLine(dataLine):
    if len(recentData)>=10:
        recentData.pop(0)
    recentData.append(dataLine)

def CheckLaunch():
    global hasLaunched
    global timeLaunched
    global heightAtLaunch
    if len(recentData)<2:
        return
    if ((recentData[-1][alt])-(recentData[-2][alt])) > TOL_Launch:
        hasLaunched=True
        timeLaunched=recentData[-2][t]
        heightAtLaunch=recentData[-2][alt]
        #sound=threading.Thread(target=Sound,args=("VOice/Launch.mp3",))
        #sound.start()
        #playsound("VOice/Launch.mp3",False)

def CheckMBO():
    global hasLaunched
    global mbo
    if not hasLaunched:
        return
    #if vertical acceleration is < 0
    if recentData[-1][Az]<0:
        mbo=True
        #playsound("VOice/Burnout.mp3",False)

def CheckApogee():
    global mbo
    global apogeeConfidence
    global apogeeReached
    global apogeeHeight
    if not mbo:
        return
    if recentData[-1][alt]<recentData[-2][alt]:
        apogeeConfidence+=1
    if apogeeConfidence>minCertaintyApogee:
        apogeeReached=True
        #playsound("VOice/apogee.mp3",False)
        for dataLine in recentData:
            if dataLine[alt]>apogeeHeight:
                apogeeHeight=dataLine[alt]



def CheckLanded():
    global hasLanded
    global timeLanded
    global heightAtLaunch
    if not apogeeReached:
        return
    if recentData[-1][alt]-heightAtLaunch > TOL_Height:
        return
    if abs(recentData[9][alt]-recentData[5][alt])<TOL_Landed:
        hasLanded=True
        timeLanded=recentData[0][t]
        #playsound("VOice/GroundHit.mp3",False)




class  GraphWidget(pg.GraphicsWindow):
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    def __init__(self, parent=None, **kargs):
        global f
        pg.GraphicsWindow.__init__(self, **kargs)
        self.setParent(parent)
        self.setWindowTitle('RRPL')
        p1 = self.addPlot(labels =  {'left':'Altitude', 'bottom':'Time'})
        self.ys = []
        self.curve = p1.plot(self.ys, pen=pg.mkPen({'color': "#F00", 'width': 3}))
        timer = pg.QtCore.QTimer(self)
        timer.timeout.connect(lambda: self.update(f))
        timer.start(1)

    def update(self,f):
        global x_vals
        global y_vals
        if not serialPortWorks:
            line=f.readline()
            strData=line.split()
            if len(strData)<10:
                return
            try:
                data = [float(i) for i in strData]
            except:
                return
            AddDataLine(data)
            x_vals.append(data[t])
            y_vals.append(data[alt])
            self.ys=y_vals
            self.curve.setData(self.ys)
            self.curve.setPos(data[t]/1000, 0)
        elif serialPortWorks:
            self.ys=y_vals
            self.curve.setData(self.ys)
            try:
                self.curve.setPos(x_vals[-1],0)
            except:
                self.curve.setPos(1,0)
        if not hasLaunched:
            CheckLaunch()
        elif not mbo:
            CheckMBO()
        elif not apogeeReached:
            CheckApogee()
            '''
        elif not mainDeployed:
            CheckMainDeployed()
            '''
        if apogeeReached and not hasLanded:
            CheckLanded()

lock=threading.Lock()
def GetData():
    global x_vals
    global y_vals
    global ser
    with lock:
        while True:
            while (ser.in_waiting < 1):
                pass
            line = ser.readline().decode('utf-8')[:-1]
            strData = line.split()
            if (len(strData) < 5):
                continue
            try:
                data=[float(i) for i in strData]
            except:
                continue
            x_vals.append(data[t])
            y_vals.append(data[alt])
            AddDataLine(data)


def window():
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

    #style sheet for check labels
    checkStyle='''font-size:20px'''

    #add logo
    logo = QtGui.QLabel(w)
    pixmap= QPixmap('logo.png')
    logo.setPixmap(pixmap)
    logo.setFixedHeight(pixmap.height())
    dataLayout.addWidget(logo,0,0)


    #add altitude monitor
    currAlt = QtGui.QLabel(w)
    currAlt.setText("waiting for data...")
    currAlt.setStyleSheet(style)
    #currAlt.setFont("digital-7")
    dataLayout.addWidget(currAlt,1,0)

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


    def TurnOnCamera():
        try:
            ser.write("1".encode())
        except:
            print("failure")

    #create camera control button, add to dataLayout
    cameraButton = QtGui.QPushButton(w)
    cameraButton.setText("Turn on Camera")
    cameraButton.setStyleSheet("background-color:white;")
    cameraButton.clicked.connect(lambda: TurnOnCamera())
    dataLayout.addWidget(cameraButton,5,0)

    #create end program button, add to dataLayout
    endButton = QtGui.QPushButton(w)
    endButton.setText("End Program")
    endButton.setStyleSheet("background-color:white;")
    endButton.clicked.connect(lambda: os._exit(0))
    dataLayout.addWidget(endButton,6,0)

    #add data to mainLayout
    mainLayout.addWidget(data,0,0)

    #create graph, add to mainLayout
    graph = GraphWidget(w)
    mainLayout.addWidget(graph,0,1)
    graph.show()


    checkboxes = QtGui.QWidget()
    checkboxLayout=QtWidgets.QGridLayout(checkboxes)


    #add launch checkbox label
    LaunchLabel = QtGui.QLabel(w)
    LaunchLabel.setText("Launch")
    LaunchLabel.setStyleSheet(checkStyle)
    LaunchLabel.setAlignment(QtCore.Qt.AlignCenter)
    checkboxLayout.addWidget(LaunchLabel,0,0)
    #add launch checkbox
    check1 = QtGui.QLabel(w)
    pixmap = QPixmap('unchecked.png')
    check1.setPixmap(pixmap)
    check1.setAlignment(QtCore.Qt.AlignCenter)
    checkboxLayout.addWidget(check1,1,0,alignment=QtCore.Qt.AlignCenter)
    
    #add mbo checkbox label
    MBOLabel = QtGui.QLabel(w)
    MBOLabel.setText("Motor Burnout")
    MBOLabel.setStyleSheet(checkStyle)
    MBOLabel.setAlignment(QtCore.Qt.AlignCenter)
    checkboxLayout.addWidget(MBOLabel,0,1,alignment=QtCore.Qt.AlignCenter)
    #add mbo checkbox
    check2 = QtGui.QLabel(w)
    pixmap = QPixmap('unchecked.png')
    check2.setPixmap(pixmap)
    check2.setAlignment(QtCore.Qt.AlignCenter)
    checkboxLayout.addWidget(check2,1,1,alignment=QtCore.Qt.AlignCenter)
    
    #add apogee checkbox label
    ApogeeLabel = QtGui.QLabel(w)
    ApogeeLabel.setText("Apogee")
    ApogeeLabel.setStyleSheet(checkStyle)
    ApogeeLabel.setAlignment(QtCore.Qt.AlignCenter)
    checkboxLayout.addWidget(ApogeeLabel,0,2,alignment=QtCore.Qt.AlignCenter)
    #add apogee checkbox
    check3 = QtGui.QLabel(w)
    pixmap = QPixmap('unchecked.png')
    check3.setPixmap(pixmap)
    check3.setAlignment(QtCore.Qt.AlignCenter)
    checkboxLayout.addWidget(check3,1,2,alignment=QtCore.Qt.AlignCenter)
    
    #add has landed checkbox label
    HasLandedLabel = QtGui.QLabel(w)
    HasLandedLabel.setText("Has Landed")
    HasLandedLabel.setStyleSheet(checkStyle)
    HasLandedLabel.setAlignment(QtCore.Qt.AlignCenter)
    checkboxLayout.addWidget(HasLandedLabel,0,3,alignment=QtCore.Qt.AlignCenter)
    #add landed checkbox
    check4 = QtGui.QLabel(w)
    pixmap = QPixmap('unchecked.png')
    check4.setPixmap(pixmap)
    check4.setAlignment(QtCore.Qt.AlignCenter)
    checkboxLayout.addWidget(check4,1,3,alignment=QtCore.Qt.AlignCenter)

    mainLayout.addWidget(checkboxes,1,0,2,2)


    def update():
        try:
            currAlt.setText("Altitude: "+str(recentData[-1][alt])+" m")
        except:
            pass
        try:
            currGPS_LA.setText("GPS LA: "+str(recentData[-1][GPS_LA]))
        except:
            pass
        try:
            currGPS_LO.setText("GPS LO: "+str(recentData[-1][GPS_LO]))
        except:
            pass
        try:
            #currHasLaunched.setText("Has Launched: "+str(hasLaunched))
            if hasLaunched:
                check1 = QtGui.QLabel(w)
                pixmap = QPixmap('checked.png')
                check1.setPixmap(pixmap)
                checkboxLayout.addWidget(check1,1,0,alignment=QtCore.Qt.AlignCenter)

        except:
            pass
        try:
            #currMBO.setText("Motor Burnout: "+str(mbo))
            if mbo:
                check2 = QtGui.QLabel(w)
                pixmap = QPixmap('checked.png')
                check2.setPixmap(pixmap)
                checkboxLayout.addWidget(check2,1,1,alignment=QtCore.Qt.AlignCenter)
        except:
            pass
        try:
            #apogee.setText("Apogee Reached: "+str(apogeeReached))
            if apogeeReached:
                check3 = QtGui.QLabel(w)
                pixmap = QPixmap('checked.png')
                check3.setPixmap(pixmap)
                checkboxLayout.addWidget(check3,1,2,alignment=QtCore.Qt.AlignCenter)

                ApogeeValueLabel = QtGui.QLabel(w)
                ApogeeValueLabel.setText("Apogee: "+str(apogeeHeight)+" m")
                ApogeeValueLabel.setStyleSheet(style)
                dataLayout.addWidget(ApogeeValueLabel,4,0)

        except:
            pass
        try:
            #currHasLanded.setText("Has Landed: "+str(hasLanded))
            if hasLanded:
                check4 = QtGui.QLabel(w)
                pixmap = QPixmap('checked.png')
                check4.setPixmap(pixmap)
                checkboxLayout.addWidget(check4,1,3,alignment=QtCore.Qt.AlignCenter)
        except:
            pass

    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(100)

    #start showing window
    w.setGeometry(app.desktop().availableGeometry())
    w.setWindowTitle("RRPL Ground Control")
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
        print ('Error: No user given, cannot check serial ports. '+
                'Function call should be \"python interpretData.py {user} {file (optional)}\"')
        sys.exit()


    if user in users.keys() and len(sys.argv)<3:
        for port in users.get(user):
            try:
                ser=serial.Serial(port,9600)
                return
            except:
                pass

    if ser==None:
        serialPortWorks=False
        try:
            fName=sys.argv[2]
        except:
            print ('Error: No working serial port and no file name in arguments.')
            sys.exit()
        return open(fName,"r")

if __name__ == '__main__':
    f=FindData()
    if not ser == None:
        getData = threading.Thread(name='GetData',target=GetData)
        getData.start()
    window()
