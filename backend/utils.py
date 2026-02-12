import cv2
import os
import numpy as np

def extract_screenshot(video_path, timestamp_sec, output_path):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000)
    success, image = cap.read()
    if success:
        cv2.imwrite(output_path, image)
    cap.release()
    return success

def refine_facecam_crop(screenshot_path, initial_coords):
    """
    Versucht das Gesicht im angegebenen Ausschnitt zu finden und den Crop zu zentrieren.
    initial_coords: [ymin, xmin, ymax, xmax] (0-1000)
    """
    img = cv2.imread(screenshot_path)
    if img is None: return initial_coords

    h, w, _ = img.size if hasattr(img, 'size') else (img.shape[0], img.shape[1], 3)

    # Ausschnitt extrahieren
    fy1, fx1, fy2, fx2 = [int(c * h / 1000) if i % 2 == 0 else int(c * w / 1000) for i, c in enumerate(initial_coords)]
    facecam_img = img[fy1:fy2, fx1:fx2]

    # Gesichtserkennung
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(facecam_img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

    if len(faces) > 0:
        # Nimm das größte Gesicht
        (x, y, fw, fh) = max(faces, key=lambda f: f[2] * f[3])

        # Berechne Verschiebung um das Gesicht im initialen Ausschnitt zu zentrieren
        # Wir wollen den Ausschnitt [fy1, fx1, fy2, fx2] so verschieben, dass das Gesicht mittig ist
        # Aber wir bleiben innerhalb der Grenzen des Originalbildes.

        face_center_x_abs = fx1 + x + fw / 2
        face_center_y_abs = fy1 + y + fh / 2

        current_w = fx2 - fx1
        current_h = fy2 - fy1

        new_fx1 = max(0, int(face_center_x_abs - current_w / 2))
        new_fx2 = min(w, new_fx1 + current_w)
        new_fy1 = max(0, int(face_center_y_abs - current_h / 2))
        new_fy2 = min(h, new_fy1 + current_h)

        return [
            int(new_fy1 * 1000 / h),
            int(new_fx1 * 1000 / w),
            int(new_fy2 * 1000 / h),
            int(new_fx2 * 1000 / w)
        ]

    return initial_coords
