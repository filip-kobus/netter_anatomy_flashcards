document.addEventListener('DOMContentLoaded', function() {
    const pasteArea = document.getElementById('paste-area');

    if (pasteArea) {
        pasteArea.addEventListener('click', () => {
            pasteArea.focus();
        });

        pasteArea.addEventListener('paste', async function(event) {
            const clipboardItems = event.clipboardData.items;
            for (let item of clipboardItems) {
                if (item.type.indexOf('image') !== -1) {
                    const file = item.getAsFile();
                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('caption', 'Pasted Image'); // Add a default caption if you wish

                    try {
                        const response = await fetch('/upload', {
                            method: 'POST',
                            body: formData
                        });
                        const result = await response.text();
                        document.body.innerHTML = result; // Replace the entire body with new content
                    } catch (error) {
                        console.error('Error uploading the pasted image:', error);
                    }
                }
            }
        });
    }

    const existingGroupedBoxes = JSON.parse(document.getElementById('grouped-boxes-data').textContent || null);

    if (existingGroupedBoxes) {
        displayImage(document.getElementById('uploaded-image').src, existingGroupedBoxes);
    }

    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', async function() {
            const filename = this.getAttribute('data-filename');

            if (confirm(`Czy na pewno chcesz usunąć ${filename}?`)) {
                try {
                    const response = await fetch(`/delete/${filename}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });

                    const result = await response.json();
                    if (result.success) {
                        location.reload();  // Reload the page to update the gallery
                    } else {
                        alert('Wystąpił błąd podczas usuwania pliku.');
                    }
                } catch (error) {
                    console.error('Error deleting image:', error);
                }
            }
        });
    });

});

function displayImage(src, boxes) {
    const imgContainer = document.querySelector('#image-container');
    const imgElement = document.querySelector('#uploaded-image');

    if (!imgElement) {
        return;
    }

    // Update img element src
    imgElement.src = src;

    imgElement.onload = function () {
        // Get the actual dimensions of the displayed image
        const displayedWidth = imgElement.clientWidth;
        const displayedHeight = imgElement.clientHeight;

        // Get the original dimensions of the image
        const originalImage = new Image();
        originalImage.src = src;
        originalImage.onload = function () {
            const originalWidth = originalImage.width;
            const originalHeight = originalImage.height;

            const scaleX = displayedWidth / originalWidth;
            const scaleY = displayedHeight / originalHeight;

            document.querySelectorAll('.bounding-box').forEach(box => box.remove());

            boxes.forEach((box, index) => {
                const rect = document.createElement('div');
                rect.classList.add('bounding-box');
                rect.style.left = `${box[0][0] * scaleX}px`;
                rect.style.top = `${box[0][1] * scaleY}px`;
                rect.style.width = `${(box[1][0] - box[0][0]) * scaleX}px`;
                rect.style.height = `${(box[1][1] - box[0][1]) * scaleY}px`;
                rect.setAttribute('data-index', index);
                rect.addEventListener('click', function() {
                    rect.classList.toggle('hidden');
                });
                imgContainer.appendChild(rect);
            });


        };
    };
}