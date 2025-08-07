import streamlit as st
from typing import Dict, Any

# Определение ключей настроек в Streamlit Secrets
SETTINGS_KEYS = {
    "youtube_api_key": "youtube_api_key",
    "telegram_api_id": "telegram_api_id", 
    "telegram_api_hash": "telegram_api_hash",
    "telegram_bot_token": "telegram_bot_token",
    "telegram_phone": "telegram_phone"
}

def load_settings() -> Dict[str, str]:
    """Загружает настройки из Streamlit Secrets"""
    settings = {}
    for setting_key, secret_key in SETTINGS_KEYS.items():
        value = st.secrets.get(secret_key, "")
        if value:
            settings[setting_key] = str(value)
    return settings

def save_settings(settings: Dict[str, str]) -> bool:
    """Сохраняет настройки в Streamlit Secrets (только для локальной разработки)"""
    # Проверяем, есть ли secrets в продакшене
    has_secrets = any(st.secrets.get(key) for key in SETTINGS_KEYS.values())
    
    if has_secrets:
        # В продакшене нельзя изменять настройки
        st.warning("⚠️ В продакшене настройки управляются через Streamlit Cloud Secrets")
        return False
    
    try:
        # В локальной разработке обновляем session_state
        for setting_key, value in settings.items():
            if setting_key in SETTINGS_KEYS:
                # Обновляем в session_state для текущей сессии
                if "temp_settings" not in st.session_state:
                    st.session_state.temp_settings = {}
                st.session_state.temp_settings[setting_key] = value
        return True
    except Exception as e:
        st.error(f"Ошибка сохранения настроек: {e}")
        return False

def get_setting(key: str, default: str = "") -> str:
    """Получает значение настройки из secrets или временных настроек"""
    # Сначала проверяем временные настройки (для локальной разработки)
    if "temp_settings" in st.session_state and key in st.session_state.temp_settings:
        return st.session_state.temp_settings[key]
    
    # Затем проверяем secrets
    secret_key = SETTINGS_KEYS.get(key, key)
    value = st.secrets.get(secret_key, default)
    return str(value) if value else default

def get_all_settings() -> Dict[str, str]:
    """Получает все настройки"""
    settings = load_settings()
    
    # Добавляем временные настройки из session_state
    if "temp_settings" in st.session_state:
        settings.update(st.session_state.temp_settings)
    
    return settings

def is_setting_configured(key: str) -> bool:
    """Проверяет, настроен ли параметр"""
    value = get_setting(key)
    return bool(value and value.strip())

def get_environment_info() -> Dict[str, Any]:
    """Возвращает информацию об окружении"""
    # Проверяем, есть ли secrets в продакшене
    has_secrets = any(st.secrets.get(key) for key in SETTINGS_KEYS.values())
    
    return {
        "is_production": has_secrets,
        "settings_source": "streamlit_secrets",
        "has_secrets": has_secrets,
        "configured_secrets": {key: bool(st.secrets.get(secret_key)) for key, secret_key in SETTINGS_KEYS.items()}
    }

def clear_temp_settings():
    """Очищает временные настройки"""
    if "temp_settings" in st.session_state:
        st.session_state.temp_settings = {} 