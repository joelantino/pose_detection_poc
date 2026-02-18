import numpy as np

class CorrectionEngine:
    """
    Elite Level Logic: Calculates the 'Force Vector' to pull the user's joints
    into the correct positions and translates this into ghost movement.
    """
    def __init__(self, smoothing=0.2):
        self.smoothing = smoothing
        self.last_correction = None

    def calculate_correction(self, user_landmarks, target_landmarks):
        """
        Compares user pose to target pose and returns a displacement vector.
        """
        if user_landmarks is None or target_landmarks is None:
            return None
            
        # We focus on major joints for guidance: Hips, Knees, Shoulders
        major_indices = [11, 12, 23, 24, 25, 26]
        
        # Displacement vector (Target - User)
        # We want to show where the user SHOULD be
        diff = target_landmarks[:, :2] - user_landmarks[:, :2]
        
        return diff

    def get_corrected_ghost(self, base_ghost_pose, user_landmarks, target_angles, current_angles):
        """
        Modifies the ghost pose to guide the user towards target angles.
        Example: If user's knee angle is 120 and target is 90, 
        the ghost knee should emphasize 'going lower'.
        """
        if user_landmarks is None:
            return base_ghost_pose
            
        corrected_pose = base_ghost_pose.copy()
        
        # Knee correction (Dynamic height adjustment)
        target_k = target_angles.get('knee_angle', 90)
        current_k = (current_angles.get('left_knee', 180) + current_angles.get('right_knee', 180)) / 2
        
        # If user is too high (angle > target), move ghost slightly lower than target to emphasize depth
        error = current_k - target_k
        if error > 10:
            # Move ghost joints downward (higher Y)
            correction_y = 0.05 
            # Apply to lower body 
            corrected_pose[23:29, 1] += correction_y
        elif error < -10:
            # Move ghost upward
            correction_y = -0.05
            corrected_pose[23:29, 1] += correction_y
            
        return corrected_pose
