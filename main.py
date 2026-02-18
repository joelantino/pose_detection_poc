import cv2
import time
import json
import numpy as np
from pose_engine import PoseEngine
from biomechanics import get_joint_angles, calculate_angle
from ghost_coach import GhostCoach
from ui_manager import UIManager
import utils

def main():
    print("Initializng ELITE AI Physiotherapy System...")
    engine = PoseEngine(min_detection_confidence=0.85, min_tracking_confidence=0.85)
    coach = GhostCoach()
    ui = UIManager()
    
    exercises = [
        "squat", "lunge", "jumping_jacks", "high_knees", 
        "arm_circles", "side_leg_raise", "calf_raises", "torso_twist"
    ]
    current_idx = 0
    
    def load_template(idx):
        try:
            with open(f'templates/{exercises[idx]}.json', 'r') as f:
                return json.load(f)
        except:
            return {"target_angles": {"knee_angle": 100}, "tolerance": 20}

    template = load_template(current_idx)
    
    # State Machine V2 (STRICT)
    counter = 0
    state = "NEUTRAL" 
    rep_has_bottomed = False
    rep_start_time = 0
    
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    print("Elite Strict Engine Active.")

    while cap.isOpened():
        success, frame = cap.read()
        if not success: break
            
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        canvas = np.zeros((h, w * 2, 3), dtype=np.uint8)
        
        results = engine.process_frame(frame)
        landmarks = engine.get_landmarks_array(results)
        
        is_form_correct = False
        depth_percent = 0.0
        ex = exercises[current_idx]
        feedback_msg = "NO BODY DETECTED"
        
        if landmarks is not None:
            angles = get_joint_angles(landmarks)
            ex = exercises[current_idx]
            
            # --- 1. INITIALIZE & CALCULATE METRICS ---
            knee_val = (angles.get('left_knee', 180) + angles.get('right_knee', 180)) / 2
            hip_val = (angles.get('left_hip', 180) + angles.get('right_hip', 180)) / 2
            
            l_sh = calculate_angle(landmarks[23][:2], landmarks[11][:2], landmarks[13][:2])
            r_sh = calculate_angle(landmarks[24][:2], landmarks[12][:2], landmarks[14][:2])
            arm_val = (l_sh + r_sh) / 2
            
            feedback_msg = "PERFECT FORM"
            is_form_correct = True
            
            # --- 2. VISIBILITY & FORM CHECK ---
            vis_points = [23, 24, 25, 26, 27, 28] 
            full_body_vis = all(landmarks[i][3] > 0.7 for i in vis_points)
            
            if not full_body_vis:
                is_form_correct = False
                feedback_msg = "STEP BACK ->"
                # Emergency Reset: If we lose the body, reset the current rep
                rep_has_bottomed = False
            else:
                # Exercise Specific Corrections
                if ex == "squat":
                    if abs(hip_val - knee_val) > 45 and knee_val < 160: 
                        feedback_msg = "TOO MUCH LEAN!"; is_form_correct = False
                    knee_dist = abs(landmarks[25][0] - landmarks[26][0])
                    feet_dist = abs(landmarks[27][0] - landmarks[28][0])
                    if knee_dist < feet_dist * 0.7:
                        feedback_msg = "KNEES OUT!"; is_form_correct = False

                elif ex == "jumping_jacks":
                    l_el = calculate_angle(landmarks[11][:2], landmarks[13][:2], landmarks[15][:2])
                    r_el = calculate_angle(landmarks[12][:2], landmarks[14][:2], landmarks[16][:2])
                    if l_el < 140 or r_el < 140:
                        feedback_msg = "STRAIGHTEN ARMS!"; is_form_correct = False

                elif ex == "high_knees":
                    torso_lean = abs(landmarks[11][0] - landmarks[23][0])
                    if torso_lean > 0.15:
                        feedback_msg = "STAND TALL!"; is_form_correct = False

            # --- 3. REP COUNTING (DYNAMIC TRIGGER) ---
            if ex == "squat":
                if knee_val < 135: rep_has_bottomed = True
                elif knee_val > 160 and rep_has_bottomed:
                    counter += 1; rep_has_bottomed = False
                depth_percent = np.clip((170 - knee_val) / 60, 0, 1)
            
            elif ex == "jumping_jacks":
                if arm_val > 130: rep_has_bottomed = True
                elif arm_val < 50 and rep_has_bottomed:
                    counter += 1; rep_has_bottomed = False
                depth_percent = np.clip((arm_val - 40) / 110, 0, 1)

            elif ex == "high_knees":
                active_hip = max(180 - angles.get('left_hip', 180), 180 - angles.get('right_hip', 180))
                if active_hip > 65: rep_has_bottomed = True
                elif active_hip < 30 and rep_has_bottomed:
                    counter += 1; rep_has_bottomed = False
                depth_percent = np.clip(active_hip / 70, 0, 1)

            elif ex == "lunge":
                active_knee = min(angles.get('left_knee', 180), angles.get('right_knee', 180))
                if active_knee < 130: rep_has_bottomed = True
                elif active_knee > 165 and rep_has_bottomed:
                    counter += 1; rep_has_bottomed = False
                depth_percent = np.clip((170 - active_knee) / 60, 0, 1)

            elif ex == "side_leg_raise":
                val = angles.get('right_hip', 180)
                if val < 155: rep_has_bottomed = True
                elif val > 170 and rep_has_bottomed:
                    counter += 1; rep_has_bottomed = False
                depth_percent = np.clip((180 - val) / 40, 0, 1)
            
            elif ex == "calf_raises":
                curr_y = landmarks[11][1]
                if not hasattr(main, "base_y") or main.base_y == 0: main.base_y = curr_y
                
                if curr_y < main.base_y - 0.03: rep_has_bottomed = True
                elif curr_y > main.base_y - 0.005 and rep_has_bottomed:
                    counter += 1; rep_has_bottomed = False
                
                diff = main.base_y - curr_y
                depth_percent = np.clip(diff / 0.08, 0, 1)

            elif ex == "arm_circles":
                # Simple accumulate
                if not hasattr(main, "circ_accum"): main.circ_accum = 0
                main.circ_accum += np.linalg.norm(landmarks[15][:2] - landmarks[11][:2])
                if main.circ_accum > 15: # Arbitrary accumulation
                    counter += 1; main.circ_accum = 0
                depth_percent = 0.5 # No specific depth for circles, just rhythmic

            elif ex == "torso_twist":
                w = abs(landmarks[11][0] - landmarks[12][0])
                if w < 0.10: rep_has_bottomed = True
                elif w > 0.15 and rep_has_bottomed:
                    counter += 1; rep_has_bottomed = False
                depth_percent = 0.5 # No specific depth for twist, just rhythmic

            # --- 4. DYNAMIC COACH SYNC (Demo vs. Sync) ---
            # If user is idle, show a demo. If user moves, sync to them.
            if not hasattr(main, "last_move_time"): main.last_move_time = time.time()
            if not hasattr(main, "is_user_moving"): main.is_user_moving = False
            
            # Sensitivity trigger for sync
            if depth_percent > 0.1:
                main.last_move_time = time.time()
                main.is_user_moving = True
            elif time.time() - main.last_move_time > 2.0:
                main.is_user_moving = False

            if main.is_user_moving:
                # SYNC MODE: Coach follows user
                target_pose = coach.get_animated_pose(ex, int(time.time()*1000), user_progress=depth_percent)
            else:
                # DEMO MODE: Coach shows how to do it (Slow looping 0 -> 1 -> 0)
                t = (time.time() % 4) / 4.0
                demo_phase = (1 - np.cos(t * 2 * np.pi)) / 2
                target_pose = coach.get_animated_pose(ex, int(time.time()*1000), user_progress=demo_phase)
            
            # Draw User Skeleton
            sk_color = (0, 255, 136) if is_form_correct else (0, 61, 255)
            frame = engine.draw_landmarks(frame, results, color=sk_color)
            
            # Render Coach
            coach_canvas = np.zeros((h, w, 3), dtype=np.uint8)
            # 3D Grid Floor
            cx, cy = w // 2, h * 3 // 4
            for i in range(-5, 6):
                cv2.line(coach_canvas, (cx + i*40, cy), (cx + i*150, h), (40, 40, 40), 1)
            cv2.line(coach_canvas, (0, cy), (w, cy), (60, 60, 60), 2)
            
            coach.render(coach_canvas, target_pose, color=(0, 255, 255))
            
            # HUD Alerts
            if not is_form_correct:
                cv2.rectangle(frame, (50, h - 120), (w - 50, h - 40), (0, 0, 0), -1)
                cv2.rectangle(frame, (50, h - 120), (w - 50, h - 40), (0, 61, 255), 2)
                cv2.putText(frame, feedback_msg, (70, h - 65), cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 61, 255), 2)

            # Stack 
            canvas[:, :w] = frame
            canvas[:, w:] = coach_canvas
            canvas = ui.render_hud(canvas, ex, counter, is_form_correct, depth_percent)

        else:
            # No body detected
            coach_canvas = np.zeros((h, w, 3), dtype=np.uint8)
            canvas[:, :w] = frame
            canvas[:, w:] = coach_canvas
            cv2.putText(canvas, "NO BODY DETECTED", (w//2 - 150, h//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 150), 2)

        cv2.imshow('AI Physiotherapy Assistant', canvas)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'): break
        elif ord('1') <= key <= ord('8'):
            current_idx = key - ord('1')
            template = load_template(current_idx)
            counter = 0; rep_has_bottomed = False


    cap.release(); cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
