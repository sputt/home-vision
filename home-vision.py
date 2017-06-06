import paho.mqtt.client as mqtt
import os, shutil
import logging
import thread
import cv2
import sys
import time
import uuid
import sched;

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)s %(levelname)s - %(message)s')  # include timestamp

class FaceCapture(object):
    """Capture video for the specific door and run face detector algorithms on it"""

    logger = logging.getLogger("face-capture")

    def identify_camera(self, which):
        return 0

    def run(self, which):
        # Start OpenCV camera
        self.logger.info("Starting video capture for %s door", which)

        faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
        video_capture = cv2.VideoCapture(self.identify_camera(which))
        start_time = time.clock()

        self.logger.info("Camera open, proceeding with capture")
        frames = 0
        full_frame_saved = False

        candidate_faces = []

        while (time.clock() - start_time) < 12.0:
            (ret, frame) = video_capture.read()
            if frame is not None:
                frames += 1
                gray = cv2.cvtColor(frame[140:380, 160:340], cv2.COLOR_BGR2GRAY)
                faces = faceCascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(24, 24),
                    maxSize=(64, 64),
                    flags=cv2.cv.CV_HAAR_SCALE_IMAGE
                )

                if not full_frame_saved and (time.clock() - start_time > 3.0):
                    cv2.imwrite("raw/full-" + str(uuid.uuid1()) + ".jpg", frame)
                    full_frame_saved = True

                for (x, y, w, h) in faces:
                    face = gray[y:y+h, x:x+w]
                    candidate_faces += face;

        self.logger.info("Video capture complete (%.2f seconds, %d frames)", (time.clock() - start_time), frames)

        if len(candidate_faces) > 0:
            self.logger.info("Processing faces...")
            for face in candidate_faces:
                cv2.imwrite("raw/" + str(uuid.uuid1()) + ".jpg", face)
        video_capture.release()

class ArrivalProcesor(object):
    """Process events captured from the home automation gateway"""

    logger = logging.getLogger("arrival-processor")

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

        thread.start_new(FaceCapture().run, (which,))

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
