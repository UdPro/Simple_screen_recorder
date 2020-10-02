from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtCore import pyqtSlot
import cv2
import numpy as np
import pyautogui
import time
import threading
import argparse
import tempfile
import queue
import subprocess
import sys
import sounddevice as sd
import soundfile as sf
import os
import numpy as np
import pyautogui
import time
import threading

status = True

class videoRecoder():

    def __init__(self):

        self.screen_size = (1920,1080)
        self.fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self.fr = 0
        self.array_frame = []
        self.start = None
        self.finish = None
        self.out = None
        self.rate = 0

    def record_video(self):
        self.start = time.perf_counter()
        while status:
            img = pyautogui.screenshot()
            self.fr += 1
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.array_frame.append(frame)
        self.finish = time.perf_counter()
        self.rate = round(self.fr/(self.finish - self.start))
        print('makeing video')
        self.out = cv2.VideoWriter("temp_video.avi", self.fourcc, self.rate, self.screen_size)
        for frame in self.array_frame:
            self.out.write(frame)
        cv2.destroyAllWindows()
        self.out.release()


    def rec(self):
        print('stating thread')
        self.video_thread = threading.Thread(target=self.record_video)
        self.video_thread.start()

class Record_audio():


    def record_audio(self):
        def callback(indata, frames, time, stat):
            """This is called (from a separate thread) for each audio block."""
            if stat:
                print(stat, file=sys.stderr)
            q.put(indata.copy())

        def int_or_str(text):
            """Helper function for argument parsing."""
            try:
                return int(text)
            except ValueError:
                return text
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('-l', '--list-devices', action='store_true', help='show list of audio devices and exit')
        args, remaining = parser.parse_known_args()
        if args.list_devices:
            print(sd.query_devices())
            parser.exit(0)
        parser = argparse.ArgumentParser( description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter, parents=[parser])
        parser.add_argument('filename', nargs='?', metavar='FILENAME', help='audio file to store recording to')
        parser.add_argument('-d', '--device', type=int_or_str, help='input device (numeric ID or substring)')
        parser.add_argument('-r', '--samplerate', type=int, help='sampling rate')
        parser.add_argument('-c', '--channels', type=int, default=1, help='number of input channels')
        parser.add_argument('-t', '--subtype', type=str, help='sound file subtype (e.g. "PCM_24")')
        args = parser.parse_args(remaining)

        q = queue.Queue()

        try:
            if args.samplerate is None:
                device_info = sd.query_devices(args.device, 'input')
                # soundfile expects an int, sounddevice provides a float:
                args.samplerate = int(device_info['default_samplerate'])
            args.filename = 'temp_audio.wav'
            if args.filename is None:
                args.filename = tempfile.mktemp(prefix='temp_audio', suffix='.wav', dir='')

            # Make sure the file is opened before recording anything:
            with sf.SoundFile(args.filename, mode='x', samplerate=args.samplerate,channels=args.channels, subtype=args.subtype) as file:
                with sd.InputStream(samplerate=args.samplerate, device=args.device, channels=args.channels, callback=callback):
                    while status:
                        file.write(q.get())
        except Exception as e:
            parser.exit(type(e).__name__ + ': ' + str(e))
    

    def rec(self):
        print('stating thread')
        self.audio_thread = threading.Thread(target=self.record_audio)
        self.audio_thread.start()

class App(QWidget):
    def __init__(self):
        """Initialize init"""
        super().__init__()
        self.title = 'Screen Recorder'
        self.left = 100
        self.top = 100
        self.width = 200
        self.height = 60
        self.count = 0
        self.status = True
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.button = QPushButton('Start Desktop Recorder', self)
        self.button.setToolTip('Click here to start recording')
        self.button.move(10, 10)
        self.button.clicked.connect(self.chg)
        self.show()

    def chg(self):
        global status
        if (self.button.text() == 'Start Desktop Recorder'):
            status = True
            print('making true')
            self.av = videoRecoder()
            self.av.rec()
            self.ru = Record_audio()
            self.ru.rec()
            self.button.setText('Stop Desktop Recording')
        else:
            print("making False")
            status = False
            self.button.setText('Processing')
            self.ru.audio_thread.join()
            self.av.video_thread.join()
            cmd = "ffmpeg -ac 2 -channel_layout stereo -i temp_audio.wav -i temp_video.avi -pix_fmt yuv420p output.avi"
            subprocess.call(cmd, shell=True)

            local_path = os.getcwd()

            if os.path.exists(str(local_path) + "/temp_audio.wav"):
                os.remove(str(local_path) + "/temp_audio.wav")

            if os.path.exists(str(local_path) + "/temp_video.avi"):
                os.remove(str(local_path) + "/temp_video.avi")


            self.button.setText('Start Desktop Recorder')


app = QApplication(sys.argv)
ex = App()
sys.exit(app.exec_())