import datetime as dt
from time import sleep
import os

# video length in seconds
vid_length = 10
t_vidl = vid_length * 1000

# resolution & framerate
height = 1280
width = 720
fps = 60

# file location
save_name = "/"

while True:
    filename = dt.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
    completed_video_name =os.path.join(save_name, filename + ".h264")

    print("video is recording")
    record_cmd = 'sudo raspivid -n -rot 0 -w 1280 -h 720 -fps %d -t %d -o ' % (fps,t_vidl) + completed_video_name
    cmd1 = os.popen(record_cmd)
    sleep(vid_length)
    print("video is converting")
    convert_cmd = 'sudo MP4Box -add ' + filename + '.h264 -fps %d ' % (fps) + filename + '.mp4'
    cmd2 = os.popen(convert_cmd)
    sleep(0.5)
    print("erasing h264")
    remove_cmd = 'sudo rm ' + filename + '.h264'
    cmd3 = os.popen(remove_cmd)
    print("resetting")
    
    
