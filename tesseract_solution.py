import pytesseract
import pandas as pd
from PIL import Image
from pytesseract import image_to_string
import cv2
import numpy as np

class Flashcard:
    def __init__(self, text, left, width, top, height):
        self.text = text
        self.left = left
        self.width = width
        self.top = top
        self.height = height

    def appendText(self, new_text):
        self.text = self.text + ' ' + new_text

    def resizeFlashcard(self, new_left, new_width, new_top, new_height):
        self.width = new_left - self.left + new_width
        self.top = min(self.top, new_top)
        self.height = max(self.height, new_height)


def scrape_data(path):
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    im = cv2.imread(path)
    processed_data = pytesseract.image_to_data(
        im,
        lang='pol',
        output_type=pytesseract.Output.DATAFRAME
        # config='--psm 6 --oem 0'
    )

    processed_data = processed_data.dropna(subset=['text'])

    high_confidence_data = processed_data[
        (processed_data['conf'] > 5) &
        ((processed_data['text'].str.len() > 2) | (processed_data['text'] == 'i')) &
        processed_data['text'].str.isalpha()
        ]

    return processed_data

def data_to_flashcards(data):
    flashcardsSet = []
    flashcard = None
    previousLeft = -10000
    previousWidth = -10000
    previousTop = -10000
    previousHeight = -10000

    for index, row in data[['text', 'left', 'width', 'top', 'height']].iterrows():
        text = row['text']
        left = row['left']
        width = row['width']
        top = row['top']
        height = row['height']

        if previousWidth + previousLeft + 10 >= left and abs(previousTop - top) <= 5:
            flashcard.appendText(text)
            flashcard.resizeFlashcard(left, width, top, height)
        else:
            if flashcard:
                flashcardsSet.append(flashcard)
            flashcard = Flashcard(text, left, width, top, height)

        previousLeft = left
        previousWidth = width
        previousTop = top
        previousHeight = height

    if flashcard:
        flashcardsSet.append(flashcard)

    return flashcardsSet

def show_image_with_boxes(path, flashcards):
    image = cv2.imread(path)
    window_name = 'Image'
    color = (6,57,112)
    thickness = 2

    for o in flashcards:
        start = (o.left, o.top)
        end = (o.left + o.width, o.top + o.height)
        image = cv2.rectangle(image, start, end, color, thickness)
        #print(o.text)

    cv2.imshow(window_name, image)
    cv2.waitKey(0)

