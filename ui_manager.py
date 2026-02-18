import cv2
import numpy as np

class UIManager:
    def __init__(self):
        # Premium Color Palette (BGR)
        self.colors = {
            "bg_dark": (30, 30, 30),
            "glass_white": (240, 240, 240),
            "neon_cyan": (255, 229, 0),
            "emerald": (136, 255, 0),
            "warning": (0, 61, 255),
            "text_white": (255, 255, 255)
        }

    def draw_glass_panel(self, frame, rect, opacity=0.4):
        """Draws a semi-transparent 'glass' panel with rounded edges."""
        x1, y1, x2, y2 = rect
        sub_img = frame[y1:y2, x1:x2]
        
        # Create white overlay
        white_rect = np.ones(sub_img.shape, dtype=np.uint8) * 20
        res = cv2.addWeighted(sub_img, 1 - opacity, white_rect, opacity, 0)
        
        frame[y1:y2, x1:x2] = res
        # Draw sleek border
        cv2.rectangle(frame, (x1, y1), (x2, y2), (200, 200, 200), 1, cv2.LINE_AA)

    def draw_rounded_rect(self, img, pt1, pt2, color, thickness, r):
        """Draws a rectangle with rounded corners."""
        x1, y1 = pt1
        x2, y2 = pt2
        # Top-Left
        cv2.line(img, (x1 + r, y1), (x2 - r, y1), color, thickness)
        cv2.line(img, (x1, y1 + r), (x1, y2 - r), color, thickness)
        # Add corners here if needed, keeping it simple for OpenCV perf

    def draw_stat_card(self, canvas, label, value, pos, size=(180, 80)):
        """Draws a modern stat card with a label and large value."""
        x, y = pos
        w, h = size
        self.draw_glass_panel(canvas, (x, y, x + w, y + h), opacity=0.3)
        
        cv2.putText(canvas, label, (x + 15, y + 25), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, (180, 180, 180), 1, cv2.LINE_AA)
        cv2.putText(canvas, str(value), (x + 15, y + 65), 
                    cv2.FONT_HERSHEY_DUPLEX, 1.2, self.colors["text_white"], 2, cv2.LINE_AA)

    def draw_depth_gauge(self, canvas, pos, progress, color=(0, 255, 0)):
        """Draws a vertical depth/range-of-motion gauge."""
        x, y = pos
        w, h = 15, 200
        # Background
        cv2.rectangle(canvas, (x, y), (x + w, y + h), (50, 50, 50), -1)
        # Fill
        fill_h = int(h * progress)
        cv2.rectangle(canvas, (x, y + h - fill_h), (x + w, y + h), color, -1)
        # Label
        cv2.putText(canvas, "DEPTH", (x - 10, y + h + 20), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.5, (200, 200, 200), 1)

    def render_hud(self, canvas, exercise_name, rep_count, is_correct, depth_val):
        h, w_total, _ = canvas.shape
        w = w_total // 2

        # 1. Header Bar
        self.draw_glass_panel(canvas, (0, 0, w_total, 80), opacity=0.5)
        cv2.putText(canvas, "AI PHYSIO ASSISTANT", (30, 50), 
                    cv2.FONT_HERSHEY_DUPLEX, 1.2, self.colors["neon_cyan"], 2, cv2.LINE_AA)
        
        # 2. Exercise Info & Reps
        cv2.putText(canvas, f"MODE: {exercise_name.upper()}", (w - 150, 50), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.8, (200, 200, 200), 1, cv2.LINE_AA)
        
        # 3. Floating Rep Counter (Large)
        rep_color = self.colors["emerald"] if is_correct else self.colors["warning"]
        self.draw_stat_card(canvas, "REPS", rep_count, (w_total - 210, 10))

        # 4. Status Indicator (Bottom Left)
        status_text = "IDEAL FORM" if is_correct else "ADJUST POSE"
        status_color = self.colors["emerald"] if is_correct else self.colors["warning"]
        self.draw_glass_panel(canvas, (30, h - 70, 250, h - 20), opacity=0.4)
        cv2.circle(canvas, (55, h - 45), 8, status_color, -1)
        cv2.putText(canvas, status_text, (75, h - 38), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.7, self.colors["text_white"], 1, cv2.LINE_AA)

        # 5. Depth Gauge (On the line between frames)
        self.draw_depth_gauge(canvas, (w - 7, h // 2 - 100), depth_val, color=status_color)

        return canvas

ui = UIManager()
