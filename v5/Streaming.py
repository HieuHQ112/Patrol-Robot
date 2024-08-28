"""
Using the NanoCamera with RTSP Source Cameras
@author: Ayo Ayibiowu

"""

import cv2
import time

src = ('rtspsrc location={} latency={}! queue! '
'rtph265depay ! h265parse ! omxh265dec! '
'nvvidconv ! '
'video/x-raw,format=BGRx ! videoconvert ! video/x-raw,format=BGR ! '
'queue ! appsink drop=1 ').format('rtsp://admin:jetson@192.168.29.32:554/cam/realmonitor?channel=1&subtype=1', 200)

stream = cv2.VideoCapture(src, cv2.CAP_GSTREAMER)

# from nanocamera.NanoCam import Camera
import nanocamera as nano

while True:
    stream = cv2.VideoCapture(src , cv2.CAP_GSTREAMER)

    if not stream.isOpened():
        print(' Source not Available')
        time.sleep(1)
    else: 
        print(' Source connected')
        while true:
            ret, frame= stream.read()
            if not ret:
                print(' Failed to read from stream')
                strea.release()
                break
            else:
                cv2.imshow(' Cam0',frame)
                cv2.waitkey(1)
   
