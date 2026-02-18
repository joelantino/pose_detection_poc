import cv2
import numpy as np
from utils import draw_skeleton

class GhostCoach:
    """
    Renders a semi-transparent 'Ghost Stickman' to guide the user.
    """
    def __init__(self):
        # MediaPipe POSE_CONNECTIONS indices
        self.connections = [
            (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), # Upper Body
            (11, 23), (12, 24), (23, 24), # Torso
            (23, 25), (25, 27), (24, 26), (26, 28), # Legs
            (15, 17), (17, 19), (19, 15), (16, 18), (18, 20), (20, 16), # Hands
            (27, 29), (29, 31), (31, 27), (28, 30), (30, 32), (32, 28)  # Feet
        ]
        
        # Default 'neutral' ghost position (will be updated dynamically)
        self.base_pose = None 
        self.current_display_pose = None
        self.alpha = 0.4 # Ghost transparency
        
    def set_ideal_pose(self, landmarks):
        """
        Sets the template landmark set for the coach.
        """
        self.base_pose = landmarks
        self.current_display_pose = landmarks.copy()

    def render(self, frame, landmarks, color=(200, 200, 200), offset=(100, 0)):
        """
        Draws the ghost skeleton on the frame.
        """
        if landmarks is None:
            return frame
            
        overlay = frame.copy()
        draw_skeleton(overlay, landmarks, self.connections, color=color, thickness=3, offset=offset)
        
        # Blend overlay for ghost effect
        cv2.addWeighted(overlay, self.alpha, frame, 1 - self.alpha, 0, frame)
        return frame

    def get_animated_pose(self, exercise_type, timestamp_ms, user_progress=None):
        """
        Calculates frame-by-frame anatomical movement for the Coach.
        If 'user_progress' (0.0-1.0) is provided, the coach syncs to the user.
        Otherwise, it falls back to time-based animation.
        """
        # Base Standing Pose (Realistic Proportions)
        # Coordinates: [x, y, z, visibility]
        pose = np.zeros((33, 4))
        pose[0]  = [0.5, 0.15, 0, 1]   # Head
        pose[11] = [0.42, 0.25, 0, 1]  # L Shoulder
        pose[12] = [0.58, 0.25, 0, 1]  # R Shoulder
        
        # Default Arms: Hands on Hips (Stationary)
        # Elbows out slightly
        pose[13] = [0.38, 0.45, 0, 1]; pose[14] = [0.62, 0.45, 0, 1] 
        # Wrists on Hips
        pose[15] = [0.44, 0.58, 0, 1]; pose[16] = [0.56, 0.58, 0, 1] 
        
        pose[23] = [0.45, 0.60, 0, 1]; pose[24] = [0.55, 0.60, 0, 1] # Hips
        pose[25] = [0.45, 0.80, 0, 1]; pose[26] = [0.55, 0.80, 0, 1] # Knees
        pose[27] = [0.45, 0.98, 0, 1]; pose[28] = [0.55, 0.98, 0, 1] # Ankles

        # determine phase curve
        if user_progress is not None:
             # User-driven (Sync Mode)
             # Smooth the raw 0-1 input slightly
             phase = user_progress 
        else:
             # Time-driven (Demo Mode)
             t = (timestamp_ms % 4000) / 4000.0
             phase = (1 - np.cos(t * 2 * np.pi)) / 2 # Smooth 0->1->0 cycle

        if exercise_type == "squat":
            # Realistic squat: Hips go back (z), Torso leans forward slightly
            depth = 0.25
            pose[23:25, 1] += depth * phase             # Hips down
            pose[25:27, 1] += (depth * 0.45) * phase     # Knees flex
            pose[0:23, 1] += (depth * 0.8) * phase       # Upper body follows
            # ARMS: Stationary on hips (move with torso)

        elif exercise_type == "bicep_curl":
            # Tuck elbows to sides
            pose[13] = [0.42, 0.42, 0, 1]
            pose[14] = [0.58, 0.42, 0, 1]
            # Curl arc for wrists
            # Phase 0: Down (150 deg), Phase 1: Up (30 deg)
            radius = 0.18
            # Angle 0 = Straight down (+PI/2), Angle PI = Straight up (-PI/2)
            angle = (np.pi/2) - (phase * 1.2 * np.pi) 
            angle = np.clip(angle, -np.pi/3, np.pi/2) # Limit ROM
            
            pose[15, 0] = pose[13, 0] - radius * np.cos(angle)
            pose[15, 1] = pose[13, 1] + radius * np.sin(angle)
            pose[16, 0] = pose[14, 0] + radius * np.cos(angle)
            pose[16, 1] = pose[14, 1] + radius * np.sin(angle)

        elif exercise_type == "shoulder_press":
            # Start: Elbows at 90 deg, shoulder height
            # End: Arms full extension overhead
            pose[13] = [0.35, 0.25 - (0.2 * phase), 0, 1] # Elbows
            pose[14] = [0.65, 0.25 - (0.2 * phase), 0, 1]
            
            pose[15] = [0.35, 0.25 - (0.35 * phase), 0, 1] # Wrists
            pose[16] = [0.65, 0.25 - (0.35 * phase), 0, 1]

        elif exercise_type == "lunge":
            # Right leg forward lunge
            lunge_depth = 0.22
            # Right leg moves forward and down
            pose[26, 0] += 0.05 * phase; pose[26, 1] += 0.1 * phase # R Knee
            pose[28, 0] += 0.15 * phase # R Ankle stays forward
            # Left leg drops back
            pose[25, 1] += 0.15 * phase # L Knee drops
            pose[23:25, 1] += lunge_depth * phase # Hips drop
            pose[0:23, 1] += (lunge_depth * 0.95) * phase # Torso follows
            # ARMS: Stationary on hips (move with torso)

        elif exercise_type == "jumping_jacks":
            # Reset Arms to sides for start of Jumping Jack
            pose[13] = [0.40, 0.45, 0, 1]; pose[14] = [0.60, 0.45, 0, 1]
            pose[15] = [0.40, 0.60, 0, 1]; pose[16] = [0.60, 0.60, 0, 1]
            
            # Arc movement for arms
            arm_radius = 0.35
            angle = -np.pi/2 + (phase * 3.14) # -90 to 90 degrees (User driven 0-1)
            pose[15, 0] = pose[11, 0] - arm_radius * np.cos(angle)
            pose[15, 1] = pose[11, 1] - arm_radius * np.sin(angle)
            pose[16, 0] = pose[12, 0] + arm_radius * np.cos(angle)
            pose[16, 1] = pose[12, 1] - arm_radius * np.sin(angle)
            # Legs jump out
            pose[27, 0] -= 0.15 * phase
            pose[28, 0] += 0.15 * phase
            
        elif exercise_type == "high_knees":
            # For alternating exercises, single 0-1 phase isn't enough to know L vs R.
            # We fail back to time for rhythm, but scale magnitude by user_progress if available
            alt_t = (timestamp_ms % 2000) / 2000.0
            alt_phase = np.sin(alt_t * 2 * np.pi)
            
            # If user is stationary (progress=0), coach marks time but stays low? 
            # Or just keep coach marching to set tempo. keeping time based for High Knees is safer.
            if alt_phase > 0: # Left knee
                pose[25, 1] -= 0.3 * alt_phase
                pose[27, 1] -= 0.25 * alt_phase; pose[27, 0] += 0.05 * alt_phase
            else: # Right knee
                pose[26, 1] -= 0.3 * abs(alt_phase)
                pose[28, 1] -= 0.25 * abs(alt_phase); pose[28, 0] -= 0.05 * abs(alt_phase)
            # ARMS: Stationary on hips

        elif exercise_type == "arm_circles":
            circ_t = (timestamp_ms % 2000) / 2000.0
            radius = 0.12
            # Hold arms out horizontally
            pose[13, 0] = pose[11, 0] - 0.15; pose[13, 1] = pose[11, 1]
            pose[14, 0] = pose[12, 0] + 0.15; pose[14, 1] = pose[12, 1]
            # Circle the wrists
            pose[15, 0] = pose[13, 0] + radius * np.cos(circ_t * 2 * np.pi)
            pose[15, 1] = pose[13, 1] + radius * np.sin(circ_t * 2 * np.pi)
            pose[16, 0] = pose[14, 0] - radius * np.cos(circ_t * 2 * np.pi)
            pose[16, 1] = pose[14, 1] + radius * np.sin(circ_t * 2 * np.pi)

        elif exercise_type == "side_leg_raise":
            # Right leg raises out to the side
            pose[26, 0] += 0.25 * phase; pose[26, 1] -= 0.1 * phase # Knee
            pose[28, 0] += 0.35 * phase; pose[28, 1] -= 0.15 * phase # Ankle
            # Slight torso tilt (moves arms too)
            pose[0:23, 0] -= 0.05 * phase
            # ARMS: Stationary on hips

        elif exercise_type == "calf_raises":
            rise = 0.08
            pose[0:27, 1] -= rise * phase # Entire body raises
            # Ankles stay down but "stretch"
            pose[27, 1] = 0.98 - (rise * 0.2 * phase)
            pose[28, 1] = 0.98 - (rise * 0.2 * phase)
            # ARMS: Stationary on hips

        elif exercise_type == "torso_twist":
            # Rotating the shoulders and head
            rotation = 0.1 * np.sin((timestamp_ms % 4000)/4000.0 * 2 * np.pi)
            if user_progress is not None:
                # Map 0-1 progress to -rotation to +rotation? Hard to map linear twist.
                # Keep time based for twist.
                pass
                
            pose[11, 0] += rotation; pose[12, 0] += rotation
            pose[0, 0] += rotation * 1.5
            # Arms move across body if they are on hips
            pose[15, 0] += rotation * 1.5
            pose[16, 0] += rotation * 1.5

        return pose

    def generate_static_squat_pose(self):
        return self.get_animated_pose("squat", 0)
