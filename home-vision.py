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
import numpy

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)s %(levelname)s - %(message)s')

class FaceCapture(object):
    """Capture video for the specific door and run face detector and identifier algorithms on it"""
    CAPTURE_DURATION = 6.0

    logger = logging.getLogger("face-capture")
    lock = threading.Lock()

    def __init__(self, which, processor):
        self.door = which
        self.duration = self.CAPTURE_DURATION
        self.done = False
        self.processor = processor

    def get_camera(self):
        return 0

    def get_camera_inset(self):
        insets = {
            "kitchen": ((20, 300), (160, 340))
        }
        return insets[self.door]

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
        #faceCascade = cv2.CascadeClassifier("haarcascade_eye_tree_eyeglasses.xml")
        faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_alt.xml")
        video_capture = cv2.VideoCapture(self.get_camera())
        start_time = time.clock()

        self.logger.info("Camera open, proceeding with capture")
        frames = 0
        full_frame_saved = False

        candidate_faces = []

        ((y1, y2), (x1, x2)) = self.get_camera_inset()

        while True:
            (ret, frame) = video_capture.read()
            #frame = cv2.imread("raw2.jpg")
            if frame is not None:
                frames += 1

                gray = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
                #cv2.imshow("Test", gray)

                #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = faceCascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=8,
                    minSize=(20, 20),
                    flags=cv2.CASCADE_DO_CANNY_PRUNING
                )

                # Save off a sample full image that occurs at least after 3 seconds
                # if not full_frame_saved and (time.clock() - start_time > 3.0):
                #     cv2.imwrite("raw/full-" + self.door + "-" + str(uuid.uuid1()) + ".jpg", frame)
                #     full_frame_saved = True

                for (x, y, w, h) in faces:
                    face = gray[y:y+h, x:x+w]
                    candidate_faces.append(face)

            # Check to see if we are out of time
            with self.lock:
                if (time.clock() - start_time) > self.duration:
                    self.done = True
                    break

        self.logger.info("Video capture complete (%.2f seconds, %d frames)", (time.clock() - start_time), frames)

        if len(candidate_faces) > 0:
            self.logger.debug("Processing faces...")
            total_kept = 0

            total_identities = {}
            for face in candidate_faces:
                identity, confidence = self.processor.identify(self.door, face)

                if not identity in total_identities: total_identities[identity] = 0
                total_identities[identity] += 1

                img_id = str(uuid.uuid1())
                self.logger.debug("Identified %s for image id %s", identity, img_id)
                cv2.imwrite("raw/" + self.door + "-" + img_id + ".jpg", face)
                total_kept += 1

            self.logger.debug("Done (total faces = %d)", total_kept)

            user = max(total_identities, key=total_identities.get)
            self.logger.info("User identified: " + user)
        else:
            self.logger.info("No user identified this time")
        video_capture.release()

class FaceProcessor(object):
    """Train a face recognizer periodically and supply the ability to identify faces"""
    logger = logging.getLogger("face-processor")

    recognizers = {}
    dimensions = {}
    labels = {}

    def __init__(self):
       self.schedule_timer()

    def schedule_timer(self):
        self.face_processor = threading.Timer(24 * 60 * 60, self.process)
        self.face_processor.start()

    def identify(self, room, image):
        self.logger.debug("Identifying image in room %s", room)
        #gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        resized_image = cv2.resize(image, self.dimensions[room])

        id, conf = self.recognizers[room].predict(resized_image)
        return self.labels[id], conf

    def process(self):
        self.logger.info("Training face recognizer...")
        users = os.listdir("users")

        self.identifiers = {}

        images = {}
        user_idx = 0
        for user in users:
            for room in os.listdir("users/" + user):
                self.logger.info("Processing room %s user %s", room, user)

                #identifiers[room] = recognizer
                for image in self._get_images(user, room):
                    if not room in images: images[room] = []
                    images[room].append((image, user_idx))

            self.labels[user_idx] = user
            user_idx += 1

        for room in images:
            self.logger.info("Training for room %s", room)
            #recognizer = cv2.createLBPHFaceRecognizer()
            recognizer = cv2.createFisherFaceRecognizer()

            room_images = map(lambda x:x[0], images[room])
            largest_image = max(room_images, key = lambda x: x.size)

            # Resize all of the images to the size of the largest library image
            resized_room_images = map(lambda x: cv2.resize(x, largest_image.shape[:2]), room_images)

            self.logger.info("Images: %d", len(resized_room_images))

            # Train the face recognizer and provide the labels
            recognizer.train(resized_room_images, numpy.array(map(lambda x:x[1], images[room])))

            self.dimensions[room] = largest_image.shape[:2]
            self.recognizers[room] = recognizer

        self.logger.info("Done")
        self.schedule_timer()
        return 0


    def _get_images(self, user, room):
        dir = "users/" + user + "/" + room
        for image in os.listdir(dir):
            if ".jpg" in image:
                yield cv2.imread(dir + "/" + image, cv2.IMREAD_GRAYSCALE)


class ArrivalProcesor(object):
    """Process events captured from the home automation gateway"""

    logger = logging.getLogger("arrival-processor")
    running_captures = {}

    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.processor = FaceProcessor()
        self.processor.process()

    def connect_and_run_forever(self):
        # Connect to the MQTT server running on another Raspberry Pi
        self.client.connect("io-pi", 1883, 60)
        self.client.loop_forever()

    def on_connect(self, client, userdata, flags, rc):
        self.logger.info("mqtt connected: %d", rc)
        self.client.subscribe("presence/#")
        self.client.subscribe("door/#")

    def handle_door(self, which, payload):
        self.logger.info("Processing door (%s)", payload)
        if int(payload) == 100:
            capture = self.running_captures[which] if which in self.running_captures else None
            if capture is None or capture.done or not capture.extend():
                self.logger.info("Starting capture for %s", which)
                capture = FaceCapture(which, self.processor)
                self.running_captures[which] = capture
                capture.start()

    def handle_presence(self, which, payload):
        presences = {
            0: "away",
            100: "home"
        }
        presence = presences[int(payload)]
        self.logger.info("Processing presence for %s - %s", which, presence)

        # When a user is detect home, move all the latest raw images to their user folder
        if presence == "home":
            self.logger.debug("Processing images recently taken")
            files = os.listdir("raw")

            for f in files:
                room = f.split("-")[0]
                dir = "users/" + which + "/" + room
                try:
                    os.mkdir(dir)
                except OSError as exc:
                    pass
                print("Moving " + str(f) + " to " + dir)
                shutil.move("raw/" + f, dir)

    def on_message(self, client, userdata, msg):
        subject = msg.topic.split('/')[0]
        allsub = {
            "door": self.handle_door,
            "presence": self.handle_presence
        }
        allsub[subject](msg.topic.split('/')[1], msg.payload)


#result = processor.identify("kitchen", cv2.imread("users/spencer/kitchen/kitchen1a6cb72e-4b14-11e7-b485-b827eb09c8e1.jpg"))
#result = processor.identify("kitchen", cv2.imread("users/stacy/kitchen/kitchen6ae957ec-4b1f-11e7-a2b7-b827eb09c8e1.jpg"))
#print("Result = " + str(result))

ArrivalProcesor().connect_and_run_forever()
