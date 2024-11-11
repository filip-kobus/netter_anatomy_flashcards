import io
import os
import numpy as np
from google.cloud import vision
from scipy.spatial import distance
from scipy.cluster.hierarchy import fcluster, linkage
import cv2

class VisionAI:

    def __init__(self, image_path, client_path='client_file.json'):
        self.path = image_path
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = client_path
        self.client = vision.ImageAnnotatorClient()

        self.image = cv2.imread(image_path)
        self.content = self.open_image(image_path)
        self.texts = self.detect_text()

        self.words = self.extract_words()
        self.positions = np.array([[word['x'], word['y']] for word in self.words])
        self.grouped_boxes = self.group_and_get_boxes()
        self.draw_bounding_boxes()

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

    def weighted_distance(self, u, v):
        horizontal_weight = 1.0  # Adjust this to place more weight on horizontal proximity
        vertical_weight = 3.0  # Adjust this to control vertical sensitivity
        return distance.euclidean((u[0] * horizontal_weight, u[1] * vertical_weight),
                                  (v[0] * horizontal_weight, v[1] * vertical_weight))

    def group_and_get_boxes(self):
        Z = linkage(self.positions, method='single', metric=self.weighted_distance)
        threshold_distance = 60  # Tune this based on desired clustering range
        clusters = fcluster(Z, t=threshold_distance, criterion='distance')

        grouped_boxes = []
        for cluster_id in set(clusters):
            cluster_words = [self.words[i] for i in range(len(self.words)) if clusters[i] == cluster_id]
            x_coords = [vertex[0] for word in cluster_words for vertex in word['vertices']]
            y_coords = [vertex[1] for word in cluster_words for vertex in word['vertices']]
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            grouped_boxes.append(((min_x, min_y), (max_x, max_y)))

            cluster_text = ' '.join(word['text'] for word in cluster_words)
            print(f"Clustered caption: {cluster_text}")
            print(f"Bounding box: {((min_x, min_y), (max_x, max_y))}")

        return grouped_boxes

    def draw_bounding_boxes(self):
        for box in self.grouped_boxes:
            cv2.rectangle(self.image, box[0], box[1], color=(0, 255, 0), thickness=2)

        cv2.imshow("Image with Clustered Bounding Boxes", self.image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    vision_ai = VisionAI(image_path='your_image_path.jpg', client_path='path_to_your_client_file.json')