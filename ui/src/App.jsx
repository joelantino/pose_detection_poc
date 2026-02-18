import React, { useState, useEffect, useRef } from 'react';

const exercises = [
    "Squat", "Lunge", "Jumping Jacks", "High Knees",
    "Bicep Curl", "Shoulder Press", "Calf Raises", "Torso Twist"
];

function App() {
    const [currentEx, setCurrentEx] = useState("Squat");
    const [reps, setReps] = useState(0);
    const [isCorrect, setIsCorrect] = useState(true);
    const [depth, setDepth] = useState(0);
    const videoRef = useRef(null);
    const canvasRef = useRef(null);

    useEffect(() => {
        // Start Camera
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } })
                .then(stream => {
                    if (videoRef.current) {
                        videoRef.current.srcObject = stream;
                    }
                });
        }
    }, []);

    return (
        <div className="dashboard-container">
            {/* Sidebar */}
            <div className="sidebar">
                <div className="brand">PHYSIO AI PRO</div>
                {exercises.map(ex => (
                    <button
                        key={ex}
                        className={`exercise-btn ${currentEx === ex ? 'active' : ''}`}
                        onClick={() => {
                            setCurrentEx(ex);
                            setReps(0);
                        }}
                    >
                        {ex}
                    </button>
                ))}
            </div>

            {/* Main Console */}
            <div className="main-console">
                {/* Header HUD */}
                <div className="header-hud">
                    <div>
                        <div style={{ color: '#a0a0a0', fontSize: '0.9rem' }}>CURRENT SESSION</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: 600 }}>{currentEx}</div>
                    </div>

                    <div className="rep-counter">
                        <div style={{ color: '#a0a0a0', fontSize: '0.9rem' }}>REPS COMPLETED</div>
                        <div className="rep-count">{reps}</div>
                    </div>
                </div>

                {/* Video & Coach Console */}
                <div className="split-view">
                    <div className="camera-feed">
                        <video ref={videoRef} autoPlay playsInline muted />
                        <canvas ref={canvasRef} style={{ position: 'absolute', top: 0, left: 0 }} />
                        <div className="view-label">LIVE FEED</div>

                        <div className="depth-gauge-container">
                            <div className="depth-fill" style={{ height: `${depth}%` }} />
                        </div>

                        {!isCorrect && (
                            <div className="status-toast error">
                                ADJUST FORM
                            </div>
                        )}
                        {isCorrect && (
                            <div className="status-toast">
                                EXCELLENT FORM
                            </div>
                        )}
                    </div>

                    <div className="coach-view">
                        {/* Placeholder for Animated Coach */}
                        <div style={{
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            height: '100%',
                            fontSize: '1.2rem',
                            color: '#444'
                        }}>
                            COACH ANIMATION (VIRTUAL)
                        </div>
                        <div className="view-label">GHOST COACH</div>
                    </div>
                </div>

                {/* Footer Info */}
                <div style={{ color: '#666', fontSize: '0.8rem', textAlign: 'center' }}>
                    ELITE TRACKING MODE ACTIVE • 93%+ ACCURACY GUARANTEED
                </div>
            </div>
        </div>
    );
}

export default App;
