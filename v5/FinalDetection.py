import cv2
import torch
import os
import subprocess
import smtplib
import email.utils
import threading
import time
from datetime import datetime
import queue
import Jetson.GPIO as GPIO
from jetbot import Robot
from playsound import playsound
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage

# Constants
SENDER_EMAIL = "qhtn520@gmail.com"
SENDER_PASSWORD = "nzelyfpmdygfhwqk"
RECEIVER_EMAILS = ["19520544@gm.uit.edu.vn"]
MODEL_PATH = 'v5n.pt'
ALERT_SOUND_PATH = 'beep.mp3'

# Global variables
stop_threads = False
robot_moving = False
detection_count = 0
led_pin = 7
# GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(led_pin, GPIO.OUT, initial=GPIO.LOW)

def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1280,
    capture_height=720,
    display_width=640,
    display_height=320,
    framerate=30,
    flip_method=0,
):
    return (
        f"nvarguscamerasrc sensor-id={sensor_id} ! "
        f"video/x-raw(memory:NVMM), width=(int){capture_width}, height=(int){capture_height}, "
        f"framerate=(fraction){framerate}/1 ! "
        f"nvvidconv flip-method={flip_method} ! "
        f"video/x-raw, width=(int){display_width}, height=(int){display_height}, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
    )

# Model
model = torch.hub.load('../v5', 'custom', path='v5n.pt', source='local', force_reload=True)

# Robot
robot = Robot()

# Set up the GPIO channel
led_pin = 7
GPIO.setmode(GPIO.BCM)
GPIO.setup(led_pin, GPIO.OUT, initial=GPIO.LOW)

# Camera setup
cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)

# Directory to the videos
VIDEO_SAVE_DIR = '/home/jetson/jetbot-0.4.3/Detect'
if not os.path.exists(VIDEO_SAVE_DIR):
    os.makedirs(VIDEO_SAVE_DIR)

# Get video properties
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))

# Define the codec and create VideoWriter object
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_filename = f'output_video_{timestamp}.avi'
output_path = os.path.join(VIDEO_SAVE_DIR, output_filename)
out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'XVID'), fps, (width, height))

# Email setup
sender_email = "qhtn520@gmail.com"
sender_password = "nzelyfpmdygfhwqk"
receiver_emails = ["19520544@gm.uit.edu.vn"]

server = smtplib.SMTP_SSL('smtp.googlemail.com', 465)
server.login(sender_email, sender_password)

# Model settings
model.conf = 0.47
model.iou = 0.45
model.classes = None

# Global variables
flag = 0
stop_threads = False

def alert():
    playsound('beep.mp3')
    #time.sleep(2)
    GPIO.output(led_pin, GPIO.HIGH)

def upload_video_to_firebase():
    cred = credentials.Certificate("jetson.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'jetson-a48a6.appspot.com'
    })
    
    bucket = storage.bucket()
    
    firebase_filename = output_filename

    blob = bucket.blob(firebase_filename)
    blob.upload_from_filename('output_video.avi')
    print("Video uploaded to Firebase Storage")

def send_mail(sender_email, receiver_emails):
    for receiver_email in receiver_emails:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Alert"
        msg['From'] = sender_email
        msg['To'] = receiver_email
        html = "HUMAN DETECTED"
        msg.attach(MIMEText(html, 'html'))
        server.sendmail(sender_email, receiver_email, msg.as_string())
    print('Email sent!')

def movement_thread():
    global stop_threads
    while not stop_threads:
        for i in range(12, -1, -1):
            robot.forward(speed=0.2)
            time.sleep(1)
        for i in range(1, 0, -1):
            robot.left(speed=0.136)
            time.sleep(1)
    robot.stop()

def detection_thread():
    global flag, stop_threads
    while not stop_threads:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        rendered_frame = results.render()[0]

        out.write(rendered_frame)
        cv2.imshow('YOLOv5 Inference', rendered_frame)

        person_detections = results.pandas().xyxy[0]
        num_people = len(person_detections[person_detections['class'] == 0])
        
        if num_people > 0:
            flag += 1
            print('Alert')
            threading.Thread(target=alert).start()
            #time.sleep(2)
            #GPIO.output(led_pin, GPIO.HIGH)
        #else:
            #time.sleep(2)
            #GPIO.output(led_pin, GPIO.LOW)
            #flag = 0
        print(f'Number of people: {num_people}')
        print(f'Flag: {flag}')

        if flag == 5:
            threading.Thread(target=send_mail, args=(sender_email, receiver_emails)).start()
            #flag = 0  # Reset flag after sending email

        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_threads = True
            break

# Main execution
if __name__ == "__main__":
    # Start the movement thread
    move_thread = threading.Thread(target=movement_thread)
    move_thread.start()

    # Start the detection thread
    detect_thread = threading.Thread(target=detection_thread)
    detect_thread.start()

    try:
        # Wait for threads to complete
        move_thread.join()
        detect_thread.join()
    except KeyboardInterrupt:
        print("Stopping threads...")
        stop_threads = True
    finally:
        # Clean up
        upload_video_to_firebase()
        cap.release()
        out.release()
        cv2.destroyAllWindows()
        GPIO.cleanup()
        server.quit()




