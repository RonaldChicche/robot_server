import json
import os

class RedisKeyMap:
    def __init__(self, folder_path="web/config/redis_keys"):
        self.map = {}
        for filename in os.listdir(folder_path):
            if filename.endswith(".json"):
                with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.map.update(data)

    def get(self, key_name, **kwargs):
        if key_name not in self.map:
            raise KeyError(f"Clave Redis '{key_name}' no encontrada.")
        try:
            return self.map[key_name]["template"].format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Falta argumento para la clave '{key_name}': {e}")

    def ttl(self, key_name):
        return self.map.get(key_name, {}).get("ttl")

    def description(self, key_name):
        return self.map.get(key_name, {}).get("description", "")
