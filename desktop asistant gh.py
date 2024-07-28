
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 22 22:36:58 2024

@author: halif
"""

import sys
import pyautogui
import speech_recognition as sr
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
import requests
import json
from mss import mss
from PIL import Image
import io
import time
import re

OCR_API_KEY = ""

def capture_screenshot():
    with mss() as sct:
        monitor = sct.monitors[0]
        sct_img = sct.grab(monitor)
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

def ocr_space_api(image):
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    image_bytes = img_byte_arr.getvalue()
    payload = {
        'apikey': OCR_API_KEY,
        'language': 'eng',
        'OCREngine': '2',
        'isOverlayRequired': 'true'
    }
    files = {'file': ('screenshot.png', image_bytes, 'image/png')}
    try:
        r = requests.post('https://api.ocr.space/parse/image', files=files, data=payload, timeout=10)
        r.raise_for_status()
        return r.content.decode()
    except requests.exceptions.RequestException as e:
        print(f"Error in OCR API request: {e}")
        return None

def word_match(target, word):
    target = target.lower()
    word = word.lower()
    if target == word:
        return True
    if target in word and len(target) > 3:
        return True
    if word in target and len(word) > 3:
        return True
    return False

def find_word_coordinates(ocr_result, target_word):
    coordinates = []
    if not ocr_result:
        return coordinates
    try:
        result = json.loads(ocr_result)
        if result.get("IsErroredOnProcessing") == False:
            for text_result in result.get("ParsedResults", []):
                text_overlay = text_result.get("TextOverlay", {})
                lines = text_overlay.get("Lines", [])
                for line in lines:
                    line_text = ' '.join([word.get("WordText", "") for word in line.get("Words", [])])
                    print(f"OCR detected line: {line_text}")  # Debug output
                    if word_match(target_word, line_text):
                        for word in line.get("Words", []):
                            word_text = word.get("WordText", "")
                            if word_match(target_word, word_text):
                                left = word.get("Left", 0)
                                top = word.get("Top", 0)
                                width = word.get("Width", 0)
                                height = word.get("Height", 0)
                                coordinates.append((int(left), int(top), int(width), int(height)))
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse API response: {e}")
    except Exception as e:
        print(f"Unexpected error in find_word_coordinates: {e}")
    return coordinates

def listen_for_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for command...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
        except sr.WaitTimeoutError:
            print("Listening timed out. Please try again.")
            return None
    
    try:
        command = recognizer.recognize_google(audio).lower()
        print(f"Command recognized: {command}")
        return command
    except sr.UnknownValueError:
        print("Could not understand the audio")
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return None

def click_on_word(coordinates):
    x, y = coordinates[0] + coordinates[2] // 2, coordinates[1] + coordinates[3] // 2
    pyautogui.moveTo(x, y, duration=0.5)
    pyautogui.click()
    print(f"Clicked at coordinates: ({x}, {y})")

class OverlayWidget(QWidget):
    def __init__(self, coordinates, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(0, 0, QApplication.desktop().screenGeometry().width(), QApplication.desktop().screenGeometry().height())
        self.numbers = []
        self.coordinates = coordinates
        for i, (left, top, width, height) in enumerate(coordinates, 1):
            number_label = QLabel(str(i), self)
            number_label.setFont(QFont('Arial', 40, QFont.Bold))
            number_label.setStyleSheet("color: green;")
            number_label.setAlignment(Qt.AlignCenter)
            number_label.setGeometry(left, top - 50, width, 50)
            number_label.mousePressEvent = self.create_click_event(i, left + width // 2, top + height // 2)
            self.numbers.append((i, number_label, left, top))
            number_label.show()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.listen_for_number)
        self.timer.start(100)  # Check for voice command every 100 ms

    def create_click_event(self, number, x, y):
        def click_event(event):
            self.move_mouse_to_number(x, y)
            self.close()
        return click_event

    def move_mouse_to_number(self, x, y):
        pyautogui.moveTo(x, y, duration=0.5)
        pyautogui.click()
        print(f"Clicked at coordinates: ({x}, {y})")

    def parse_number(self, command):
        number_words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
        words = command.split()
        for word in words:
            if word.isdigit():
                return int(word)
            if word in number_words:
                return number_words.index(word)
        return None

    def listen_for_number(self):
        command = listen_for_command()
        if command:
            number = self.parse_number(command)
            if number is not None:
                if 1 <= number <= len(self.coordinates):
                    left, top, width, height = self.coordinates[number - 1]
                    self.move_mouse_to_number(left + width // 2, top + height // 2)
                    self.close()
                else:
                    print("Invalid number. Please try again.")
            elif "exit" in command:
                self.close()

def main():
    app = QApplication(sys.argv)

    while True:
        print("Say 'click' followed by the word you want to click on, or 'exit' to quit.")
        command = listen_for_command()
        
        if not command:
            continue
        
        if command.startswith("click"):
            target_word = command.split("click", 1)[1].strip()
            if target_word:
                print(f"Searching for '{target_word}'")
                screenshot = capture_screenshot()
                response = ocr_space_api(screenshot)
                if response:
                    coordinates = find_word_coordinates(response, target_word)
                    
                    if coordinates:
                        print(f"Found {len(coordinates)} instances of '{target_word}'")
                        if len(coordinates) == 1:
                            click_on_word(coordinates[0])
                        else:
                            print("Say the number of the instance you want to click, or 'exit' to cancel")
                            overlay = OverlayWidget(coordinates)
                            overlay.show()
                            app.exec_()  # This will keep the overlay open until a number is clicked or spoken
                    else:
                        print(f"'{target_word}' not found on screen")
                else:
                    print("OCR processing failed. Please try again.")
            else:
                print("No word specified after 'click'")
        elif command == "exit":
            print("Exiting the program.")
            break
        else:
            print("Command not recognized. Please say 'click' followed by a word, or 'exit'.")
        
        time.sleep(0.5)  # Add a small delay between commands

    sys.exit()

if __name__ == "__main__":
    main()