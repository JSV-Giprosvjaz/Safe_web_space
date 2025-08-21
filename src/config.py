import streamlit as st
import toml
import os
from typing import Dict, Any

# Определение ключей настроек в Streamlit Secrets
SETTINGS_KEYS = {
    "youtube_api_key": "youtube_api_key",
    "telegram_api_id": "telegram_api_id", 
    "telegram_api_hash": "telegram_api_hash",
    "telegram_bot_token": "telegram_bot_token",
    "telegram_phone": "telegram_phone"
}

def ensure_secrets_file_exists():
    """Создает файл secrets.toml если он не существует"""
    secrets_file = ".streamlit/secrets.toml"
    
    # Создаем директорию .streamlit если её нет
    os.makedirs(".streamlit", exist_ok=True)
    
    # Если файл не существует, создаем его с дефолтными значениями
    if not os.path.exists(secrets_file):
        default_secrets = {
            "debug": True,  # Включаем режим отладки по умолчанию
            # Добавляем пустые значения для всех настроек
            **{key: "" for key in SETTINGS_KEYS.keys()}
        }
        
        try:
            with open(secrets_file, 'w', encoding='utf-8') as f:
                toml.dump(default_secrets, f)
            print(f"✅ Создан файл secrets.toml: {os.path.abspath(secrets_file)}")
        except Exception as e:
            print(f"❌ Ошибка создания secrets.toml: {e}")

def load_settings() -> Dict[str, str]:
    """Загружает настройки из Streamlit Secrets"""
    # Убеждаемся, что файл secrets существует
    ensure_secrets_file_exists()
    
    settings = {}
    for setting_key, secret_key in SETTINGS_KEYS.items():
        value = st.secrets.get(secret_key, "")
        if value:
            settings[setting_key] = str(value)
    return settings

def is_debug_mode() -> bool:
    """Проверяет, включен ли режим отладки"""
    # Убеждаемся, что файл secrets существует
    ensure_secrets_file_exists()
    return st.secrets.get("debug", False)

def save_settings_to_secrets_file(settings: Dict[str, str]) -> bool:
    """Сохраняет настройки в файл .streamlit/secrets.toml"""
    try:
        secrets_file = ".streamlit/secrets.toml"
        
        # Загружаем существующие secrets
        existing_secrets = {}
        if os.path.exists(secrets_file):
            with open(secrets_file, 'r', encoding='utf-8') as f:
                existing_secrets = toml.load(f)
        
        # Обновляем настройки
        for setting_key, value in settings.items():
            if setting_key in SETTINGS_KEYS:
                if value.strip():  # Сохраняем только непустые значения
                    existing_secrets[setting_key] = value
                elif setting_key in existing_secrets:
                    # Удаляем пустые значения
                    del existing_secrets[setting_key]
        
        # Сохраняем обратно в файл
        with open(secrets_file, 'w', encoding='utf-8') as f:
            toml.dump(existing_secrets, f)
        
        return True
    except Exception as e:
        st.error(f"Ошибка сохранения в secrets.toml: {e}")
        return False

def save_settings(settings: Dict[str, str]) -> bool:
    """Сохраняет настройки в Streamlit Secrets (только в режиме отладки)"""
    if not is_debug_mode():
        # В продакшене нельзя изменять настройки
        st.warning("⚠️ Настройки можно изменять только в режиме отладки (debug = True)")
        return False
    
    try:
        # В режиме отладки сохраняем в secrets.toml файл
        if save_settings_to_secrets_file(settings):
            st.success("✅ Настройки успешно сохранены в secrets.toml!")
            return True
        else:
            st.error("❌ Ошибка при сохранении настроек")
            return False
    except Exception as e:
        st.error(f"Ошибка сохранения настроек: {e}")
        return False

def get_setting(key: str, default: str = "") -> str:
    """Получает значение настройки из secrets"""
    # Убеждаемся, что файл secrets существует
    ensure_secrets_file_exists()
    
    secret_key = SETTINGS_KEYS.get(key, key)
    value = st.secrets.get(secret_key, default)
    return str(value) if value else default

def get_all_settings() -> Dict[str, str]:
    """Получает все настройки из secrets"""
    # Убеждаемся, что файл secrets существует
    ensure_secrets_file_exists()
    return load_settings()

def is_setting_configured(key: str) -> bool:
    """Проверяет, настроен ли параметр"""
    # Убеждаемся, что файл secrets существует
    ensure_secrets_file_exists()
    
    value = get_setting(key)
    return bool(value and value.strip())

def get_environment_info() -> Dict[str, Any]:
    """Возвращает информацию об окружении"""
    # Убеждаемся, что файл secrets существует
    ensure_secrets_file_exists()
    
    debug_mode = is_debug_mode()
    
    return {
        "is_production": not debug_mode,
        "settings_source": "streamlit_secrets",
        "debug_mode": debug_mode,
        "configured_secrets": {key: bool(st.secrets.get(secret_key)) for key, secret_key in SETTINGS_KEYS.items()}
    } 