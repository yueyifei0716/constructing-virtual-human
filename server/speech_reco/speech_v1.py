import json
import re
import sounddevice as sd
from speech_reco.common import credential
from speech_reco.asr import flash_recognizer
from scipy.io.wavfile import write

fs = 48000  # Sample rate
seconds = 4  # Duration of recording
reg = "[^0-9A-Za-z\u4e00-\u9fa5]"

APPID = "1305223688"
SECRET_ID = "AKIDqSomV0bAqHSM2UqalfKNCm8C3ovnHc9Q"
SECRET_KEY = "KVQzIhpWcWBxU2NTIzUl2KbjiWB0c7S1"
ENGINE_TYPE = "16k_zh"


def speech_recognition(audio_path):
    recorder = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
    sd.wait()  # Wait until recording is finished
    write(audio_path, fs, recorder)  #

    if APPID == "":
        print("Please set APPID!")
        exit(0)
    if SECRET_ID == "":
        print("Please set APPID!")
        exit(0)
    if SECRET_KEY == "":
        print("Please set SECRET_KEY!")
        exit(0)

    credential_var = credential.Credential(SECRET_ID, SECRET_KEY)
    # Create a new FlashRecognizer where a Recognizer can perform N recognition requests
    recognizer = flash_recognizer.FlashRecognizer(APPID, credential_var)
    # New Identification Request
    req = flash_recognizer.FlashRecognitionRequest(ENGINE_TYPE)
    req.set_filter_modal(0)
    req.set_filter_punc(0)
    req.set_filter_dirty(0)
    req.set_voice_format("wav")
    req.set_word_info(0)
    req.set_convert_num_mode(1)

    with open(audio_path, 'rb') as f:
        # Read audio data
        data = f.read()
        # Perform identification
        result_data = recognizer.recognize(req, data)
        resp = json.loads(result_data)
        request_id = resp["request_id"]
        code = resp["code"]
        if code != 0:
            print("Recognize failed! request_id: ", request_id, " code: ", code, ", message: ", resp["message"])
            exit(0)

        print("request_id: ", request_id)
        # A channel_result corresponds to the recognition result of a sound channel
        # Most of the audio is mono, corresponding to a channel_result
        for channel_result in resp["flash_result"]:
            print("channel_id: ", channel_result["channel_id"])
            print(channel_result["text"])

        sentence = re.sub(reg, ' ', channel_result["text"]).split()

        hello = ['Hello', 'hello', 'Hi', 'hi', '哈喽', '哈咯', '哈喽哈喽', '嗨']
        game = ['Game', 'game', 'Games', 'games']
        bye = ['Goodbye', 'goodbye', 'Bye', 'bye', '拜拜', 'see', 'See']
        name = ['Name', 'name']
        nothing = ['嗯嗯', '啊啊']

        get_hello = [True for keyword in sentence if keyword in hello]
        get_game = [True for keyword in sentence if keyword in game]
        get_bye = [True for keyword in sentence if keyword in bye]
        get_name = [True for keyword in sentence if keyword in name]
        get_nothing = [True for keyword in sentence if keyword in nothing]

        if get_hello:
            return "hello"
        elif get_game:
            return "game"
        elif get_bye:
            return "bye"
        elif get_name:
            return "name"
        elif get_nothing:
            return "nothing"
        else:
            return ""
