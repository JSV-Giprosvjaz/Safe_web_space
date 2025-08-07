import os
import json
import streamlit as st
from typing import Dict, Any

# Путь к файлу настроек
SETTINGS_FILE = "settings.json"

# Определение переменных окружения для продакшена
ENV_VARIABLES = {
    "youtube_api_key": "YOUTUBE_API_KEY",
    "telegram_api_id": "TELEGRAM_API_ID", 
    "telegram_api_hash": "TELEGRAM_API_HASH",
    "telegram_bot_token": "TELEGRAM_BOT_TOKEN",
    "telegram_phone": "TELEGRAM_PHONE"
}

def is_production() -> bool:
    """Определяет, запущено ли приложение в продакшене"""
    # Проверяем наличие переменной окружения, которая обычно устанавливается в продакшене
    return os.getenv("STREAMLIT_SERVER_ENV") == "production" or os.getenv("DEPLOYMENT_ENV") == "production"

def load_settings_from_env() -> Dict[str, str]:
    """Загружает настройки из переменных окружения"""
    settings = {}
    for setting_key, env_var in ENV_VARIABLES.items():
        value = os.getenv(env_var, "")
        if value:
            settings[setting_key] = value
    return settings

def load_settings_from_file() -> Dict[str, str]:
    """Загружает настройки из файла"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Ошибка загрузки настроек из файла: {e}")
    return {}

def save_settings_to_file(settings: Dict[str, str]) -> bool:
    """Сохраняет настройки в файл"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Ошибка сохранения настроек в файл: {e}")
        return False

def load_settings() -> Dict[str, str]:
    """Загружает настройки в зависимости от окружения"""
    if is_production():
        # В продакшене используем переменные окружения
        return load_settings_from_env()
    else:
        # Локально используем файл настроек
        return load_settings_from_file()

def save_settings(settings: Dict[str, str]) -> bool:
    """Сохраняет настройки в зависимости от окружения"""
    if is_production():
        # В продакшене нельзя сохранять настройки через интерфейс
        st.warning("⚠️ В продакшене настройки управляются через переменные окружения")
        return False
    else:
        # Локально сохраняем в файл
        return save_settings_to_file(settings)

def get_setting(key: str, default: str = "") -> str:
    """Получает значение настройки"""
    settings = load_settings()
    return settings.get(key, default)

def get_all_settings() -> Dict[str, str]:
    """Получает все настройки"""
    return load_settings()

def is_setting_configured(key: str) -> bool:
    """Проверяет, настроен ли параметр"""
    value = get_setting(key)
    return bool(value and value.strip())

def get_environment_info() -> Dict[str, Any]:
    """Возвращает информацию об окружении"""
    return {
        "is_production": is_production(),
        "settings_source": "environment_variables" if is_production() else "settings_file",
        "settings_file_path": SETTINGS_FILE if not is_production() else None,
        "environment_variables": {key: bool(os.getenv(env_var)) for key, env_var in ENV_VARIABLES.items()}
    } 