# ABOUT
This is a python-based Remote Access Trojan(RAT)  

* With functions such as
  > Download/Upload file command
  > 
  > Keylogging
  >
  > screen share/shot
  >
  > camera streaming/snap
  >
  > persistence (maintaining access)
  >
  > mic recording, and keystroke

* The required modules for the server(attacker):
  > pyaudio
  >
  > colorama (optional to use)
  >
  > pyfiglet (optional to use)
  >
  > cv2

* The required modules for the client(target):
  > cv2
  >
  > pyautogui
  >
  > pynput
  >
  > mss
  >
  > numpy

## NOTE
This RAT is only a PoC project, this still has alot of Errors and won't work if you run the client on different computers unless you did a tunneling or a port forwarding.  
If you wanna run the client-side in exe file, you can use pyinstaller for the CLI version, and auto-py-to-exe for the GUI version.  

```bash
pip install pyinstaller
```

for CLI version or  


```bash
pip install auto-py-to-exe
```

for GUI version

## SETUP
Server machine(listener)
```
python attacker.py
```
Target machine
```
python target.py
```

## WARNING ⚠
I do not take any responsibility if someone has installed this Trojan on another person computer, if there's any person who got their data stolen. Not my fault, not my responsibility to apologize.
* DETECTION ⚠
> High network usage
> 
> High cpu usage
> 
> Unknown process pops up in task manager
> 
> High ram usage
> 
> Netstat cmd command
> 
> VirusTotal
> 
> Strange Behaviour
> 
> Heuristic detection
> 
> Registry
> 
> Strange text file
> 
> Hash
> 
> etc.
>

I don't take any responsibility if anyone has this installed on someone computer.
