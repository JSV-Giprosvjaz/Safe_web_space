import streamlit as st
import sqlite3
import pandas as pd
from db.models import db, Tone, Hate, Comment, BaseModel
from peewee import *

def get_database_info():
    """Получает информацию о структуре базы данных"""
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect("tone_analysis.db")
        cursor = conn.cursor()
        
        # Получаем список таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        database_info = {}
        
        for table in tables:
            table_name = table[0]
            
            # Получаем информацию о структуре таблицы
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            # Получаем количество записей в таблице
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            row_count = cursor.fetchone()[0]
            
            # Получаем информацию о внешних ключах
            cursor.execute(f"PRAGMA foreign_key_list({table_name});")
            foreign_keys = cursor.fetchall()
            
            database_info[table_name] = {
                'columns': columns,
                'row_count': row_count,
                'foreign_keys': foreign_keys
            }
        
        conn.close()
        return database_info
    except Exception as e:
        st.error(f"Ошибка при получении информации о базе данных: {e}")
        return None

def display_table_structure(table_name, table_info):
    """Отображает структуру таблицы"""
    st.subheader(f"📋 Таблица: {table_name}")
    
    # Информация о таблице
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Количество записей", table_info['row_count'])
    
    # Структура таблицы
    st.markdown("#### Структура таблицы:")
    
    columns_data = []
    for col in table_info['columns']:
        columns_data.append({
            'Поле': col[1],
            'Тип': col[2],
            'NOT NULL': 'Да' if col[3] else 'Нет',
            'Значение по умолчанию': str(col[4]) if col[4] else 'NULL',
            'Первичный ключ': 'Да' if col[5] else 'Нет'
        })
    
    df_columns = pd.DataFrame(columns_data)
    st.dataframe(df_columns, use_container_width=True)
    
    # Внешние ключи
    if table_info['foreign_keys']:
        st.markdown("#### Внешние ключи:")
        foreign_keys_data = []
        for fk in table_info['foreign_keys']:
            foreign_keys_data.append({
                'Таблица': fk[2],
                'Поле': fk[4],
                'Ссылается на': fk[3]
            })
        
        df_fk = pd.DataFrame(foreign_keys_data)
        st.dataframe(df_fk, use_container_width=True)
    
    # Показываем содержимое для таблиц tone и hate
    if table_name in ["tone", "hate"]:
        st.markdown("#### Содержимое таблицы:")
        try:
            conn = sqlite3.connect("tone_analysis.db")
            df_content = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            conn.close()
            
            if not df_content.empty:
                # Переименовываем колонки
                if table_name == "tone":
                    df_content = df_content.rename(columns={'id': 'ID', 'name': 'Название тональности'})
                else:
                    df_content = df_content.rename(columns={'id': 'ID', 'name': 'Название категории'})
                
                st.dataframe(df_content, use_container_width=True, hide_index=True)
            else:
                st.info("Таблица пуста.")
        except Exception as e:
            st.error(f"Ошибка при загрузке содержимого таблицы {table_name}: {e}")
    
    st.divider()

# Заголовок страницы
st.title("🗄️ Структура базы данных")

st.markdown("""
Эта страница отображает структуру базы данных проекта анализа тональности.
Здесь вы можете увидеть таблицы, их поля, связи и содержимое справочных таблиц.
""")

# Получаем информацию о базе данных
database_info = get_database_info()

if database_info:
    # Отображаем общую информацию
    st.header("📊 Общая информация")
    
    total_tables = len(database_info)
    total_records = sum(info['row_count'] for info in database_info.values())
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Количество таблиц", total_tables)
    with col2:
        st.metric("Общее количество записей", total_records)
    
    st.divider()
    
    # Отображаем структуру каждой таблицы
    st.header("🏗️ Структура таблиц")
    
    for table_name, table_info in database_info.items():
        display_table_structure(table_name, table_info)
    
    # Схема базы данных
    st.header("🔗 Схема связей")
    
    st.markdown("""
    **Схема базы данных:**
    
    ```
    Tone (Тональность)
    ├── id (Primary Key)
    └── name (Название тональности)
    
    Hate (Категория ненависти)
    ├── id (Primary Key)
    └── name (Название категории)
    
    Comment (Комментарий)
    ├── id (Primary Key)
    ├── text (Текст комментария)
    ├── tone_id (Foreign Key → Tone.id)
    └── hate_id (Foreign Key → Hate.id)
    ```
    """)
    
    st.markdown("""
    **Описание связей:**
    - Каждый комментарий связан с одной тональностью (tone_id)
    - Каждый комментарий связан с одной категорией ненависти (hate_id)
    - Одна тональность может иметь множество комментариев
    - Одна категория ненависти может иметь множество комментариев
    """)
    
else:
    st.error("Не удалось получить информацию о базе данных. Убедитесь, что файл базы данных существует.")

# Кнопка для обновления данных
if st.button("🔄 Обновить данные"):
    st.rerun() 