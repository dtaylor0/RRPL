import serial
import sys
from time import sleep
import datetime as dt
import os
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import Tkinter as tk
from playsound import playsound
import threading

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



time=0.0


fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)
x_vals = []
y_vals = []

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

Ay_max=0.0

timeLaunched=0
timeLanded=0

serialPortWorks=True


users={'drew':['/dev/cu.usbserial-1410','/dev/cu.usbserial-1420'],
        'aaron':['COM3','COM6','COM7']}



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
        playsound("VOice/Launch.mp3",False)

def CheckMBO():
    global hasLaunched
    global mbo
    if not hasLaunched:
        return
    #if vertical acceleration is < 0
    if recentData[-1][Ay]<0:
        mbo=True
        playsound("VOice/Burnout.mp3",False)

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
        playsound("VOice/apogee.mp3",False)
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
    if abs(recentData[9][alt]-recentData[0][alt])<TOL_Landed:
        hasLanded=True
        timeLanded=recentData[0][t]
        playsound("VOice/GroundHit.mp3",False)





def animate(i):
    global ser
    global Ay_max
    global time
    global x_vals
    global y_vals
    #if serialPortWorks:
    #    while (ser.in_waiting < 1):
    #        pass
    #    line = ser.readline().decode('utf-8')[:-1]
    if not serialPortWorks:
        line = f.readline()
        strData = line.split()
        if (len(strData) < 10):
            return
        data=[float(i) for i in strData]
        data[Ay] *= -9.81
        data.append(time)
        time+=0.5
        AddDataLine(data)
        x_vals.append(data[t])
        y_vals.append(data[alt])

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
    ax1.cla()
    ax1.set_title(dt.datetime.now().strftime("%Y-%m-%d_%H.%M.%S"))
    color = 'r'
    ax1.set_xlabel('time (s)')
    ax1.set_ylabel('altitude (m)',color=color)
    ax1.plot(x_vals, y_vals,color=color)
    return [ax1]



class GUI(tk.Tk):

    def __init__(self, *args, **kwargs):

        tk.Tk.__init__(self, *args, **kwargs)

        tk.Tk.wm_title(self, "Data Visuals")


        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand = True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in [GraphPage]:

            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(GraphPage)

    def show_frame(self, cont):

        frame = self.frames[cont]
        frame.tkraise()




stupidFont=("Comic Sans MS",35,"bold")
bigBoringFont=("Arial",35)
boringFont=("Helvetica",20)
bgColor="#b9c5ca"

class GraphPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        #set background color
        self.configure(bg=bgColor)
        
        #title label
        label = tk.Label(self, text="RRPL",font=bigBoringFont)
        label["bg"]=bgColor
        label.pack(pady=10,padx=10)

        #graph widget
        canvas = FigureCanvasTkAgg(fig, self)
        canvas.show()
        canvas.get_tk_widget().pack(side=tk.BOTTOM,fill=tk.BOTH,expand=True)

        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.RIGHT, expand=True)

        #launch label
        LaunchLabel=tk.Label(self, text='',font=boringFont,borderwidth=2,relief="sunken")
        LaunchLabel["bg"]=bgColor
        LaunchLabel.pack(anchor=tk.W,pady=10,padx=10)
        def UpdateLaunchLabel(LaunchLabel):
            def update():
                LaunchLabel.config(text="Has Launched: "+str(hasLaunched))
                LaunchLabel.after(100,update)
            update()
        UpdateLaunchLabel(LaunchLabel)

        #mbo label
        MBOLabel=tk.Label(self, text='',font=boringFont,borderwidth=2,relief="sunken")
        MBOLabel["bg"]=bgColor
        MBOLabel.pack(anchor=tk.W,pady=10,padx=10)
        def UpdateMBOLabel(MBOLabel):
            def update():
                MBOLabel.config(text="Motor Burnout: "+str(mbo))
                MBOLabel.after(100,update)
            update()
        UpdateMBOLabel(MBOLabel)

        #apogee label
        apogeeLabel=tk.Label(self, text='',font=boringFont,borderwidth=2,relief="sunken")
        apogeeLabel["bg"]=bgColor
        apogeeLabel.pack(anchor=tk.W,pady=10,padx=10)
        def UpdateApogeeLabel(apogeeLabel):
            def update():
                if not apogeeReached:
                    apogeeLabel.config(text='Apogee Reached: False')
                else:
                    apogeeLabel.config(text='Apogee Reached at '+str(apogeeHeight)+" meters.")
                apogeeLabel.after(100,update)
            update()
        UpdateApogeeLabel(apogeeLabel)
    
        #landing label
        LandingLabel=tk.Label(self, text='',font=boringFont,borderwidth=2,relief="sunken")
        LandingLabel["bg"]=bgColor
        LandingLabel.pack(anchor=tk.W,pady=10,padx=10)
        def UpdateLandingLabel(LandingLabel):
            def update():
                LandingLabel.config(text="Has Landed: "+str(hasLanded))
                LandingLabel.after(100,update)
            update()
        UpdateLandingLabel(LandingLabel)

        #GPS label
        GPSLabel=tk.Label(self, text='',font=boringFont,borderwidth=2,relief="sunken")
        GPSLabel["bg"]=bgColor
        GPSLabel.pack(anchor=tk.W,pady=10,padx=10)
        def UpdateGPSLabel(GPSLabel):
            def update():
                try:
                    GPSLabel.config(text='GPS coordinates: '+str(recentData[-1][GPS_LA])+', '+str(recentData[-1][GPS_LO]))
                except:
                    GPSLabel.config(text='waiting for data...')
                GPSLabel.after(100,update)
            update()
        UpdateGPSLabel(GPSLabel)

        #altitude label
        altitudeLabel=tk.Label(self, text='',font=boringFont,borderwidth=2,relief="sunken")
        altitudeLabel["bg"]=bgColor
        altitudeLabel.pack(anchor=tk.W,pady=10,padx=10)
        def UpdateAltLabel(altitudeLabel):
            def update():
                try:
                    altitudeLabel.config(text='altitude: '+str(recentData[-1][alt])+' meters')
                except:
                    altitudeLabel.config(text='waiting for data...')
                altitudeLabel.after(100,update)
            update()
        UpdateAltLabel(altitudeLabel)
        
        #end program button
        def EndProgram():

            os._exit(1)

        endButton=tk.Button(self,text="End Program",command=EndProgram)
        endButton["highlightbackground"]=bgColor
        endButton.pack(anchor=tk.W,pady=10,padx=10)

try:
    user=sys.argv[1]
except:
    print ('Error: No user given, cannot check serial ports. '+ 
            'Function call should be \"python interpretData.py {user} {file (optional)}\"')
    sys.exit()



ser=None
if user in users.keys() and len(sys.argv)<3:
    for port in users.get(user):
        try:
            ser=serial.Serial(port,9600)
            
        except:
            pass

if ser==None:
    serialPortWorks=False
    try:
        fName=sys.argv[2]
    except:
        print ('Error: No working serial port and no file name in arguments.')
        sys.exit()
    f=open(fName,"r")
        

app=GUI()
app.state('zoomed')




def RunVisuals():
    global x_vals
    global y_vals
    ani = FuncAnimation(plt.gcf(), animate, interval = 50, blit=True)
    app.mainloop()


def main():
    global x_vals
    global y_vals

    lock=threading.Lock()
    def GetData():

        global x_vals
        global y_vals
        with lock:
            while True:
                while (ser.in_waiting < 1):
                    pass
                line = ser.readline().decode('utf-8')[:-1]
                strData = line.split()
                if (len(strData) < 10):
                    continue
                data=[float(i) for i in strData]
                data[Ay]*=-9.81
                x_vals.append(data[t])
                y_vals.append(data[alt])
                AddDataLine(data)


    if serialPortWorks:
        
        #runVisuals = threading.Thread(name='RunVisuals',target=RunVisuals)
        getData = threading.Thread(name='GetData',target=GetData)
        #runVisuals.start()
        getData.start()
        RunVisuals()
    else:
        RunVisuals()



if __name__ == "__main__":
    main()

if not serialPortWorks:
    f.close()
