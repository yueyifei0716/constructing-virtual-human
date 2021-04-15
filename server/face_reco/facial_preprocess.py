import os
import face_recognition


def load_faces(img_path):
    # face_images = []
    images = []
    names = []
    files = os.listdir(img_path)
    for file in files:
        images.append(face_recognition.load_image_file(img_path + '/' + file))
        names.append(file[:-4])
    image_dict = dict(zip(names, images))
    return image_dict


def encode_faces(image_dict):
    for key in image_dict:
        image_dict[key] = face_recognition.face_encodings(image_dict[key])[0]
    return image_dict
