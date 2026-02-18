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
        "bicep_curl", "shoulder_press", "calf_raises", "torso_twist"
    ]
    current_idx = 0
    
    def load_template(idx):
        try:
            with open(f'templates/{exercises[idx]}.json', 'r') as f:
                return json.load(f)
        except:
            return {"target_angles": {"knee_angle": 100}, "tolerance": 20}

    template = load_template(current_idx)
    
    # State Machine V3 (STRICT ISOLATION)
    # Using a state dict to prevent leakage between exercises
    state_tracker = {ex: {"counter": 0, "bottomed": False, "last_rep_time": 0} for ex in exercises}
    
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
            st = state_tracker[ex]
            
            # --- ULTIMATE ISOLATION: Wipe background states ---
            # This prevents any movement while in one "tab" from ever being remembered by another
            for other_ex in exercises:
                if other_ex != ex:
                    state_tracker[other_ex]["bottomed"] = False
            
            # --- 1. INITIALIZE & CALCULATE METRICS ---
            knee_val = (angles.get('left_knee', 180) + angles.get('right_knee', 180)) / 2
            hip_val = (angles.get('left_hip', 180) + angles.get('right_hip', 180)) / 2
            
            l_sh = calculate_angle(landmarks[23][:2], landmarks[11][:2], landmarks[13][:2])
            r_sh = calculate_angle(landmarks[24][:2], landmarks[12][:2], landmarks[14][:2])
            arm_val = (l_sh + r_sh) / 2
            
            feedback_msg = "PERFECT FORM"
            is_form_correct = True
            
            # --- 2. VISIBILITY & FORM CHECK ---
            seated_exercises = ["bicep_curl", "shoulder_press", "torso_twist"]
            if ex in seated_exercises:
                vis_points = [11, 12, 13, 14, 15, 16] # Just upper body
            else:
                vis_points = [23, 24, 25, 26, 27, 28] # Critical lower body
                
            full_body_vis = all(landmarks[i][3] > 0.6 for i in vis_points)
            
            if not full_body_vis:
                is_form_correct = False
                feedback_msg = "ADJUST VIEW ->" if ex in seated_exercises else "STEP BACK ->"
                st["bottomed"] = False
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

                elif ex == "bicep_curl":
                    l_el = calculate_angle(landmarks[11][:2], landmarks[13][:2], landmarks[15][:2])
                    r_el = calculate_angle(landmarks[12][:2], landmarks[14][:2], landmarks[16][:2])
                    
                    # Movement Authentication: Wrists MUST stay below shoulders for a curl
                    wrist_below = landmarks[15][1] > landmarks[11][1] and landmarks[16][1] > landmarks[12][1]
                    if not wrist_below:
                        feedback_msg = "KEEP HANDS BELOW SHOULDERS"; is_form_correct = False
                    elif abs(l_el - r_el) > 40:
                        feedback_msg = "SYNC BOTH ARMS!"; is_form_correct = False
                        
                elif ex == "shoulder_press":
                    l_el_ang = calculate_angle(landmarks[11][:2], landmarks[13][:2], landmarks[15][:2])
                    r_el_ang = calculate_angle(landmarks[12][:2], landmarks[14][:2], landmarks[16][:2])
                    elbow_avg = (l_el_ang + r_el_ang) / 2
                    
                    # BIOMETRIC ZONE: In a press, ELBOWS must be at or above shoulder level
                    # This prevents Bicep Curls (elbows at ribs) from being detected here
                    l_elbow_y, r_elbow_y = landmarks[13][1], landmarks[14][1]
                    sh_y = (landmarks[11][1] + landmarks[12][1]) / 2
                    
                    if l_elbow_y > sh_y + 0.05 or r_elbow_y > sh_y + 0.05:
                        feedback_msg = "RAISE ELBOWS TO SHOULDER LEVEL"; is_form_correct = False
                    elif abs(l_el_ang - r_el_ang) > 45:
                        feedback_msg = "SYNC BOTH ARMS!"; is_form_correct = False
                
                elif ex == "lunge":
                    active_knee = min(angles.get('left_knee', 180), angles.get('right_knee', 180))
                    # Lunge should have a significant knee bend
                    if active_knee > 160 and depth_percent > 0.1:
                        feedback_msg = "GO DEEPER!"; is_form_correct = False
                    # Check for chest leaning forward too much
                    torso_tilt = abs(landmarks[11][0] - landmarks[23][0])
                    if torso_tilt > 0.12:
                        feedback_msg = "KEEP CHEST UP"; is_form_correct = False

            
            # --- 3. REP COUNTING (STRICT ISOLATION) ---
            if ex == "squat":
                if knee_val < 135 and is_form_correct: st["bottomed"] = True
                elif knee_val > 165 and st["bottomed"]:
                    if is_form_correct and (time.time() - st["last_rep_time"] > 1.5):
                        st["counter"] += 1
                        st["last_rep_time"] = time.time()
                    st["bottomed"] = False
                depth_percent = np.clip((170 - knee_val) / 60, 0, 1)

            elif ex == "jumping_jacks":
                if arm_val > 140 and is_form_correct: st["bottomed"] = True
                elif arm_val < 60 and st["bottomed"]:
                    if is_form_correct and (time.time() - st["last_rep_time"] > 1.0):
                        st["counter"] += 1
                        st["last_rep_time"] = time.time()
                    st["bottomed"] = False
                depth_percent = np.clip((arm_val - 40) / 110, 0, 1)

            elif ex == "high_knees":
                active_hip = max(180 - angles.get('left_hip', 180), 180 - angles.get('right_hip', 180))
                if active_hip > 70 and is_form_correct: st["bottomed"] = True
                elif active_hip < 30 and st["bottomed"]:
                    if is_form_correct and (time.time() - st["last_rep_time"] > 1.0):
                        st["counter"] += 1
                        st["last_rep_time"] = time.time()
                    st["bottomed"] = False
                depth_percent = np.clip(active_hip / 70, 0, 1)

            elif ex == "bicep_curl":
                l_el = calculate_angle(landmarks[11][:2], landmarks[13][:2], landmarks[15][:2])
                r_el = calculate_angle(landmarks[12][:2], landmarks[14][:2], landmarks[16][:2])
                elbow_avg = (l_el + r_el) / 2
                depth_percent = np.clip((155 - elbow_avg) / 80, 0, 1)
                
                # Double check hands are below shoulders (to block Press leakage)
                wrist_below = landmarks[15][1] > landmarks[11][1] and landmarks[16][1] > landmarks[12][1]
                
                if elbow_avg < 95 and is_form_correct and wrist_below: 
                    st["bottomed"] = True
                elif elbow_avg > 145 and st["bottomed"]:
                    if is_form_correct and (time.time() - st["last_rep_time"] > 1.2):
                        st["counter"] += 1
                        st["last_rep_time"] = time.time()
                    st["bottomed"] = False

            elif ex == "shoulder_press":
                l_el_ang = calculate_angle(landmarks[11][:2], landmarks[13][:2], landmarks[15][:2])
                r_el_ang = calculate_angle(landmarks[12][:2], landmarks[14][:2], landmarks[16][:2])
                elbow_avg = (l_el_ang + r_el_ang) / 2
                
                # Height Authentication: Highest point (wrist) must definitely be above shoulder
                sh_y = (landmarks[11][1] + landmarks[12][1]) / 2
                highest_wrist_y = min(landmarks[15][1], landmarks[16][1])
                overhead_clearance = sh_y - highest_wrist_y
                
                # Depth gauge based on how close elbows are to full extension (100 to 160)
                depth_percent = np.clip((elbow_avg - 100) / 60, 0, 1)
                
                # TRIGGER TOP: Arms straightening + Hands Overhead
                if elbow_avg > 145 and overhead_clearance > 0.1 and is_form_correct:
                    st["bottomed"] = True
                
                # TRIGGER COMPLETION: Arms return to 'bent' state near ears
                elif elbow_avg < 115 and st["bottomed"]:
                    if time.time() - st["last_rep_time"] > 1.2:
                        st["counter"] += 1
                        st["last_rep_time"] = time.time()
                    st["bottomed"] = False

            elif ex == "lunge":
                active_knee = min(angles.get('left_knee', 180), angles.get('right_knee', 180))
                if active_knee < 120 and is_form_correct: st["bottomed"] = True
                elif active_knee > 165 and st["bottomed"]:
                    if is_form_correct and (time.time() - st["last_rep_time"] > 1.8):
                        st["counter"] += 1
                        st["last_rep_time"] = time.time()
                    st["bottomed"] = False
                depth_percent = np.clip((175 - active_knee) / 60, 0, 1)

            elif ex == "calf_raises":
                curr_y = landmarks[11][1]
                if not hasattr(main, "base_y") or main.base_y == 0: main.base_y = curr_y
                diff = main.base_y - curr_y
                if diff > 0.04 and is_form_correct: st["bottomed"] = True
                elif diff < 0.01 and st["bottomed"]:
                    if is_form_correct and (time.time() - st["last_rep_time"] > 1.2):
                        st["counter"] += 1
                        st["last_rep_time"] = time.time()
                    st["bottomed"] = False
                depth_percent = np.clip(diff / 0.08, 0, 1)

            elif ex == "torso_twist":
                w_val = abs(landmarks[11][0] - landmarks[12][0])
                if w_val < 0.10 and is_form_correct: st["bottomed"] = True
                elif w_val > 0.15 and st["bottomed"]:
                    if is_form_correct and (time.time() - st["last_rep_time"] > 1.2):
                        st["counter"] += 1
                        st["last_rep_time"] = time.time()
                    st["bottomed"] = False
                depth_percent = 0.5

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
            canvas = ui.render_hud(canvas, ex, st["counter"], is_form_correct, depth_percent)

        else:
            # No body detected
            coach_canvas = np.zeros((h, w, 3), dtype=np.uint8)
            canvas[:, :w] = frame
            canvas[:, w:] = coach_canvas
            cv2.putText(canvas, "NO BODY DETECTED", (w//2 - 150, h//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 150), 2)

        cv2.imshow('AI Physiotherapy Assistant', canvas)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'): break
        elif ord('1') <= key <= ord('9') or key == ord('0'):
            idx = 9 if key == ord('0') else (key - ord('1'))
            if idx < len(exercises):
                current_idx = idx
                template = load_template(current_idx)
                # RESET current rep state when switching to prevent leakage
                state_tracker[exercises[current_idx]]["bottomed"] = False
                if hasattr(main, "base_y"): del main.base_y


    cap.release(); cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
