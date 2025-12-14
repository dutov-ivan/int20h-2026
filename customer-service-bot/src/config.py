from pathlib import Path
from typing import Dict, Optional


# Path to project root (two levels up from this file: src/ -> project root)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = PROJECT_ROOT / "config.yaml"


def _ensure_config_exists(path: Path) -> None:
	if not path.exists():
		# create a simple empty YAML with the expected keys
		path.write_text("""bot_token: ''
chat_id: ''
api_id: ''
api_key: ''
""", encoding="utf-8")


def _load_yaml(path: Path) -> Dict[str, Optional[str]]:
	try:
		import yaml  # PyYAML
	except Exception as e:  # pragma: no cover - runtime/import error
		raise RuntimeError("PyYAML is required for YAML parsing. Install with `pip install pyyaml`")

	with path.open("r", encoding="utf-8") as fh:
		data = yaml.safe_load(fh) or {}
	return data


def load_config() -> Dict[str, Optional[str]]:
	"""Ensure `config.yaml` exists, load it, and return a dict with keys:
	`bot_token`, `chat_id`, `api_id`, `api_key`.
	Missing keys will have value `None`.
	"""
	_ensure_config_exists(CONFIG_FILE)
	data = _load_yaml(CONFIG_FILE)

	return {
		"bot_token": data.get("bot_token"),
		"chat_id": data.get("chat_id"),
		"api_id": data.get("api_id"),
		"api_key": data.get("api_key"),
	}


# Load on import for convenience
_cfg = load_config()

BOT_TOKEN = _cfg.get("bot_token")
CHAT_ID = _cfg.get("chat_id")
API_ID = _cfg.get("api_id")
API_KEY = _cfg.get("api_key")

__all__ = ["load_config", "BOT_TOKEN", "CHAT_ID", "API_ID", "API_KEY"]


def save_config(updates: Dict[str, Optional[str]]) -> None:
	"""Persist configuration updates to `config.yaml`.

	- `updates` may include any of the keys: `bot_token`, `chat_id`, `api_id`, `api_key`.
	- Values of `None` are written as an empty string in the YAML file to keep
	  the file simple and consistent with the initial template.
	- After writing the file, the module-level cached values are refreshed so
	  callers can rely on the updated `BOT_TOKEN`, `CHAT_ID`, etc.
	"""
	_ensure_config_exists(CONFIG_FILE)

	try:
		import yaml
	except Exception:  # pragma: no cover - runtime/import
		raise RuntimeError("PyYAML is required to write config. Install with `pip install pyyaml`")

	# Load existing values and merge
	current = _load_yaml(CONFIG_FILE) or {}
	keys = ("bot_token", "chat_id", "api_id", "api_key")
	new_data = {}
	for k in keys:
		if k in updates:
			# Normalize None -> empty string for file
			v = updates[k]
			new_data[k] = "" if v is None else str(v)
		else:
			# Keep existing; normalize None -> empty string
			v = current.get(k)
			new_data[k] = "" if v is None else str(v)

	# Write YAML with stable ordering
	with CONFIG_FILE.open("w", encoding="utf-8") as fh:
		yaml.safe_dump(new_data, fh, default_flow_style=False, sort_keys=False)

	# Refresh module-level cache
	_refresh_module_vars()


def _refresh_module_vars() -> None:
	"""Reload config from disk and update module-level variables.

	Call this after `save_config` so other modules importing these
	names get the updated values.
	"""
	global _cfg, BOT_TOKEN, CHAT_ID, API_ID, API_KEY
	_cfg = load_config()
	BOT_TOKEN = _cfg.get("bot_token")
	CHAT_ID = _cfg.get("chat_id")
	API_ID = _cfg.get("api_id")
	API_KEY = _cfg.get("api_key")

__all__ = ["load_config", "save_config", "_refresh_module_vars", "BOT_TOKEN", "CHAT_ID", "API_ID", "API_KEY"]