import io
import os
import numpy as np
from google.cloud import vision
from scipy.spatial import distance
from scipy.cluster.hierarchy import fcluster, linkage
import cv2
from sphinx.ext.autodoc import between


class Flashcard:
    def __init__(self, left, right, top, height):
        self.left = left
        self.right = right
        self.top = top
        self.bottom = height

    def add_flashcard(self, flashcard):
        self.right = max(self.right, flashcard.right)
        self.left = min(self.left, flashcard.left)
        self.top = min(self.top, flashcard.top)
        self.bottom = max(self.bottom, flashcard.bottom)

    def print_properties(self):
        print(f'Left: {self.left}, Right: {self.right}, Top: {self.top}, Bottom: {self.bottom}')

    def get_height(self):
        return self.bottom - self.top

    def is_overlapping(self, other):
        left = max(self.left, other.left)
        right = min(self.right, other.right)
        return right > left


class VisionAI:

    def __init__(self, image_path, client_path='client_file.json'):
        self.path = image_path
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = client_path
        self.client = vision.ImageAnnotatorClient()

        self.image = cv2.imread(image_path)
        self.content = self.open_image(image_path)
        self.texts = self.detect_text()
        self.words = self.extract_words()

    def open_image(self, path):
        with io.open(path, 'rb') as image_file:
            content = image_file.read()
        return content

    def detect_text(self):
        image_vision = vision.Image(content=self.content)
        response = self.client.text_detection(image=image_vision)
        texts = response.text_annotations

        if response.error.message:
            raise Exception(f'{response.error.message}')

        return texts

    def extract_words(self):
        words = []
        for text in self.texts[1:]:  # Skip the first result as it contains the entire text
            word = text.description
            vertices = [(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
            x_center = sum([v[0] for v in vertices]) / 4
            y_center = sum([v[1] for v in vertices]) / 4
            words.append({'text': word, 'x': x_center, 'y': y_center, 'vertices': vertices})
        return words

    def create_flashcards(self, words):
        flashcards = []

        for word in self.words:
            def get_midpoint(point1, point2):
                return int((point1 + point2) / 2)

            left_upper = word['vertices'][0]
            right_upper = word['vertices'][1]
            right_lower = word['vertices'][2]
            left_lower = word['vertices'][3]

            left = get_midpoint(left_upper[0], left_lower[0])
            right = get_midpoint(right_upper[0], right_lower[0])
            top = get_midpoint(left_upper[1], right_upper[1])
            bottom = get_midpoint(left_lower[1], right_lower[1])

            flashcard = Flashcard(left, right, top, bottom)
            flashcards.append(flashcard)

        flashcards.sort(key=lambda f: f.left)

        return flashcards

    def get_spacings(self, flashcards):
        sorted_cards = sorted(flashcards, key=lambda f: f.get_height())
        median_height = sorted_cards[len(sorted_cards) // 2].get_height()

        words_spacing = 11/20 * median_height
        line_height_differs = 6/20 * median_height
        horizontal_spacing = 6/20 * median_height

        return words_spacing, line_height_differs, horizontal_spacing

    def words_to_flashcards(self):
        flashcards = self.create_flashcards(self.words)
        words_spacing, height_difference, horizontal_spacing = self.get_spacings(flashcards)

        def connect_vertically():
            size = len(flashcards)
            i = 0
            while i < size:
                card = flashcards[i]
                j = i + 1
                while j < size:
                    next_card = flashcards[j]
                    if abs(next_card.bottom - card.bottom) < height_difference and abs(
                            next_card.left - card.right) < words_spacing:
                        card.add_flashcard(next_card)
                        flashcards.pop(j)
                        size -= 1
                    else:
                        j += 1

                i += 1

        def connect_horizontally():
            size = len(flashcards)
            flashcards.sort(key = lambda f: f.top)
            i = 0
            while i < size:
                card = flashcards[i]
                j = i + 1
                while j < size:
                    next_card = flashcards[j]
                    if abs(next_card.top - card.bottom) < horizontal_spacing and card.is_overlapping(next_card):
                        card.add_flashcard(next_card)
                        flashcards.pop(j)
                        size -= 1
                    else:
                        j += 1

                i += 1

        connect_vertically()
        connect_horizontally()

        return flashcards

    def draw_bounding_boxes(self):
        flashcards = self.words_to_flashcards()
        for card in flashcards:
            cv2.rectangle(self.image, (card.left, card.top), (card.right, card.bottom), color=(0, 255, 0), thickness=2)

        cv2.imshow("Image with Clustered Bounding Boxes", self.image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    vision_ai = VisionAI(image_path='static/uploads/nerki.png', client_path='client_file.json')
    vision_ai.draw_bounding_boxes()
