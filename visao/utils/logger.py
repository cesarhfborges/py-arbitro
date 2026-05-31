import json
import os

class AppLogger:
    def __init__(self):
        self.log_file = "app_debug.log"
        self.debug_enabled = False
        
    def reload_config(self):
        try:
            with open("config/settings.json", 'r', encoding='utf-8') as f:
                settings = json.load(f)
                self.debug_enabled = settings.get("debug", False)
        except Exception:
            pass
            
    def init_log(self):
        self.reload_config()
        if self.debug_enabled:
            with open(self.log_file, "w", encoding='utf-8') as f:
                f.write("=== LOG DE DEBUG INICIADO ===\n")
                
    def log(self, message):
        if self.debug_enabled:
            try:
                with open(self.log_file, "a", encoding='utf-8') as f:
                    f.write(message + "\n")
                print(f"[DEBUG] {message}", flush=True)
            except:
                pass

logger = AppLogger()
