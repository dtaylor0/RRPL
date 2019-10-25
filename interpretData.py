import serial
import sys
from time import sleep
import os
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.interpolate import spline

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

xs=[]
ys=[]

currAlt=0

#plt.style.use('fivethirtyeight')
fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)
x_vals = []
y_vals = []

ser=serial.Serial('/dev/tty.usbserial-1410',9600)



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
    while (ser.in_waiting < 1):
        pass
    line = ser.readline().decode('utf-8')[:-1]
    strData = line.split()
    if (len(strData) < 2):
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
    x_vals.append(data[t])
    y_vals.append(currAlt)
    ax1.cla()
    ax1.plot(x_vals, y_vals)
   
ani = FuncAnimation(plt.gcf(), animate, interval = 50)
plt.show()





