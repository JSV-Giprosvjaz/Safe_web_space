import streamlit as st
from config import save_settings, get_environment_info, get_setting

def clean_input(text):
    """Удаляет все пробелы из введенного текста"""
    return text.strip() if text else ""

st.header("⚙️ Настройки API")

# Показываем информацию об окружении
env_info = get_environment_info()
if env_info["debug_mode"]:
    st.info("🔧 **Режим отладки**: Настройки можно изменять через интерфейс")
else:
    st.info("🌐 **Продакшен режим**: Настройки загружаются из Streamlit Secrets")
    st.info("ℹ️ В продакшене настройки управляются через Streamlit Cloud Secrets")

st.markdown("---")

# Инициализируем переменные настройки
youtube_api_key = ""
telegram_api_id = ""
telegram_api_hash = ""
telegram_bot_token = ""
telegram_phone = ""

# Показываем поля ввода только в режиме отладки
if env_info["debug_mode"]:
    st.markdown("### YouTube API")
    st.markdown("Для парсинга комментариев из YouTube необходим API ключ.")

    youtube_api_key = clean_input(st.text_input(
        "YouTube API ключ",
        value=get_setting("youtube_api_key", ""),
        type="password",
        help="Получите ключ на https://console.cloud.google.com/apis/credentials"
    ))

    st.markdown("### Telegram API")
    st.markdown("Для парсинга комментариев из Telegram необходимы учетные данные.")

    col1, col2 = st.columns(2)

    with col1:
        telegram_api_id = clean_input(st.text_input(
            "Telegram API ID",
            value=get_setting("telegram_api_id", ""),
            type="password",
            help="Получите на https://my.telegram.org/apps"
        ))

    with col2:
        telegram_api_hash = clean_input(st.text_input(
            "Telegram API Hash",
            value=get_setting("telegram_api_hash", ""),
            type="password",
            help="Получите на https://my.telegram.org/apps"
        ))

    st.markdown("### Telegram Bot Token (опционально)")
    st.markdown("Если планируете использовать Bot API для парсинга Telegram")

    telegram_bot_token = clean_input(st.text_input(
        "Bot Token",
        value=get_setting("telegram_bot_token", ""),
        type="password",
        help="Получите у @BotFather в Telegram"
    ))

    st.markdown("### Номер телефона (опционально)")
    st.markdown("Если планируете использовать пользовательский аккаунт для парсинга Telegram")

    telegram_phone = clean_input(st.text_input(
        "Номер телефона",
        value=get_setting("telegram_phone", ""),
        help="Введите номер в международном формате (например: +79001234567)"
    ))

# Показываем кнопки только в режиме отладки
if env_info["debug_mode"]:
    # Кнопка сохранения настроек
    if st.button("💾 Сохранить настройки"):
        new_settings = {
            "youtube_api_key": youtube_api_key,
            "telegram_api_id": telegram_api_id,
            "telegram_api_hash": telegram_api_hash,
            "telegram_bot_token": telegram_bot_token,
            "telegram_phone": telegram_phone
        }
        
        # Сохраняем настройки
        if save_settings(new_settings):
            st.rerun()  # Перезагружаем страницу для отображения новых значений

    # Кнопка очистки настроек
    if st.button("🗑️ Очистить настройки"):
        empty_settings = {
            "youtube_api_key": "",
            "telegram_api_id": "",
            "telegram_api_hash": "",
            "telegram_bot_token": "",
            "telegram_phone": ""
        }
        
        # Сохраняем пустые настройки
        if save_settings(empty_settings):
            st.rerun()  # Перезагружаем страницу

# Отображение текущих настроек (маскированные)
st.markdown("### Текущие настройки")
col1, col2 = st.columns(2)

with col1:
    st.write("**YouTube API:**")
    youtube_key = get_setting("youtube_api_key")
    if youtube_key:
        st.write("✅ Ключ установлен")
    else:
        st.write("❌ Ключ не установлен")
    
    st.write("**Telegram API:**")
    telegram_id = get_setting("telegram_api_id")
    telegram_hash = get_setting("telegram_api_hash")
    if telegram_id and telegram_hash:
        st.write("✅ API ID и Hash установлены")
    else:
        st.write("❌ API ID или Hash не установлены")

with col2:
    st.write("**Telegram Bot:**")
    bot_token = get_setting("telegram_bot_token")
    if bot_token:
        st.write("✅ Bot Token установлен")
    else:
        st.write("❌ Bot Token не установлен")
    
    st.write("**Telegram Phone:**")
    phone = get_setting("telegram_phone")
    if phone:
        st.write("✅ Номер телефона установлен")
    else:
        st.write("❌ Номер телефона не установлен") 