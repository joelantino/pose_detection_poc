import cv2
import numpy as np

def draw_text_status(frame, status_text, color=(0, 255, 0)):
    """
    Draws status text on the frame.
    Note: The user requested visual feedback ONLY, but status text is useful for debugging 
    or as a tiny overhead indicator. We will use it sparingly or hide it.
    """
    cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)

def alpha_blend(frame, overlay, alpha=0.5):
    """
    Blends an overlay with the original frame.
    """
    return cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

def draw_skeleton(frame, landmarks, connections, color=(255, 255, 255), thickness=2, offset=(0, 0)):
    """
    Manually draws a skeleton on a frame using normalized landmarks.
    """
    h, w, _ = frame.shape
    
    # Scale and Shift context mapping if needed
    for connection in connections:
        start_idx = connection[0]
        end_idx = connection[1]
        
        # Get coordinates
        p1 = landmarks[start_idx]
        p2 = landmarks[end_idx]
        
        # Map to pixel coordinates
        x1, y1 = int(p1[0] * w), int(p1[1] * h)
        x2, y2 = int(p2[0] * w), int(p2[1] * h)
        
        # Skip if either point is at (0,0) - prevents lines stretching to corner
        if (x1 == 0 and y1 == 0) or (x2 == 0 and y2 == 0):
            continue
            
        # Apply offset and draw
        x1 += offset[0]
        y1 += offset[1]
        x2 += offset[0]
        y2 += offset[1]
        
        cv2.line(frame, (x1, y1), (x2, y2), color, thickness)
        cv2.circle(frame, (x1, y1), thickness + 1, color, -1)
        cv2.circle(frame, (x2, y2), thickness + 1, color, -1)
    
    return frame
