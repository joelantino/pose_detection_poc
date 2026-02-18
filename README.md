# AI Physiotherapy Assistant - Dynamic Stickman Guidance System

This is a Proof of Concept (PoC) for a real-time AI Physiotherapist that guides users through exercises (specifically squats) using a "Ghost Stickman" coach and dynamic visual feedback.

## Features
- **Real-time Pose Detection**: Powered by MediaPipe BlazePose.
- **Ghost Coach**: A semi-transparent overlay demonstrating the ideal posture.
- **Dynamic Correction (Elite Level)**: The ghost stickman adjusts its position based on the user's mistakes to lead them toward the correct posture.
- **Visual Feedback**: Skeleton color changes from Red (incorrect) to Green (correct) based on joint angles. No text coaching.
- **Modular Architecture**: Clean separation between pose detection, biomechanics, and rendering.

## Project Structure
```text
physio_ai_poc/
│
├── main.py                # Entry point & Orchestration
├── pose_engine.py         # MediaPipe Pose Detection wrapper
├── biomechanics.py        # Logic for angles & joint calculations
├── ghost_coach.py         # Rendering logic for the Ghost Stickman
├── correction_engine.py   # Elite Level: Dynamic adjustment logic
├── templates/
│   └── squat.json         # Exercise targets for Squats
├── utils.py               # Helper functions for rendering
└── requirements.txt       # Python dependencies
```

## Setup Instructions

1. **Install Dependencies**:
   Ensure you have Python installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   Execute the main script:
   ```bash
   python main.py
   ```

## How It Works (The Pipeline)
1. **Camera Feed**: Captures real-time video via OpenCV.
2. **Pose Inference**: MediaPipe BlazePose extracts 33 body landmarks.
3. **Biomechanics Analysis**: The system calculates the user's knee and hip angles.
4. **Validation**: Compares current angles with the target angles in `templates/squat.json`.
5. **Correction Logic**: 
   - If the user is out of range, the user's skeleton turns **Red**.
   - If the user is within range, the user's skeleton turns **Green**.
6. **Dynamic Guidance**: The `CorrectionEngine` calculates the "error vector" and shifts the Ghost Stickman to encourage the user to move in the right direction (e.g., squatting deeper).

## Future Upgrade Path (Advanced AI Roadmap)
- **ELITE+**: Implement a temporal transformer to analyze the *rhythm* and *tempo* of the exercise.
- **Biometric Integration**: Connect with health APIs to track heart rate and fatigue.
- **Voice Feedback (Optional Toggle)**: Context-aware audio cues using Text-to-Speech.
- **3D Visualization**: Use Three.js or similar for a full 3D interactive coach view in a web browser.
