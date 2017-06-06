import paho.mqtt.client as mqtt
import os, shutil
import logging
import thread
import cv2
import sys
import time
import uuid
import sched
import threading

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)s %(levelname)s - %(message)s')  # include timestamp

class FaceCapture(object):
    """Capture video for the specific door and run face detector algorithms on it"""
    CAPTURE_DURATION = 1.0

    logger = logging.getLogger("face-capture")
    lock = threading.Lock()

    def __init__(self, which):
        self.door = which
        self.duration = self.CAPTURE_DURATION
        self.done = False

    def get_camera(self):
        return 0

    def extend(self):
        with self.lock:
            if self.done:
                return False
            self.logger.info("Extending duration")
            self.duration += self.CAPTURE_DURATION
            return True

    def start(self):
        self.logger.info("Starting video capture for %s door", self.door)
        thread.start_new(self._process_video, ())

    def _process_video(self):
        faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
        video_capture = cv2.VideoCapture(self.get_camera())
        start_time = time.clock()

        self.logger.info("Camera open, proceeding with capture")
        frames = 0
        full_frame_saved = False

        candidate_faces = []

        while True:
            (ret, frame) = video_capture.read()
            #frame = cv2.imread("Y:\\home-vision\\raw\\bug-eyes.jpg")
            if frame is not None:
                frames += 1
                gray = cv2.cvtColor(frame[140:380, 160:340], cv2.COLOR_BGR2GRAY)
                faces = faceCascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(24, 24),
                    maxSize=(64, 64),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )

                if not full_frame_saved and (time.clock() - start_time > 3.0):
                    cv2.imwrite("raw/full-" + door + "-" + str(uuid.uuid1()) + ".jpg", frame)
                    full_frame_saved = True

                for (x, y, w, h) in faces:
                    face = gray[y:y+h, x:x+w]
                    candidate_faces += face

            # Check to see if we are out of time
            with self.lock:
                if (time.clock() - start_time) > self.duration:
                    self.done = True
                    break

        self.logger.info("Video capture complete (%.2f seconds, %d frames)", (time.clock() - start_time), frames)

        if len(candidate_faces) > 0:
            self.logger.info("Processing faces...")
            for face in candidate_faces:
                cv2.imwrite("raw/" + door + str(uuid.uuid1()) + ".jpg", face)
        video_capture.release()

class ArrivalProcesor(object):
    """Process events captured from the home automation gateway"""

    logger = logging.getLogger("arrival-processor")
    running_captures = {}

    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def connect_and_run_forever(self):
        # Connect to the MQTT server running on another Raspberry Pi
        self.client.connect("io-pi", 1883, 60)
        self.client.loop_forever()

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        self.logger.info("mqtt connected: %d", rc)
        self.client.subscribe("presence/#")
        self.client.subscribe("door/#")

    def handle_door(self, which, payload):
        self.logger.info("Processing door")
        if int(payload) == 100:
            capture = self.running_captures[which] if which in self.running_captures else None
            if capture is None or capture.done or not capture.extend():
                self.logger.info("Starting capture for %s", which)
                capture = FaceCapture(which)
                self.running_captures[which] = capture
                capture.start()

    def handle_presence(self, which, payload):
        presences = {
            0: "away",
            100: "home"
        }
        presence = presences[int(payload)]
        self.logger.info("Processing presence for %s - %s", which, presence)
        if presence == "home":
            self.logger.debug("Processing images recently taken")
        #    files = os.listdir("raw")
        #    try:
        #      os.mkdir(which)
        #    except OSError as exc:
        #      pass
        #
        #    for f in files:
        #      print("Moving " + str(f) + " to " + which.lower())
        #      shutil.move("raw/" + f, which + "/" + f)

    def on_message(self, client, userdata, msg):
        subject = msg.topic.split('/')[0]
        allsub = {
            "door": self.handle_door,
            "presence": self.handle_presence
        }
        allsub[subject](msg.topic.split('/')[1], msg.payload)


ArrivalProcesor().connect_and_run_forever()
