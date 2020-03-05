#!/usr/bin/env python3
import serial
from time import sleep
import sys
import time
import subprocess
import datetime as dt
serialPortWorks = True
users={'Pi':['/dev/ttyUSB0','/dev/ttyUSB1'],'aaron':['COM6','COM3','COM7','COM4']}
ser=None
#f=None
f1=None
data=[]
#Array Denotation
alt=0
#GPS
GPS_LA=9
GPS_LO=10
#gyroscope
Gx=1
Gy=2
Gz=3
#accelerometer
Ax=4
Ay=5
Az=6
#magnemometer
#Mx=10
#My=11
#Mz=12
#time
t=7
#camera boolean, have to change index values later
cam=8

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

#landed vars
hasLanded=False
TOL_Landed=0.5
TOL_Height=100
heightAtLaunch=0

timeLaunched=0
timeLanded=0

recentData=[]

#file to write to
filename='flightData-'+dt.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")+'.txt'


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

def CheckMBO():
    global hasLaunched
    global mbo
    if not hasLaunched:
        return
    #if vertical acceleration is < 0
    if recentData[-1][Az]<0:
        mbo=True

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



#camera control
camIsOn = False
def CheckCamera():
    if len(data)<=cam:
        return
    global camIsOn
    if data[cam]==1 and not camIsOn:
        try:
            #run camera program
            p = subprocess.Popen(['sudo','python','/rasp_record.py'])
            camIsOn = True
        except:
            print("oof")
            return
    elif (data[cam]==0 or hasLanded) and camIsOn:
        try:
            #end camera program
            p.terminate()
            camIsOn = False
        except:
            print("oof 2")
            return



def FindData():
    global ser
    global f
    global f1
    global serialPortWorks
    global data
    try:
        user=sys.argv[1]
    except:
        print ('No user given, cannot check serial ports. '+
               'Function call should be \"py interpretData.py {user} {file (optional)}\"')
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
            print ('No serial port or file detected')
            sys.exit()
        f1=open(fName, "r")

def GetData():
    global ser
    global data
    global f
    if serialPortWorks==True:
        while (ser.in_waiting <1):
            pass
        line = ser.readline().decode('utf-8')[:-1]
        strData = line.split()
        if (len(strData) <10):
            return
        data = [float(i) for i in strData]
        AddDataLine(data)
    if serialPortWorks==False:
        line=f1.readline()
        if len(line)<1:
            sys.exit()
        strData=line.split()
        if len(strData)<10:
            return
        try:
            data = [float(i) for i in strData]
        except:
            return
    AddDataLine(data)
    if not hasLaunched:
        CheckLaunch()
    elif not mbo:
        CheckMBO()
    elif not apogeeReached:
        CheckApogee()
    if apogeeReached and not hasLanded:
        CheckLanded()
    if mbo and serialPortWorks:
        ser.write("a".encode())
    f = open(filename, 'a+')
    #f.write(line)
    print(line)
    f.write(' '.join(strData)+'\n')
    f.close()
    #print(strData)


def SerWrite():
    if serialPortWorks==True:
        ser.write(cmd.encode())
    else:
        print(cmd)
def FileWrite():
    file.write(str(cmd) +"\n")
    print(str(cmd))


FindData()
while True:
    GetData()
    CheckCamera()
    #SerWrite()
