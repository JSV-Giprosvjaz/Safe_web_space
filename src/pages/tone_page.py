import streamlit as st
import pandas as pd

st.header("Анализ тональности")

# Проверяем наличие данных
data = st.session_state.data_for_tone

if data is None:
    st.warning("Данные для анализа отсутствуют. Перейдите к странице источника данных.")
    st.info("Для анализа тональности необходимо загрузить данные через парсеры или файл.")
    st.stop()

# Проверяем, что данные не пустые
if data.empty:
    st.error("Получены пустые данные для анализа.")
    st.info("Попробуйте изменить настройки парсера или загрузить другой файл.")
    st.stop()

# Маппинг для тональностей
TONE_MAPPING = {
    0: "Оскорбление",
    1: "Нейтральное", 
    2: "Позитивное"
}

# Маппинг для категорий ненависти
HATE_MAPPING = {
    0: "Отсутствие оскарбления",
    1: "Ксенофобия",
    2: "Гомофобия", 
    3: "Cексизм",
    4: "Лукизм",
    5: "Другое"
}

# Создаем копию данных с наименованиями для отображения
display_data = data.copy()

# Добавляем колонки с наименованиями, если есть предсказания
if 'tone_prediction' in display_data.columns:
    display_data['tone_name'] = display_data['tone_prediction'].map(TONE_MAPPING)
    
if 'class_prediction' in display_data.columns:
    display_data['hate_name'] = display_data['class_prediction'].map(HATE_MAPPING)

# Показываем статистику
st.subheader("Статистика данных")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Всего записей", len(data))

with col2:
    if 'tone_prediction' in data.columns:
        tone_counts = data['tone_prediction'].value_counts()
        st.metric("Уникальных тональностей", len(tone_counts))
    else:
        st.metric("Тональность", "Не обработано")

with col3:
    if 'class_prediction' in data.columns:
        class_counts = data['class_prediction'].value_counts()
        st.metric("Уникальных классов", len(class_counts))
    else:
        st.metric("Классификация", "Не обработано")

# Показываем данные
st.subheader("Результаты анализа")

# Фильтры для данных
st.write("### Фильтры")
col1, col2 = st.columns(2)

with col1:
    if 'tone_name' in display_data.columns:
        tone_filter = st.selectbox(
            "Фильтр по тональности",
            ["Все"] + list(display_data['tone_name'].unique())
        )
    else:
        tone_filter = "Все"

with col2:
    if 'hate_name' in display_data.columns:
        hate_filter = st.selectbox(
            "Фильтр по категории ненависти",
            ["Все"] + list(display_data['hate_name'].unique())
        )
    else:
        hate_filter = "Все"

# Применяем фильтры
filtered_data = display_data.copy()

if tone_filter != "Все" and 'tone_name' in display_data.columns:
    filtered_data = filtered_data[filtered_data['tone_name'] == tone_filter]

if hate_filter != "Все" and 'hate_name' in display_data.columns:
    filtered_data = filtered_data[filtered_data['hate_name'] == hate_filter]

# Инициализация session_state для пагинации
if "page_tone" not in st.session_state:
    st.session_state["page_tone"] = 1

# Настройки пагинации
page_size_options = [10, 25, 50, 100]
page_size = st.selectbox(
    "Записей на страницу:",
    page_size_options,
    key="page_size_tone"
)

# Применяем пагинацию к отфильтрованным данным
current_page = st.session_state["page_tone"]
start_idx = (current_page - 1) * page_size
end_idx = start_idx + page_size
paginated_data = filtered_data.iloc[start_idx:end_idx]

# Показываем информацию о пагинации
total_pages = max(1, (len(filtered_data) + page_size - 1) // page_size)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Всего записей", len(filtered_data))
with col2:
    st.metric("Записей на странице", len(paginated_data))
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

# Показываем отфильтрованные данные
st.write(f"### Показано записей: {len(paginated_data)} из {len(filtered_data)}")

# Создаем более читаемое отображение
final_columns = ['sentence']
if 'author' in paginated_data.columns:
    final_columns.append('author')
if 'timestamp' in paginated_data.columns:
    final_columns.append('timestamp')
if 'source' in paginated_data.columns:
    final_columns.append('source')
if 'tone_name' in paginated_data.columns:
    final_columns.append('tone_name')
if 'hate_name' in paginated_data.columns:
    final_columns.append('hate_name')

# Переименовываем колонки для лучшего отображения
result_data = paginated_data[final_columns].copy()
if 'sentence' in result_data.columns:
    result_data = result_data.rename(columns={'sentence': 'Текст'})
if 'author' in result_data.columns:
    result_data = result_data.rename(columns={'author': 'Автор'})
if 'timestamp' in result_data.columns:
    result_data = result_data.rename(columns={'timestamp': 'Время'})
if 'source' in result_data.columns:
    result_data = result_data.rename(columns={'source': 'Источник'})
if 'tone_name' in result_data.columns:
    result_data = result_data.rename(columns={'tone_name': 'Тональность'})
if 'hate_name' in result_data.columns:
    result_data = result_data.rename(columns={'hate_name': 'Категория ненависти'})

st.dataframe(result_data, hide_index=True, use_container_width=True)

# Пагинация под таблицей
if total_pages > 1:
    st.markdown("#### Навигация по страницам:")
    
    # Создаем кнопки для навигации
    cols = st.columns(min(10, total_pages + 2))  # +2 для кнопок "Предыдущая" и "Следующая"
    
    # Кнопка "Предыдущая"
    if cols[0].button("◀", key="prev_tone", disabled=(current_page <= 1)):
        if current_page > 1:
            st.session_state["page_tone"] = current_page - 1
            st.rerun()
    
    # Номера страниц
    start_page = max(1, current_page - 4)
    end_page = min(total_pages, start_page + 8)
    
    for i, col in enumerate(cols[1:-1]):
        page_num = start_page + i
        if page_num <= end_page:
            if col.button(str(page_num), key=f"page_tone_{page_num}", disabled=(page_num == current_page)):
                st.session_state["page_tone"] = page_num
                st.rerun()
    
    # Кнопка "Следующая"
    if cols[-1].button("▶", key="next_tone", disabled=(current_page >= total_pages)):
        if current_page < total_pages:
            st.session_state["page_tone"] = current_page + 1
            st.rerun()
    
    # Показываем текущую страницу
    st.info(f"Страница {current_page} из {total_pages}")

# Показываем графики, если есть данные о предсказаниях
if 'tone_name' in display_data.columns or 'hate_name' in display_data.columns:
    st.subheader("Визуализация результатов")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'tone_name' in display_data.columns:
            st.write("### Распределение тональности")
            tone_counts = display_data['tone_name'].value_counts()
            st.bar_chart(tone_counts)
    
    with col2:
        if 'hate_name' in display_data.columns:
            st.write("### Распределение категорий ненависти")
            hate_counts = display_data['hate_name'].value_counts()
            st.bar_chart(hate_counts)

# Кнопка для экспорта результатов
# Создаем экспортируемые данные с наименованиями
export_data = filtered_data.copy()  # Экспортируем все отфильтрованные данные
if 'tone_prediction' in export_data.columns:
    export_data['tone_name'] = export_data['tone_prediction'].map(TONE_MAPPING)
if 'class_prediction' in export_data.columns:
    export_data['hate_name'] = export_data['class_prediction'].map(HATE_MAPPING)

csv = export_data.to_csv(index=False)
st.download_button(
    label="📥 Скачать результаты (CSV)",
    data=csv,
    file_name="tone_analysis_results.csv",
    mime="text/csv",
    key="download_tone"
)
