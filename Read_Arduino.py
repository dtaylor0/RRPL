#!/usr/bin/env python3
import serial
from time import sleep
import sys
import time
import subprocess
from math import *
serialPortWorks = True
users={'Pi':['/dev/ttyUSB0'],'aaron':['COM6','COM3','COM7','COM4']}
ser=None
f=None
f1=None
start=0
stop=0
duration=0
data=[]
#Array Denotation
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
#camera boolean, have to change index values later
cam=14
#Quaterion Preset
qa=1
qb=0
qc=0
qd=0
alpha=0
cmd=0


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
            p = subprocess.Popen(['python','/rasp_record.py'])
            camIsOn = True
        except:
            print("oof")
            return
    elif data[cam]==0 and camIsOn:
        try:
            #end camera program
            p.terminate()
            camIsOn = False
        except:
            print("oof 2")
            return


#File
file=open("Quat.txt","w")
def Start():
    global start
    start=time.time()
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
        sleep(0.1)
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
    print(hasLaunched)
    print(mbo)
    print(apogeeReached)
    print(hasLanded)
    f = open('ard_log.txt', 'a+')
    f.write(line + '/n')
    f.close()
    #print(strData)


def QCF():
    global qa
    global qb
    global qc
    global qd
    global cmd
    if len(data)<6:
        return
    else:
        gx=((data[Gx]*3.14)/180)
        gy=((data[Gy]*3.14)/180)
        gz=((data[Gz]*3.14)/180)
        wa=0.0
        wb=gx
        wc=gy
        wd=gz
        qdota = (wa*qa - wb*qb - wc*qc - wd*qd) * -0.5
        qdotb = (wa*qb + wb*qa + wc*qd - wd*qc) * -0.5
        qdotc = (wa*qc - wb*qd + wc*qa + wd*qb) * -0.5
        qdotd = (wa*qd + wb*qc - wc*qb + wd*qa) * -0.5
        qwa = qa + qdota * duration
        qwb = qb + qdotb * duration
        qwc = qc + qdotc * duration
        qwd = qd + qdotd * duration
        norm = sqrt(qwa*qwa + qwb*qwb + qwc*qwc + qwd*qwd)
        qwa = qwa/norm
        qwb = qwb/norm
        qwc = qwc/norm
        qwd = qwd/norm
        aa=0
        ab=data[Ax]
        ac=data[Ay]
        ad=data[Az]
        norma = sqrt(ab*ab + ac*ac + ad*ad)
        ab = ab/norma
        ac = ac/norma
        ad = ad/norma
        gb = (2*qwa*qwa - 1 + 2*qwb*qwb)*ab + (2*qwc*qwb + 2*qwa*qwd)*ac + (2*qwd*qwb - 2*qwa*qwc)*ad
        gc = (2*qwb*qwc - 2*qwa*qwd)*ab + (2*qwa*qwa - 1 + 2*qwc*qwc)*ac + (2*qwd*qwc + 2*qwa*qwb)*ad
        gd = (2*qwb*qwd + 2*qwa*qwc)*ab + (2*qwc*qwd - 2*qwa*qwb)*ac + (2*qwa*qwa - 1 + 2*qwd*qwd)*ad
        normb = sqrt(gb*gb + gc*gc + gd*gd)
        gb = gb/normb
        gc = gc/normb
        gd = gd/normb
        if (gd >= 0):
            q_acca = sqrt((gd + 1)*0.5)
            q_accb = -gc/2*q_acca
            q_accc = gb/2*q_acca
            q_accd = 0.0
            normc = sqrt(q_acca*q_acca + q_accb*q_accb + q_accc*q_accc + q_accd*q_accd)
            q_acca = q_acca/normc
            q_accb = q_accb/normc
            q_accc = q_accc/normc
            q_accd = q_accd/norm
        else:
            q_acca = -gc/sqrt(2 - 2*gd)
            q_accb = sqrt((1 - gd)/2)
            q_accc = 0.0
            q_accd = gb/sqrt(2 - 2*gd)
            normc = sqrt(q_acca*q_acca + q_accb*q_accb + q_accc*q_accc + q_accd*q_accd)
            q_acca = q_acca/normc
            q_accb = q_accb/normc
            q_accc = q_accc/normc
            q_accd = q_accd/normc
        if(q_acca > 0.9):
            q_acca = (1 - alpha) + alpha * q_acca 
            q_accb = alpha * q_accb
            q_accc = alpha * q_accc
            q_accd = alpha * q_accd
            normc = sqrt(q_acca*q_acca + q_accb*q_accb + q_accc*q_accc + q_accd*q_accd)
            q_acca = q_acca/normc
            q_accb = q_accb/normc
            q_accc = q_accc/normc
            q_accd = q_accd/normc
        else:
            angle = acos(q_acca)
            q_acca = sin((1 - alpha) * angle)/sin(angle) + sin(alpha * angle) * q_acca/sin(angle)
            q_accb = sin(alpha * angle) * q_accb/sin(angle)
            q_accc = sin(alpha * angle) * q_accc/sin(angle)
            q_accd = sin(alpha * angle) * q_accd/sin(angle)
        qa = qwa * q_acca - qwb * q_accb - qwc * q_accc - qwd * q_accd
        qb = qwa * q_accb + qwb * q_acca + qwc * q_accd - qwd * q_accc
        qc = qwa * q_accc - qwb * q_accd + qwc * q_acca + qwd * q_accb
        qd = qwa * q_accd + qwb * q_accc - qwc * q_accb + qwd * q_acca
        normd = sqrt(qa*qa + qb*qb + qc*qc + qd*qd)
        qa = qa/normd
        qb = qb/normd
        qc = qc/normd
        qd = qd/normd
        val0=2*acos(qa)
        if(val0<=0.01):
            val1 = qb
            val2 = qc
            val3 = qd
            cmd=(str(val0)+" "+str(val1)+" "+str(val2)+" "+str(val3))
        else:
            val1 = qb/sin(val0/2)
            val2 = qc/sin(val0/2)
            val3 = qd/sin(val0/2)
            cmd=(str(val0)+" "+str(val1)+" "+str(val2)+" "+str(val3))
def SerWrite():
    if serialPortWorks==True:
        ser.write(cmd.encode())
    else:
        print(cmd)
def FileWrite():
    file.write(str(cmd) +"\n")
    print(str(cmd))
def Stop():
    global start
    global stop
    global duration
    stop=time.time()
    duration=stop-start


FindData()
while True:
    Start()
    GetData()
    QCF()
    CheckCamera()
    #SerWrite()
    FileWrite()
    Stop()
