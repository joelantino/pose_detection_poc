import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class PoseEngine:
    """
    Wrapper for MediaPipe Tasks API to handle real-time body landmark detection.
    """
    def __init__(self, model_path='pose_landmarker.task', min_detection_confidence=0.5, min_tracking_confidence=0.5):
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=min_detection_confidence,
            min_pose_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            output_segmentation_masks=False,
        )
        self.detector = vision.PoseLandmarker.create_from_options(options)
        self.last_results = None
        self.frame_timestamp_ms = 0

    def process_frame(self, frame):
        """
        Processes a single frame and returns results.
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # Incremental timestamp
        self.frame_timestamp_ms += 33 # Approx 30 FPS
        
        self.last_results = self.detector.detect_for_video(mp_image, self.frame_timestamp_ms)
        return self.last_results

    def draw_landmarks(self, frame, results, color=(0, 255, 0)):
        """
        Manually draws skeleton landmarks on the frame (since drawing_utils may be missing).
        """
        if not results or not results.pose_landmarks:
            return frame
        
        h, w, _ = frame.shape
        # POSE_CONNECTIONS indices for MediaPipe
        CONNECTIONS = [
            (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), # Upper Body
            (11, 23), (12, 24), (23, 24), # Torso
            (23, 25), (25, 27), (24, 26), (26, 28), # Legs
            (15, 17), (17, 19), (19, 15), (16, 18), (18, 20), (20, 16), # Hands
            (27, 29), (29, 31), (31, 27), (28, 30), (30, 32), (32, 28)  # Feet
        ]

        # Get landmarks for the first detected pose
        landmarks = results.pose_landmarks[0]
        
        # Draw joints
        for lm in landmarks:
            cx, cy = int(lm.x * w), int(lm.y * h)
            cv2.circle(frame, (cx, cy), 3, color, -1)
            
        # Draw connections
        for connection in CONNECTIONS:
            start_idx = connection[0]
            end_idx = connection[1]
            p1 = landmarks[start_idx]
            p2 = landmarks[end_idx]
            
            x1, y1 = int(p1.x * w), int(p1.y * h)
            x2, y2 = int(p2.x * w), int(p2.y * h)
            cv2.line(frame, (x1, y1), (x2, y2), color, 2)
            
        return frame

    def get_landmarks_array(self, results):
        """
        Converts Tasks API landmarks to a normalized NumPy array compatible with biomechanics.py.
        """
        if not results or not results.pose_landmarks:
            return None
        
        landmarks = results.pose_landmarks[0]
        arr = []
        for lm in landmarks:
            arr.append([lm.x, lm.y, lm.z, getattr(lm, 'visibility', 1.0)])
        
        return np.array(arr)
