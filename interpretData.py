import serial
import sys
from time import sleep
import datetime as dt
import os
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

alt=0
#GPS
GPS_LA=1
GPS_LO=2
#gyroscope
Gx=3
Gy=4
Gz=5
#accelerometer
Ax=6
Ay=7
Az=8
#magnemometer
Mx=9
My=10
Mz=11
#time
t=12

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
minCertaintyMain=2
mainDeployed=False

#landed vars
hasLanded=False
TOL_Landed=1

#list of last 10 data readings
recentData=[]


currAlt=0
currAy=0

#plt.style.use('fivethirtyeight')
fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)
ax2 = ax1.twinx()
x_vals = []
y_vals = []
y2_vals = []

ser=serial.Serial('/dev/cu.usbserial-1420',9600)
#ser=serial.Serial('/dev/tty.usbserial-1410',9600)
'''
while True:
    if (ser.in_waiting>0):
        line = ser.readline().decode('utf-8')[:-1]
        print(line.split())
'''

def AddDataLine(dataLine):
    if len(recentData)>=10:
        recentData.pop(0)
    recentData.append(dataLine)

def CheckLaunch():
    global hasLaunched
    if len(recentData)<2:
        return
    if ((recentData[-1][alt])-(recentData[-2][alt])) > TOL_Launch:
        hasLaunched=True

def CheckMBO():
    global hasLaunched
    global mbo
    if not hasLaunched:
        return
    if recentData[-1][Ay]>0:
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
        apogeeHeight=recentData[-3][alt]

def CheckMainDeployed():
    global apogeeReached
    global mainDeployed
    global mainConfidence
    global minCertaintyMain
    if not apogeeReached:
        return
    currVelocity=(recentData[-1][alt]-recentData[-2][alt])/(recentData[-1][t]-recentData[-2][t])
    prevVelocity=(recentData[-2][alt]-recentData[-3][alt])/(recentData[-2][t]-recentData[-3][t])
    if abs(currVelocity-prevVelocity)>TOL_Main:
        mainConfidence+=1
    if mainConfidence >= minCertaintyMain:
        mainDeployed=True

def CheckLanded():
    global mainDepployed
    global hasLanded
    if not apogeeReached:
        return
    if abs(recentData[9][alt]-recentData[0][alt])<TOL_Landed:
        hasLanded=True


def animate(i):
    global ser
    global currAlt
    global currAy
    while (ser.in_waiting < 1):
        pass
    line = ser.readline().decode('utf-8')[:-1]
    strData = line.split()
    if (len(strData) < 10):
        return
    print(line)
    data=[float(i) for i in strData]
    AddDataLine(data)
    if not hasLaunched:
        CheckLaunch()
    if not mbo:
        CheckMBO()
    if not apogeeReached:
        CheckApogee()
    if not mainDeployed:
        CheckMainDeployed()
    if not hasLanded:
        CheckLanded()
    print 'has launched: %s\nmbo: %s\napogee reached: %s\nmain deployed: %s\nhas landed: %s\n' % (hasLaunched, mbo, apogeeReached, mainDeployed, hasLanded)
    currAlt= 0.1 * data[alt] + 0.9 * currAlt
    currAy=0.1 + data[Ay] + 0.9 * currAy
    x_vals.append(data[t])
    y_vals.append(currAlt)
    y2_vals.append(currAy)
    ax1.cla()
    ax2.cla()
    ax1.set_title(dt.datetime.now().strftime("%Y-%m-%d_%H.%M.%S"))
    color = 'r'
    ax1.set_xlabel('time (s)')
    ax1.set_ylabel('altitude (m)',color=color)
    ax1.plot(x_vals, y_vals,color=color)
    color = 'g'
    ax2.set_ylabel('vertical acceleration (m/s^2)',color=color)
    ax2.plot(x_vals,y2_vals,color=color)
   
ani = FuncAnimation(plt.gcf(), animate, interval = 50)
plt.show()





