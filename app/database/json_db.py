import os
import json
import threading
from typing import List, Dict, Any
from app.config import settings

class JSONDatabase:
    def __init__(self):
        self.file_path = settings.absolute_data_file_path
        self._lock = threading.Lock()
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        with self._lock:
            dir_name = os.path.dirname(self.file_path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)
            if not os.path.exists(self.file_path):
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump([], f, indent=4)

    def read_all(self) -> List[Dict[str, Any]]:
        with self._lock:
            try:
                if not os.path.exists(self.file_path):
                    return []
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []

    def write_all(self, data: List[Dict[str, Any]]) -> None:
        with self._lock:
            # First write to a temporary file, then rename it, to prevent data corruption
            temp_file_path = f"{self.file_path}.tmp"
            try:
                with open(temp_file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                if os.path.exists(self.file_path):
                    os.remove(self.file_path)
                os.rename(temp_file_path, self.file_path)
            except Exception as e:
                if os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except:
                        pass
                raise e
