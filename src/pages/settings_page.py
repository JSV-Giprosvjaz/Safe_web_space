import streamlit as st
import json
import os

# Путь к файлу настроек
SETTINGS_FILE = "settings.json"

def clean_input(text):
    """Удаляет все пробелы из введенного текста"""
    return text.strip() if text else ""

def save_settings(settings):
    """Сохраняет настройки в файл"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Ошибка сохранения настроек: {e}")
        return False

st.header("⚙️ Настройки API")

st.markdown("### YouTube API")
st.markdown("Для парсинга комментариев из YouTube необходим API ключ.")

youtube_api_key = clean_input(st.text_input(
    "YouTube API ключ",
    value=st.session_state.settings.get("youtube_api_key", ""),
    type="password",
    help="Получите ключ на https://console.cloud.google.com/apis/credentials"
))

st.markdown("### Telegram API")
st.markdown("Для парсинга комментариев из Telegram необходимы учетные данные.")

col1, col2 = st.columns(2)

with col1:
    telegram_api_id = clean_input(st.text_input(
        "Telegram API ID",
        value=st.session_state.settings.get("telegram_api_id", ""),
        type="password",
        help="Получите на https://my.telegram.org/apps"
    ))

with col2:
    telegram_api_hash = clean_input(st.text_input(
        "Telegram API Hash",
        value=st.session_state.settings.get("telegram_api_hash", ""),
        type="password",
        help="Получите на https://my.telegram.org/apps"
    ))

st.markdown("### Telegram Bot Token (опционально)")
st.markdown("Если планируете использовать Bot API для парсинга Telegram")

telegram_bot_token = clean_input(st.text_input(
    "Bot Token",
    value=st.session_state.settings.get("telegram_bot_token", ""),
    type="password",
    help="Получите у @BotFather в Telegram"
))

st.markdown("### Номер телефона (опционально)")
st.markdown("Если планируете использовать пользовательский аккаунт для парсинга Telegram")

telegram_phone = clean_input(st.text_input(
    "Номер телефона",
    value=st.session_state.settings.get("telegram_phone", ""),
    help="Введите номер в международном формате (например: +79001234567)"
))

# Кнопка сохранения настроек
if st.button("💾 Сохранить настройки"):
    new_settings = {
        "youtube_api_key": youtube_api_key,
        "telegram_api_id": telegram_api_id,
        "telegram_api_hash": telegram_api_hash,
        "telegram_bot_token": telegram_bot_token,
        "telegram_phone": telegram_phone
    }
    
    # Обновляем session_state
    st.session_state.settings.update(new_settings)
    
    # Сохраняем в файл
    if save_settings(st.session_state.settings):
        st.success("✅ Настройки сохранены и будут доступны после перезагрузки!")

# Кнопка очистки настроек
if st.button("🗑️ Очистить настройки"):
    empty_settings = {
        "youtube_api_key": "",
        "telegram_api_id": "",
        "telegram_api_hash": "",
        "telegram_bot_token": "",
        "telegram_phone": ""
    }
    
    # Обновляем session_state
    st.session_state.settings = empty_settings
    
    # Сохраняем в файл
    if save_settings(empty_settings):
        st.success("✅ Настройки очищены!")

# Отображение текущих настроек (маскированные)
st.markdown("### Текущие настройки")
col1, col2 = st.columns(2)

with col1:
    st.write("**YouTube API:**")
    if st.session_state.settings.get("youtube_api_key"):
        st.write(f"✅ Ключ установлен: {st.session_state.settings['youtube_api_key'][:10]}...")
    else:
        st.write("❌ Ключ не установлен")
    
    st.write("**Telegram API:**")
    if st.session_state.settings.get("telegram_api_id") and st.session_state.settings.get("telegram_api_hash"):
        st.write("✅ API ID и Hash установлены")
    else:
        st.write("❌ API ID или Hash не установлены")

with col2:
    st.write("**Telegram Bot:**")
    if st.session_state.settings.get("telegram_bot_token"):
        st.write("✅ Bot Token установлен")
    else:
        st.write("❌ Bot Token не установлен")
    
    st.write("**Telegram Phone:**")
    if st.session_state.settings.get("telegram_phone"):
        st.write("✅ Номер телефона установлен")
    else:
        st.write("❌ Номер телефона не установлен") 