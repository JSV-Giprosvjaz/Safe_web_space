import pandas as pd
import streamlit as st

placeholder = st.empty()

st.image("static/loading.gif")

hide_img_fs = '''
<style>
button[title="View fullscreen"]{
    visibility: hidden;}
</style>
'''

st.markdown(hide_img_fs, unsafe_allow_html=True)

with placeholder.container(border=True) as container:
    text_container = st.empty()
    text_container.write("Подготовка моделей...")

    from algorithms.tone import predict

    st.toast("Подготовка моделей завершена!")

    # Проверяем, есть ли уже данные в session_state (от парсеров)
    if st.session_state.data_for_tone is not None:
        df = st.session_state.data_for_tone
        text_container.empty()
        text_container.write("Обработка данных для анализа тональности...")
        st.session_state.data_for_tone = predict(df)
    else:
        # Обрабатываем данные из файла
        if st.session_state.file is None:
            st.error("Данные не найдены. Пожалуйста, загрузите файл или используйте парсинг на странице 'Источник данных'.")
            st.stop()
            
        try:
            df = pd.read_csv(st.session_state.file, header=0, skip_blank_lines=True,
                             skipinitialspace=True, encoding='latin-1')
        except:
            df = pd.read_excel(st.session_state.file, header=0)

        text_container.empty()
        text_container.write("Обработка данных для анализа тональности...")
        st.session_state.data_for_tone = predict(df)

st.session_state.is_need_to_process_data = False
st.rerun()
