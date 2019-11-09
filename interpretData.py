import serial
import sys
from time import sleep
import datetime as dt
import os
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import tkinter

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
barom=1
Gx=2
Gy=3
Gz=4
Ax=5
Ay=6
Az=7
Mx=8
My=9
Mz=10
t=11
'''
time=0.0

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

currAlt=0
currAy=0
Ay_max=0.0

timeLaunched=0
timeLanded=0

serialPortWorks=True

fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)
ax2 = ax1.twinx()
x_vals = []
y_vals = []
y2_vals = []
try:
    ser=serial.Serial('/dev/cu.usbserial-1420',9600)
except:
    try:
        ser=serial.Serial('/dev/cu.usbserial-1410',9600)
    except:
        serialPortWorks=False
        try:
            fName=sys.argv[1]
        except:
            print 'Error: No working serial port and no file name in arguments.'
            sys.exit()
        f=open(fName,"r")

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
    if recentData[-1][Ay]<0:
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


'''
def CheckMainDeployed():
    global mainDeployed
    global mainConfidence
    global minCertaintyMain
    currVelocity=(recentData[-1][alt]-recentData[-2][alt])/(recentData[-1][t]-recentData[-2][t])*1000
    prevVelocity=(recentData[5][alt]-recentData[4][alt])/(recentData[5][t]-recentData[4][t])*1000
    prevVelocity2=(recentData[1][alt]-recentData[0][alt])/(recentData[1][t]-recentData[0][t])*1000
    currAcc=(currVelocity-prevVelocity)/(recentData[-1][t]-recentData[4][t])*1000
    prevAcc=(prevVelocity-prevVelocity2)/(recentData[5][t]-recentData[0][t])*1000
    #print 'difference in acc: %f' % (abs(currAcc/1000-prevAcc/1000))
    #print 'currAcc: %f\nprevAcc: %f' % (currAcc/1000, prevAcc/1000)
    
    if currAcc>=0:
        mainConfidence+=1
    if mainConfidence>=minCertaintyMain:
        mainDeployed=True
        #mainConfidence+=1
    #if abs(currVelocity-prevVelocity)>TOL_Main:
    #    mainConfidence+=1
    #if mainConfidence >= minCertaintyMain:
        #mainDeployed=True
'''

def CheckLanded():
    global hasLanded
    global timeLanded
    global heightAtLaunch
    if not apogeeReached:
        return
    if recentData[-1][alt]-heightAtLaunch > TOL_Height:
        return
    if abs(recentData[9][alt]-recentData[0][alt])<TOL_Landed:
        hasLanded=True
        timeLanded=recentData[0][t]


def animate(i):
    global ser
    global currAlt
    global currAy
    global Ay_max
    global time
    if serialPortWorks:
        while (ser.in_waiting < 1):
            pass
        line = ser.readline().decode('utf-8')[:-1]
    else:
        line = f.readline()
    strData = line.split()
    if (len(strData) < 10):
        return
    print(line)
    data=[float(i) for i in strData]
    data[Ay] *= -9.81
    data.append(time)
    time+=0.5
    AddDataLine(data)
    if data[Ay]>Ay_max:
        Ay_max=data[Ay]
    #print "current highest Ay: %f" % (Ay_max)
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
    #print 'has launched: %s\nmbo: %s\napogee reached: %s\nmain deployed: %s\nhas landed: %s\n' % (hasLaunched, mbo, apogeeReached, mainDeployed, hasLanded)
    print 'has launched: %s\nmbo: %s\napogee reached: %s\nhas landed: %s\n' % (hasLaunched, mbo, apogeeReached, hasLanded)
    if hasLanded:
        print 'flight duration: %f' % ((timeLanded-timeLaunched))
    if apogeeReached:
        print 'height at apogee: %f' % (apogeeHeight)
    currAlt= 0.1 * data[alt] + 0.9 * currAlt
    currAy=0.1 + data[Ay] + 0.9 * currAy
    x_vals.append(data[t]/1000.0)
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
f.close()




