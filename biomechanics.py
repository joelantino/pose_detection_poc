import numpy as np

def calculate_angle(a, b, c):
    """
    Calculates the angle between three points (a, b, c) in degrees.
    b is the vertex.
    a: [x, y]
    b: [x, y]
    c: [x, y]
    """
    a = np.array(a)  # First
    b = np.array(b)  # Mid
    c = np.array(c)  # Last

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle

    return angle

def get_joint_angles(landmarks):
    """
    Extracts key physiotherapy angles from pose landmarks.
    """
    if landmarks is None:
        return {}

    # MediaPipe Landmark IDs:
    # Hip: 24 (R), 23 (L)
    # Knee: 26 (R), 25 (L)
    # Ankle: 28 (R), 27 (L)
    # Shoulder: 12 (R), 11 (L)

    # Right Knee Angle
    r_hip = landmarks[24][:2]
    r_knee = landmarks[26][:2]
    r_ankle = landmarks[28][:2]
    r_knee_angle = calculate_angle(r_hip, r_knee, r_ankle)

    # Left Knee Angle
    l_hip = landmarks[23][:2]
    l_knee = landmarks[25][:2]
    l_ankle = landmarks[27][:2]
    l_knee_angle = calculate_angle(l_hip, l_knee, l_ankle)

    # Right Hip Angle (Shoulder, Hip, Knee)
    r_shoulder = landmarks[12][:2]
    r_hip_angle = calculate_angle(r_shoulder, r_hip, r_knee)

    # Left Hip Angle
    l_shoulder = landmarks[11][:2]
    l_hip_angle = calculate_angle(l_shoulder, l_hip, l_knee)

    return {
        "right_knee": r_knee_angle,
        "left_knee": l_knee_angle,
        "right_hip": r_hip_angle,
        "left_hip": l_hip_angle
    }

def normalize_landmarks(landmarks):
    """
    Normalizes landmarks relative to hip center to make them scale/translation invariant.
    """
    if landmarks is None:
        return None
    
    # Calculate hip center
    mid_hip = (landmarks[23][:3] + landmarks[24][:3]) / 2
    
    # Subtract hip center from all coordinates
    normalized = landmarks.copy()
    normalized[:, :3] -= mid_hip
    
    return normalized

def joint_difference(user_landmarks, target_landmarks):
    """
    Calculates the Euclidean distance between user and target landmarks.
    """
    if user_landmarks is None or target_landmarks is None:
        return None
        
    # Only compare x, y coordinates
    diff = user_landmarks[:, :2] - target_landmarks[:, :2]
    return diff
