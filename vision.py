import io
import os
from google.cloud import vision

class Flashcard:
    def __init__(self, vertices):
        self.left, self.right, self.top, self.bottom = (
            self._extract_vertices(vertices))

    @staticmethod
    def _extract_vertices(vertices):
        def get_midpoint(point1, point2):
            return int((point1 + point2) / 2)

        left_upper = vertices[0]
        right_upper = vertices[1]
        right_lower = vertices[2]
        left_lower = vertices[3]

        left = get_midpoint(left_upper[0], left_lower[0])
        right = get_midpoint(right_upper[0], right_lower[0])
        top = get_midpoint(left_upper[1], right_upper[1])
        bottom = get_midpoint(left_lower[1], right_lower[1])

        return left, right, top, bottom

    def connect_flashcards(self, flashcard):
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

    def left_upper_corner(self):
        return self.left, self.top

    def right_lower_corner(self):
        return self.right, self.bottom

class VisionAI:
    HORIZONTAL_SPACING_RATIO = 11 / 20
    VERTICAl_SPACING_RATIO = 8 / 20
    HEIGHT_DIFFERENCE_RATIO = 6 / 20
    ARTIFACTS = ['ebrary', 'F.Netter']

    def __init__(self, image_path, client_path='client_file.json'):
        self.path = image_path
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = client_path
        self.client = vision.ImageAnnotatorClient()
        self.flashcards = self._create_flashcards()
        self.grouped_boxes = self._flashcards_to_boxes()

    @staticmethod
    def _open_image(path):
        with io.open(path, 'rb') as image_file:
            content = image_file.read()
        return content

    def _retrieve_data(self):
        content = self._open_image(self.path)

        image_vision = vision.Image(content=content)
        response = self.client.text_detection(image=image_vision)
        retrieved_data = response.text_annotations

        if response.error.message:
            raise Exception(f'{response.error.message}')

        return retrieved_data

    @staticmethod
    def _contains_artefacts(word):
        count = sum(c.isdigit() for c in word)
        if count > 4:
            return True

        artifacts = VisionAI.ARTIFACTS
        for artifact in artifacts:
            if word in artifact:
                return True

        return False

    def _create_flashcards(self):
        datalist = self._retrieve_data()
        flashcards = []
        for data in datalist[1:]:
            word = data.description
            vertices = [(vertex.x, vertex.y) for vertex in data.bounding_poly.vertices]

            if not self._contains_artefacts(word):
                flashcard = Flashcard(vertices)
                flashcards.append(flashcard)

        return flashcards

    def _get_thresholds(self):
        sorted_cards = sorted(self.flashcards, key=lambda f: f.get_height())
        median_of_height = sorted_cards[len(sorted_cards) // 2].get_height()

        horizontal_spacing_threshold = round(VisionAI.HORIZONTAL_SPACING_RATIO * median_of_height)
        vertical_spacing_threshold = round(VisionAI.VERTICAl_SPACING_RATIO * median_of_height)
        height_difference_threshold = round(VisionAI.HEIGHT_DIFFERENCE_RATIO * median_of_height)

        return horizontal_spacing_threshold, vertical_spacing_threshold, height_difference_threshold

    def _flashcards_to_boxes(self):
        boxes = []
        flashcards = self.flashcards
        horizontal_threshold, vertical_threshold , height_difference = self._get_thresholds()

        flashcards = self._connect_horizontally(flashcards, horizontal_threshold, height_difference)
        flashcards = self._connect_vertically(flashcards, vertical_threshold)

        for flashcard in flashcards:
            left_corner = flashcard.left_upper_corner()
            right_corner = flashcard.right_lower_corner()
            boxes.append((left_corner, right_corner))

        return boxes

    @staticmethod
    def _connect_horizontally(flashcards, horizontal_threshold, height_diff,):
        size = len(flashcards)
        flashcards.sort(key=lambda f: f.left)
        i = 0
        while i < size:
            card = flashcards[i]
            j = i + 1
            while j < size:
                next_card = flashcards[j]

                # if cards are on the same level and are apart more than threshold,
                # no point in further searching for connections (cards are sorted horizontally)
                if abs(next_card.bottom - card.bottom) < height_diff:
                    if abs(next_card.left - card.right) < horizontal_threshold:
                        card.connect_flashcards(next_card)
                        flashcards.pop(j)
                        size -= 1
                        j -= 1
                    else:
                        break
                j += 1
            i += 1
            
        return flashcards

    @staticmethod
    def _connect_vertically(flashcards, vertical_threshold):
        size = len(flashcards)
        flashcards.sort(key=lambda f: f.top)
        i = 0
        while i < size:
            card = flashcards[i]
            j = i + 1
            while j < size:
                next_card = flashcards[j]

                # if cards overlap vertically and are apart more than threshold,
                # no point in further searching for connections (cards are sorted vertically)
                if card.is_overlapping(next_card):
                    if abs(next_card.top - card.bottom) < vertical_threshold:
                        card.connect_flashcards(next_card)
                        flashcards.pop(j)
                        size -= 1
                        j -= 1
                    else:
                        break
                j += 1
            i += 1

        return flashcards
