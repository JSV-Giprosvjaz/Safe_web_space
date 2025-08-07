import streamlit as st
from config import load_settings

# Инициализация session_state
if "file" not in st.session_state:
    st.session_state.file = None
if "data_for_tone" not in st.session_state:
    st.session_state.data_for_tone = None
if "is_need_to_process_data" not in st.session_state:
    st.session_state.is_need_to_process_data = None
if "settings" not in st.session_state:
    st.session_state.settings = load_settings()

st.logo("static/logo.jpg", size="large")

tone_page = st.Page("pages/tone_page.py", title="Анализ тональности")
data_source_page = st.Page("pages/data_source_page.py", title="Источник данных")
settings_page = st.Page("pages/settings_page.py", title="⚙️ Настройки")
database_page = st.Page("pages/database_page.py", title="🗄️ Структура базы данных")
analyzed_data_page = st.Page("pages/analyzed_data_page.py", title="📊 Проанализированные данные")

loading_page = st.Page("pages/loading_page.py", title="Обработка данных")

# Определяем, какую страницу показывать
if st.session_state.is_need_to_process_data:
    # Данные есть, но нужно обработать - показываем страницу загрузки
    pg = st.navigation([loading_page])
elif (st.session_state.file is None) and (st.session_state.data_for_tone is None):
    # Нет данных - показываем страницы с настройками и источником данных
    pages = {
        "Загрузка данных": [data_source_page],
        "База данных": [database_page, analyzed_data_page],
        "Настройки": [settings_page],
    }
    pg = st.navigation(pages)
else:
    # Данные обработаны - показываем страницы с результатами и настройками
    pages = {
        "Результаты анализа": [tone_page],
        "Загрузка данных": [data_source_page],
        "База данных": [database_page, analyzed_data_page],
        "Настройки": [settings_page],
    }
    pg = st.navigation(pages)

# Запускаем навигацию
pg.run()

def main():
    """Main function for the application"""
    # The main logic is already in the global scope
    pass
