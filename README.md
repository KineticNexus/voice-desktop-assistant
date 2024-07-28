# Voice desktop assistant
This script is a voice-controlled application that allows users to click on words displayed on their screen. It uses speech recognition to listen for commands, captures a screenshot, performs OCR (Optical Character Recognition) to identify text on the screen, and then clicks on the specified word.

## Functionality:
This script is a voice-controlled application that allows users to click on words displayed on their screen. It uses speech recognition to listen for commands, captures a screenshot, performs OCR (Optical Character Recognition) to identify text on the screen, and then clicks on the specified word.

## Key Components:

Speech recognition (using speech_recognition)
Screen capture (using mss)
OCR processing (using an external FREE API)
GUI overlay for multiple word instances (using PyQt5)
Mouse control (using pyautogui)


## Main Flow:

The script continuously listens for voice commands.
When it hears "click" followed by a word, it captures a screenshot and performs OCR.
If the word is found, it either clicks on it (if there's only one instance) or displays an overlay for the user to choose which instance to click.

## Required packages:
Copypyautogui
SpeechRecognition
PyQt5
requests
mss
Pillow
