from tesseract_solution import *

def main():
    image_path = "data/nerki.png"

    data = scrape_data(image_path)
    flashcards = data_to_flashcards(data)
    show_image_with_boxes(image_path, flashcards)

if __name__ == "__main__":
    main()