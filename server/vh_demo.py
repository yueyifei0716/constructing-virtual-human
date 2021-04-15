import multiprocessing
import cv2
import sys
import os
import time
import socket
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow import keras
from multiprocessing import Process, Value
from face_recognition import face_locations, face_encodings, \
    compare_faces, face_distance
from face_reco.facial_preprocess import load_faces, encode_faces
from pydub import AudioSegment
from pydub.playback import play
from speech_reco.speech_v2 import speech_recognition

# Default Settings
IMG_SHAPE = (180, 180)
hand_gesture_names = ['nothing', 'paper', 'rock', 'scissors']   # hand gesture class
body_gesture_names = ['hello', 'nothing', 'start']              # body gesture class
hand_gesture_model = load_model("/Users/yueyifei/PycharmProjects/virtual_human/models/brief_rps_v2.h5")       # hand gesture classifier
body_gesture_model = load_model("/Users/yueyifei/Desktop/collect/models/brief_body_v2.h5")      # body gesture classifier
path = 'resources/audios/output.wav'  # speech record
fs = 44100  # sample rate
seconds = 4  # duration of recording
FPS = 12  # frame per second
video_capture = cv2.VideoCapture(1)
face_capture = cv2.VideoCapture(1)
body_capture = cv2.VideoCapture(1)
countdown_audio = AudioSegment.from_wav("resources/audios/count_down.wav")  # game count down audio
face_classifier = cv2.CascadeClassifier("resources/files/face_classifier.xml")  # face classifier


def body_reco(user_dict, message_dict, is_face_reco):
    while True:
        while user_dict["is_gaming"] == "N" and user_dict["is_reachable"] == "Y" and is_face_reco.value == 0:
            body_dict = {"hello": 0, "start": 0, "nothing": 0}
            for i in range(20):
                # grab a single frame of video
                ret, frame = body_capture.read()
                cv2.imwrite('body.png', frame)
                img = keras.preprocessing.image.load_img(
                    'body.png', target_size=IMG_SHAPE
                )
                # preprocess the frame
                img_array = keras.preprocessing.image.img_to_array(img)
                img_array = tf.expand_dims(img_array, 0)

                # predict the body gesture by using the classifier
                predictions = body_gesture_model.predict(img_array)
                score = tf.nn.softmax(predictions[0])
                user_body_name = body_gesture_names[np.argmax(score)]
                body_dict[user_body_name] = body_dict[user_body_name] + 1
                print(body_dict)

            best_name = max(body_dict, key=body_dict.get)
            print(best_name)
            # if 80% of results is hello, then the VH wave back
            if best_name == 'hello':
                is_face_reco.value = 1
                while True:
                    if user_dict["name"]:
                        name = user_dict["name"]
                        if name == "Unknown":
                            message_dict[0] = "conv.hello"
                        elif name == "yifeiyue":
                            message_dict[0] = "conv.yifeiyue"
                        elif name == "kangmingfeng":
                            message_dict[0] = "conv.kangmingfeng"
                        elif name == "wangkaijin":
                            message_dict[0] = "conv.wangkaijin"
                        elif name == "jingwang":
                            message_dict[0] = "conv.jingwang"
                        elif name == "xueli":
                            message_dict[0] = "conv.xueli"
                        elif name == "zhanpengwang":
                            message_dict[0] = "conv.zhanpengwang"
                        break
            # if 80% of results is start, then start the game
            elif best_name == 'start':
                user_dict["is_gaming"] = "Y"
                message_dict[0] = "game.gameStart"
            else:
                pass


def is_detected(user_dict, message_dict):
    false_times = 0
    while True:
        while user_dict["is_gaming"] == "N":
            detect_count = 0
            for i in range(FPS):
                # read the image
                ret, frame = face_capture.read()
                # preprocess the frame
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_classifier.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=3, minSize=(32, 32))
                # if len(faces) > 0, then face is detected
                if len(faces) > 0:
                    detect_count = detect_count + 1
            # if face can be detected from 80% of the frames in 1 second, then the person is reachable
            if detect_count > FPS * 0.8:
                false_times = 0
                user_dict["is_reachable"] = "Y"
            else:
                false_times = false_times + 1
                user_dict["is_reachable"] = "N"
                # if face can not be detected for 5 seconds, say sorry I can not see you
                if false_times == 5 and user_dict["name"] != "":
                    message_dict[0] = "conv.cantsee"
                # if face can not be detected for 15 seconds, say goodbye and clear the person dictionary
                if false_times == 15 and user_dict["name"] != "":
                    false_times = 0
                    message_dict[0] = "conv.goodday"
                    user_dict["name"] = ""
                    user_dict["is_reachable"] = "N"
                    user_dict["action"] = ""
                    user_dict["keyword"] = ""
                    user_dict["is_gaming"] = "N"


def face_reco(user_dict, is_face_reco):
    # load sample pictures and learn how to recognize it
    images_dict = load_faces("resources/images")
    # create a dictionary of known face encodings and their names
    known_faces_dict = encode_faces(images_dict)
    while True:
        # counting dictionary
        while is_face_reco.value == 1:
            frame_count = 0
            name_dict = {"yifeiyue": 0, "jingwang": 0, "xueli": 0, "kangmingfeng": 0, "zhanpengwang": 0, "wangkaijin": 0, "Unknown": 0}
            # find faces that have appeared for 2 seconds
            while frame_count < 2 * FPS:
                print(1)
                # read the image
                ret, frame = video_capture.read()
                frame_count += 1
                # initialize some variable
                face_names = []
                # resize frame of video to 1/4 size for faster face recognition processing
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                # convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
                rgb_small_frame = small_frame[:, :, ::-1]
                # find all the faces and face encodings in the current frame of video
                locations = face_locations(rgb_small_frame)
                encodings = face_encodings(rgb_small_frame, locations)
                for encoding in encodings:
                    # see if the face is a match for the known face(s)
                    matches = compare_faces(list(known_faces_dict.values()), encoding, tolerance=0.45)
                    name = "Unknown"
                    # or instead, use the known face with the smallest distance to the new face
                    face_distances = face_distance(list(known_faces_dict.values()), encoding)
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = list(known_faces_dict)[best_match_index]
                    face_names.append(name)
                if face_names:
                    for name in face_names:
                        name_dict[name] = name_dict[name] + 1
                        print(name_dict)
            best_name = max(name_dict, key=name_dict.get)
            print(best_name)
            user_dict["name"] = best_name
            is_face_reco.value = 0


def rps_mode(message_dict, user_dict):
    while True:
        index = 0
        while user_dict["is_gaming"] == "Y":
            gesture_dict = {"paper": 0, "scissors": 0, "rock": 0, "nothing": 0}
            if index == 0:
                time.sleep(3)
            message_dict[index] = 'game.countDown'
            time.sleep(3.5)
            message_dict[index] = 'game.chooseGesture'
            time.sleep(1)
            for i in range(FPS):
                # grab a single frame of video
                ret, frame = video_capture.read()
                cv2.imwrite('rps.png', frame)
                img = keras.preprocessing.image.load_img(
                    'rps.png', target_size=IMG_SHAPE
                )
                img_array = keras.preprocessing.image.img_to_array(img)
                img_array = tf.expand_dims(img_array, 0)
                # predict the gesture by using the classifier
                predictions = hand_gesture_model.predict(img_array)
                score = tf.nn.softmax(predictions[0])
                user_move_name = hand_gesture_names[np.argmax(score)]
                gesture_dict[user_move_name] = gesture_dict[user_move_name] + 1
                print(gesture_dict)
            best_gesture = max(gesture_dict, key=gesture_dict.get)

            # send the detected gesture to client
            message_dict[index] = 'game.' + best_gesture
            print(message_dict)

            # three rounds of the game
            index += 1
            if index == 3:
                user_dict["is_gaming"] = "N"
                message_dict[index] = "game.gameEnd"
                index = 0
            time.sleep(3)


# def speech_reco(user_dict, message_dict, is_face_reco):
#     con_id = 0
#     while True:
#         if user_dict["is_gaming"] == "N" and user_dict["is_reachable"] == "Y":
#             print("waiting for user input..")
#             # get user input message by analyzing the collected sounds
#             user_input = speech_recognition()
#             # extract the keyword from the input message
#             user_dict["keyword"] = user_input
#             # save the keyword to the message dictionary
#             if user_dict["keyword"] == 'hello' and user_dict["is_reachable"] == "Y":
#                 is_face_reco.value = 1
#                 while True:
#                     if user_dict["name"]:
#                         name = user_dict["name"]
#                         if name == "Unknown":
#                             message_dict[con_id] = "conv.hello"
#                         elif name == "yifeiyue":
#                             message_dict[con_id] = "conv.yifeiyue"
#                         elif name == "kangmingfeng":
#                             message_dict[con_id] = "conv.kangmingfeng"
#                         elif name == "wangkaijin":
#                             message_dict[con_id] = "conv.wangkaijin"
#                         elif name == "jingwang":
#                             message_dict[con_id] = "conv.jingwang"
#                         elif name == "xueli":
#                             message_dict[con_id] = "conv.xueli"
#                         elif name == "zhanpengwang":
#                             message_dict[con_id] = "conv.zhanpengwang"
#                         break
#             elif user_dict["keyword"] == 'game' and user_dict["is_reachable"] == "Y":
#                 user_dict["is_gaming"] = "Y"
#                 message_dict[con_id] = "game.gameStart"
#             elif user_dict["keyword"] == 'name' and user_dict["is_reachable"] == "Y":
#                 message_dict[con_id] = "conv.name"
#             elif user_dict["keyword"] == 'bye' and user_dict["is_reachable"] == "Y":
#                 message_dict[con_id] = "conv.goodbye"
#             elif user_dict["keyword"] == 'nothing' and user_dict["is_reachable"] == "Y":
#                 message_dict[con_id] = "conv.cannot"
#             else:
#                 pass
#             con_id += 1

def speech_reco(fileno, user_dict, message_dict, is_face_reco):
    con_id = 0
    sys.stdin = os.fdopen(fileno)
    while True:
        if user_dict["is_gaming"] == "N" and user_dict["is_reachable"] == "Y":
            print("waiting for user input..")
            # get user input message by analyzing the collected sounds
            user_input = speech_recognition(path)
            # user_input = input()
            # extract the keyword from the input message
            user_dict["keyword"] = user_input
            # save the keyword to the message dictionary
            if user_dict["keyword"] == 'hello' and user_dict["is_reachable"] == "Y":
                is_face_reco.value = 1
                while True:
                    if user_dict["name"]:
                        name = user_dict["name"]
                        if name == "Unknown":
                            message_dict[con_id] = "conv.hello"
                        elif name == "yifeiyue":
                            message_dict[con_id] = "conv.yifeiyue"
                        elif name == "kangmingfeng":
                            message_dict[con_id] = "conv.kangmingfeng"
                        elif name == "wangkaijin":
                            message_dict[con_id] = "conv.wangkaijin"
                        elif name == "jingwang":
                            message_dict[con_id] = "conv.jingwang"
                        elif name == "xueli":
                            message_dict[con_id] = "conv.xueli"
                        elif name == "zhanpengwang":
                            message_dict[con_id] = "conv.zhanpengwang"
                        break
            elif user_dict["keyword"] == 'game' and user_dict["is_reachable"] == "Y":
                user_dict["is_gaming"] = "Y"
                message_dict[con_id] = "game.gameStart"
            elif user_dict["keyword"] == 'name' and user_dict["is_reachable"] == "Y":
                message_dict[con_id] = "conv.name"
            elif user_dict["keyword"] == 'bye' and user_dict["is_reachable"] == "Y":
                message_dict[con_id] = "conv.goodbye"
            elif user_dict["keyword"] == 'nothing' and user_dict["is_reachable"] == "Y":
                message_dict[con_id] = "conv.cannot"
            else:
                pass
            con_id += 1


def start_server(message_dict):
    """local IP address"""
    address = ('127.0.0.1', 31500)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(address)
    s.listen(5)
    ss, addr = s.accept()
    print('got connected from', addr)
    while True:
        '''
            message sent to trigger animation
        '''
        if message_dict:
            # send message and also clear the storage unit
            msg = list(message_dict.values())[0]
            message_dict.pop(list(message_dict.keys())[0])
            ss.send(msg.encode('utf-8'))


if __name__ == '__main__':
    # managers provide a way to create data which can be shared between different processe
    # initialize a manager object
    fn = sys.stdin.fileno()
    manager = multiprocessing.Manager()

    # if the face has been recognized
    face_reco_status = Value('b', 0)

    # a shared dict object passing message to client
    message_unit = manager.dict()
    # a shared dict object storing attributes of a person
    user_unit = manager.dict()
    # five different attributes of a person
    user_unit["name"] = ""
    user_unit["is_reachable"] = "N"
    user_unit["action"] = ""
    user_unit["keyword"] = ""
    user_unit["is_gaming"] = "N"

    # create processes
    process_person_reco = Process(target=is_detected, args=(user_unit, message_unit))
    process_server = Process(target=start_server, args=(message_unit,))
    process_face_reco = Process(target=face_reco, args=(user_unit, face_reco_status))
    # process_speech_reco = Process(target=speech_reco, args=(fn, user_unit, message_unit, face_reco_status))
    process_rps = Process(target=rps_mode, args=(message_unit, user_unit))
    process_body_reco = Process(target=body_reco, args=(user_unit, message_unit, face_reco_status))

    # start processes
    process_person_reco.start()
    # process_speech_reco.start()
    process_server.start()
    process_face_reco.start()
    process_rps.start()
    process_body_reco.start()

    # wait for the worker processes to exit
    process_person_reco.join()
    # process_speech_reco.join()
    process_server.join()
    process_face_reco.join()
    process_rps.join()
    process_body_reco.join()
