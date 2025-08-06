import streamlit as st
import sqlite3
import pandas as pd
from db.models import db, Tone, Hate, Comment, BaseModel
from peewee import *

def get_analyzed_data_with_filter(page=1, page_size=50, search_term="", filter_column=""):
    """Получает проанализированные данные с пагинацией и фильтрацией"""
    try:
        conn = sqlite3.connect("tone_analysis.db")
        
        # Базовый запрос для подсчета
        count_query = """
        SELECT COUNT(*) as count 
        FROM comment c
        LEFT JOIN tone t ON c.tone_id = t.id
        LEFT JOIN hate h ON c.hate_id = h.id
        """
        
        # Базовый запрос для данных
        base_query = """
        SELECT c.id, c.text, t.name as tone_name, h.name as hate_name
        FROM comment c
        LEFT JOIN tone t ON c.tone_id = t.id
        LEFT JOIN hate h ON c.hate_id = h.id
        """
        
        # Добавляем фильтрацию
        if search_term and filter_column:
            if filter_column == "text":
                where_clause = f"WHERE c.text LIKE '%{search_term}%'"
            elif filter_column == "tone_name":
                where_clause = f"WHERE t.name LIKE '%{search_term}%'"
            elif filter_column == "hate_name":
                where_clause = f"WHERE h.name LIKE '%{search_term}%'"
            else:
                where_clause = ""
        else:
            where_clause = ""
        
        # Получаем общее количество записей с фильтром
        if where_clause:
            count_query = f"{count_query} {where_clause}"
        
        count_result = pd.read_sql_query(count_query, conn)
        total_count = int(count_result.iloc[0]['count'])
        
        # Получаем данные с пагинацией и фильтром
        query = f"{base_query} {where_clause} LIMIT {page_size} OFFSET {(page - 1) * page_size}"
        df = pd.read_sql_query(query, conn)
        
        conn.close()
        
        return df, total_count
    except Exception as e:
        st.error(f"Ошибка при получении проанализированных данных: {e}")
        return None, 0

def main():
    st.title("📊 Проанализированные данные")
    
    st.markdown("""
    Эта страница отображает все проанализированные комментарии с возможностью поиска и фильтрации.
    Здесь вы можете просматривать результаты анализа тональности и категорий ненависти.
    """)
    
    # Инициализация session_state для пагинации
    if "page_analyzed" not in st.session_state:
        st.session_state["page_analyzed"] = 1
    
    # Настройки пагинации
    page_size_options = [10, 25, 50, 100]
    page_size = st.selectbox(
        "Записей на страницу:",
        page_size_options,
        key="page_size_analyzed"
    )
    
    # Фильтры для данных
    st.markdown("#### 🔍 Фильтры:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        tone_filter = st.selectbox(
            "Фильтр по тональности:",
            ["Все"] + ["Оскорбление", "Нейтральное", "Позитивное"],
            key="tone_filter_analyzed"
        )
    
    with col2:
        hate_filter = st.selectbox(
            "Фильтр по категории ненависти:",
            ["Все"] + ["Отсутствие оскарбления", "Ксенофобия", "Гомофобия", "Cексизм", "Лукизм", "Другое"],
            key="hate_filter_analyzed"
        )
    
    # Получаем данные
    current_page = st.session_state["page_analyzed"]
    
    try:
        df, total_count = get_analyzed_data_with_filter(
            page=1,  # Всегда получаем все данные
            page_size=999999,  # Большое число чтобы получить все данные
            search_term="",
            filter_column=""
        )
        
        if df is not None and not df.empty:
            # Применяем фильтры ко всем данным
            filtered_df = df.copy()
            
            if tone_filter != "Все":
                filtered_df = filtered_df[filtered_df['tone_name'] == tone_filter]
            
            if hate_filter != "Все":
                filtered_df = filtered_df[filtered_df['hate_name'] == hate_filter]
            
            # Применяем пагинацию к отфильтрованным данным
            start_idx = (current_page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_df = filtered_df.iloc[start_idx:end_idx]
            
            # Показываем информацию о пагинации
            total_pages = max(1, (len(filtered_df) + page_size - 1) // page_size)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Всего записей", len(filtered_df))
            with col2:
                st.metric("Записей на странице", len(paginated_df))
            with col3:
                st.metric("Всего страниц", total_pages)
            
            # Показываем информацию о фильтрах
            if tone_filter != "Все" or hate_filter != "Все":
                filter_info = []
                if tone_filter != "Все":
                    filter_info.append(f"Тональность: {tone_filter}")
                if hate_filter != "Все":
                    filter_info.append(f"Категория: {hate_filter}")
                st.info(f"🔍 Применены фильтры: {', '.join(filter_info)}")
            
            # Показываем данные
            st.markdown("#### 📋 Проанализированные комментарии:")
            
            # Ограничиваем отображение текста для больших полей
            df_display = paginated_df.copy()
            df_display['text'] = df_display['text'].apply(lambda x: x[:100] + "..." if len(str(x)) > 100 else x)
            
            # Переименовываем колонки для лучшего отображения
            df_display = df_display.rename(columns={
                'id': 'ID',
                'text': 'Текст комментария',
                'tone_name': 'Тональность',
                'hate_name': 'Категория ненависти'
            })
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Пагинация под таблицей
            if total_pages > 1:
                st.markdown("#### Навигация по страницам:")
                
                # Создаем кнопки для навигации
                cols = st.columns(min(10, total_pages + 2))  # +2 для кнопок "Предыдущая" и "Следующая"
                
                # Кнопка "Предыдущая"
                if cols[0].button("◀", key="prev_analyzed", disabled=(current_page <= 1)):
                    if current_page > 1:
                        st.session_state["page_analyzed"] = current_page - 1
                        st.rerun()
                
                # Номера страниц
                start_page = max(1, current_page - 4)
                end_page = min(total_pages, start_page + 8)
                
                for i, col in enumerate(cols[1:-1]):
                    page_num = start_page + i
                    if page_num <= end_page:
                        if col.button(str(page_num), key=f"page_analyzed_{page_num}", disabled=(page_num == current_page)):
                            st.session_state["page_analyzed"] = page_num
                            st.rerun()
                
                # Кнопка "Следующая"
                if cols[-1].button("▶", key="next_analyzed", disabled=(current_page >= total_pages)):
                    if current_page < total_pages:
                        st.session_state["page_analyzed"] = current_page + 1
                        st.rerun()
                
                # Показываем текущую страницу
                st.info(f"Страница {current_page} из {total_pages}")
            
            # Кнопка для экспорта данных (экспортируем все отфильтрованные данные)
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Скачать данные (CSV)",
                data=csv,
                file_name="analyzed_data.csv",
                mime="text/csv",
                key="download_analyzed"
            )
        
        elif df is not None and df.empty:
            st.info("Проанализированных данных пока нет.")
        else:
            st.error("Не удалось загрузить проанализированные данные.")
    
    except Exception as e:
        st.error(f"Ошибка при отображении проанализированных данных: {str(e)}")
        st.error("Попробуйте обновить страницу или проверить подключение к базе данных.")

if __name__ == "__main__":
    main() 