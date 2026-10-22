import json
import os
from pathlib import Path


def load_local_settings(app_data_dir=None):
    if app_data_dir is None:
        app_data_dir = os.environ.get("LOCALAPPDATA")
    if not app_data_dir:
        return {}

    config_path = (
        Path(app_data_dir)
        / "CortinasPersianas"
        / "config"
        / "notifications.json"
    )
    if not config_path.exists():
        return {}

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "No se pudo leer la configuración local de notificaciones."
        ) from exc

    if not isinstance(config, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in config.items()
    ):
        raise RuntimeError(
            "La configuración local de notificaciones debe ser un objeto "
            "JSON con valores de texto."
        )
    return config


def apply_local_settings(settings, environment=None):
    target = os.environ if environment is None else environment
    for setting_name, setting_value in settings.items():
        if not target.get(setting_name):
            target[setting_name] = setting_value
