from tensorflow.keras.models import load_model
from tensorflow import keras
import tensorflow as tf
import cv2
import numpy as np

class_names = ['nothing', 'paper', 'rock', 'scissors']
IMG_SHAPE = (180, 180)
model = load_model("../models/rps_v2.h5")

if __name__ == '__main__':

    # open the camera
    video_capture = cv2.VideoCapture(1)

    while True:

        # grab a single frame of video
        ret, frame = video_capture.read()

        # rectangle for user to play
        cv2.rectangle(frame, (200, 200), (500, 500), (255, 255, 255), 2)

        # extract the region of image within the user rectangle
        roi = frame[200:500, 200:500]
        # images = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
        img = cv2.resize(roi, IMG_SHAPE)
        img_array = keras.preprocessing.image.img_to_array(img)
        img_array = tf.expand_dims(img_array, 0)
        predictions = model.predict(img_array)
        score = tf.nn.softmax(predictions[0])
        user_move_name = class_names[np.argmax(score)]

        # images = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
        # images = cv2.resize(images, IMG_SHAPE)

        # display the information
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, "Your Move: " + user_move_name,
                    (50, 50), font, 1.2, (255, 255, 255), 1)

        cv2.imshow("Rock Paper Scissors", frame)

        # hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
