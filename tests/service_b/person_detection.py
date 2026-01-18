import numpy as np
import requests
import cv2

def get_image_url_people_count(image_url: str) -> int:
    # Download image
    response = requests.get(image_url, timeout=10)
    response.raise_for_status()

    # Convert bytes to OpenCV image
    image_array = np.frombuffer(response.content, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Failed to decode image from URL")

    # Convert BGR to RGB if your detect_people expects RGB
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Detect people
    count, _ = detect_people(image)

    return count


def detect_people(image: str) -> tuple[int, cv2.typing.MatLike]:
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    boxes, weights = hog.detectMultiScale(image, 
                                          winStride=(4, 4), 
                                          padding=(4, 4), 
                                          scale=1.05,
                                          )
    boxes = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])

    for (x1, y1, x2, y2) in boxes:
        cv2.rectangle(image, (x1, y1), (x2, y2),(0, 255, 0), 2)
        
    return (len(boxes), image)