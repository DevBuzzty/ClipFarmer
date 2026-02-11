import cv2
import os

def extract_screenshot(video_path, timestamp_sec, output_path):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000)
    success, image = cap.read()
    if success:
        cv2.imwrite(output_path, image)
    cap.release()
    return success
