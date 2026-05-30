import json
import os

class AppState:
    def __init__(self):
        self.current_step = 1
        self.image_path = None
        self.video_path = None
        self.current_frame = None
        self.homography_points = []
        self.attacker_line_y = None
        self.defender_line_y = None
        
        self.settings_file = os.path.join("config", "settings.json")
        self.settings = self.load_settings()

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "theme": "auto",
            "attacker_line_color": "#FF0000",
            "defender_line_color": "#0000FF",
            "logo_path": "",
            "multi_window_enabled": True
        }

    def save_settings(self):
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        with open(self.settings_file, "w") as f:
            json.dump(self.settings, f, indent=4)
