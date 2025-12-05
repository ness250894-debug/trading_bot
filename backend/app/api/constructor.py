"""
Constructor API - Admin endpoints for UI configuration management.
Allows admins to customize UI elements, text, colors, and layouts.
"""

import json
import os
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import get_current_admin_user

router = APIRouter(prefix="/constructor", tags=["constructor"])

# Path to the UI configuration file
CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ui-config.json")

# Default config if file doesn't exist
DEFAULT_CONFIG = {
    "branding": {
        "appName": "TradingBot Pro",
        "tagline": "Smart Crypto Trading",
        "logoUrl": None
    },
    "theme": {
        "primaryColor": "#8b5cf6",
        "accentColor": "#10b981"
    },
    "pages": {},
    "widgets": {},
    "tables": {},
    "labels": {}
}


class ConfigUpdate(BaseModel):
    """Model for config update requests"""
    config: Dict[str, Any]


class ConfigPathUpdate(BaseModel):
    """Model for updating a specific config path"""
    path: str  # e.g., "pages.landing.heroTitle"
    value: Any


def load_config() -> Dict[str, Any]:
    """Load UI configuration from file"""
    try:
        if os.path.exists(CONFIG_FILE_PATH):
            with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return DEFAULT_CONFIG.copy()
    except Exception as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> bool:
    """Save UI configuration to file"""
    try:
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def get_nested_value(data: Dict, path: str) -> Any:
    """Get a nested value from a dict using dot notation"""
    keys = path.split('.')
    result = data
    for key in keys:
        if isinstance(result, dict) and key in result:
            result = result[key]
        else:
            return None
    return result


def set_nested_value(data: Dict, path: str, value: Any) -> Dict:
    """Set a nested value in a dict using dot notation"""
    keys = path.split('.')
    current = data
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value
    return data


@router.get("/config")
async def get_config():
    """
    Get the current UI configuration.
    Public endpoint - anyone can read the config for rendering.
    """
    return load_config()


@router.put("/config")
async def update_full_config(
    update: ConfigUpdate,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Replace the entire UI configuration.
    Admin only.
    """
    if save_config(update.config):
        return {"success": True, "message": "Configuration saved"}
    raise HTTPException(status_code=500, detail="Failed to save configuration")


@router.patch("/config")
async def update_config_path(
    update: ConfigPathUpdate,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Update a specific path in the UI configuration.
    Uses dot notation (e.g., "pages.landing.heroTitle").
    Admin only.
    """
    config = load_config()
    config = set_nested_value(config, update.path, update.value)
    
    if save_config(config):
        return {
            "success": True,
            "message": f"Updated {update.path}",
            "value": update.value
        }
    raise HTTPException(status_code=500, detail="Failed to save configuration")


@router.get("/config/{section}")
async def get_config_section(section: str):
    """
    Get a specific section of the UI configuration.
    Public endpoint.
    """
    config = load_config()
    if section in config:
        return config[section]
    raise HTTPException(status_code=404, detail=f"Section '{section}' not found")


@router.put("/config/{section}")
async def update_config_section(
    section: str,
    data: Dict[str, Any],
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Update a specific section of the UI configuration.
    Admin only.
    """
    config = load_config()
    config[section] = data
    
    if save_config(config):
        return {"success": True, "message": f"Section '{section}' updated"}
    raise HTTPException(status_code=500, detail="Failed to save configuration")


@router.post("/reset")
async def reset_config(
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Reset UI configuration to defaults.
    Admin only.
    """
    # Read the original config file if it exists as a template
    default_path = os.path.join(os.path.dirname(__file__), "ui-config.default.json")
    
    if os.path.exists(default_path):
        with open(default_path, 'r', encoding='utf-8') as f:
            default_config = json.load(f)
    else:
        default_config = DEFAULT_CONFIG
    
    if save_config(default_config):
        return {"success": True, "message": "Configuration reset to defaults"}
    raise HTTPException(status_code=500, detail="Failed to reset configuration")
