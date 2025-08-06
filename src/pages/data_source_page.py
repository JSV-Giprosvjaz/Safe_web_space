import streamlit as st
import pandas as pd
import asyncio
from comment_parsers import YouTubeCommentParser, TelegramCommentParser, Comment

placeholder_container = st.empty()

# Глобальные переменные для кода подтверждения
if "telegram_code" not in st.session_state:
    st.session_state.telegram_code = None
if "show_code_input" not in st.session_state:
    st.session_state.show_code_input = False
if "show_parsing" not in st.session_state:
    st.session_state.show_parsing = False

# Инициализация других переменных session_state
if "file" not in st.session_state:
    st.session_state.file = None
if "data_for_tone" not in st.session_state:
    st.session_state.data_for_tone = None
if "is_need_to_process_data" not in st.session_state:
    st.session_state.is_need_to_process_data = None
if "settings" not in st.session_state:
    st.session_state.settings = {}

with placeholder_container.container():
    st.header("Выбор источника данных")

    # Создаем вкладки для разных источников данных
    tab1, tab2, tab3 = st.tabs(["Загрузка файла", "YouTube парсинг", "Telegram парсинг"])

    with tab1:
        st.subheader("Загрузить CSV или XLSX файл")
        uploaded_file = st.file_uploader(
                "Выберите файл", accept_multiple_files=False, type={"csv", "xlsx"}
        )
        file = uploaded_file if uploaded_file is not None else st.session_state.file
        
        button_text = "Выполнить анализ"

        if st.button(button_text):
            st.session_state.file = file
            st.session_state.is_need_to_process_data = True
            st.rerun()

    with tab2:
        st.subheader("Парсинг комментариев из YouTube")
        
        # Проверяем наличие настроек YouTube API
        if "settings" not in st.session_state or not st.session_state.settings.get("youtube_api_key"):
            st.warning("⚠️ YouTube API ключ не настроен!")
            st.info("Перейдите на страницу '⚙️ Настройки' для настройки YouTube API ключа.")
        else:
            youtube_api_key = st.session_state.settings["youtube_api_key"]
            
            if st.button("Парсить комментарии из YouTube трендов"):
                try:
                    with st.spinner("Парсинг комментариев из YouTube..."):
                        st.info("Начинаем парсинг комментариев из YouTube трендов...")
                        
                        # Проверяем API ключ
                        if len(youtube_api_key) < 10:
                            st.error("Ошибка: YouTube API ключ слишком короткий")
                            st.stop()
                        
                        st.info(f"API ключ валиден: {youtube_api_key[:10]}...")
                        
                        parser = YouTubeCommentParser(youtube_api_key)
                        comments = parser.fetch_comments()
                        
                        if comments:
                            # Конвертируем в DataFrame
                            data = []
                            for comment in comments:
                                data.append({
                                    'text': comment.text,
                                    'author': comment.author,
                                    'timestamp': comment.timestamp,
                                    'source': comment.source,
                                    'video_id': comment.metadata.get('video_id', ''),
                                    'like_count': comment.metadata.get('like_count', 0)
                                })
                            
                            df = pd.DataFrame(data)
                            # Переименовываем колонку text в sentence для совместимости с алгоритмом
                            df = df.rename(columns={'text': 'sentence'})
                            
                            # Отладочная информация
                            st.success(f"✅ Получено {len(comments)} комментариев из YouTube")
                            st.info(f"DataFrame создан: {df.shape}")
                            st.info(f"Колонки: {list(df.columns)}")
                            
                            # Сохраняем в session_state
                            st.session_state.data_for_tone = df
                            st.session_state.is_need_to_process_data = True
                            
                            st.toast(f"Данные сохранены в session_state (размер: {len(df)} записей)")

                            # Переходим к обработке данных
                            st.info("Переходим к анализу тональности...")
                            st.rerun()
                            
                        else:
                            st.warning("Не удалось получить комментарии из YouTube")
                            
                except Exception as e:
                    st.error(f"Ошибка при парсинге YouTube: {e}")
                    import traceback
                    st.code(traceback.format_exc())

    with tab3:
        st.subheader("Парсинг комментариев из Telegram")
        
        # Проверяем наличие настроек Telegram API
        if ("settings" not in st.session_state or 
            not st.session_state.settings.get("telegram_api_id") or 
            not st.session_state.settings.get("telegram_api_hash")):
            st.warning("⚠️ Telegram API не настроен!")
            st.info("Перейдите на страницу '⚙️ Настройки' для настройки Telegram API.")
        else:
            telegram_api_id = st.session_state.settings["telegram_api_id"]
            telegram_api_hash = st.session_state.settings["telegram_api_hash"]
            telegram_bot_token = st.session_state.settings.get("telegram_bot_token", "")
            telegram_phone = st.session_state.settings.get("telegram_phone", "")
            
            # Выбор типа подключения
            connection_type = st.radio(
                "Тип подключения к Telegram",
                ["Bot API", "Пользовательский аккаунт"],
                help="Bot API - использует токен бота, Пользовательский аккаунт - использует номер телефона"
            )
            
            # Проверяем наличие необходимых данных для выбранного типа
            if connection_type == "Bot API":
                if not telegram_bot_token:
                    st.warning("⚠️ Bot Token не настроен!")
                    st.info("Перейдите на страницу '⚙️ Настройки' для настройки Bot Token.")
                    bot_token = None
                else:
                    bot_token = telegram_bot_token
                    phone = None
            else:
                if not telegram_phone:
                    st.warning("⚠️ Номер телефона не настроен!")
                    st.info("Перейдите на страницу '⚙️ Настройки' для настройки номера телефона.")
                    phone = None
                else:
                    phone = telegram_phone
                    bot_token = None
            
            # Ввод каналов
            channels_input = st.text_area(
                "Список каналов (по одному на строку)",
                help="Введите @username каналов, например:\n@channel1\n@channel2"
            )
            
            channels = [line.strip() for line in channels_input.split('\n') if line.strip()] if channels_input else []
            
            # Настройка количества постов
            posts_input = st.text_input(
                "Количество постов для обработки",
                value="50",
                help="Введите число от 10 до 200. Количество последних постов из каждого канала, которые будут обработаны"
            )
            
            # Валидация ввода
            try:
                posts_limit = int(posts_input)
                if posts_limit < 10 or posts_limit > 200:
                    st.error("Количество постов должно быть от 10 до 200")
                    st.stop()
            except ValueError:
                st.error("Введите корректное число")
                st.stop()
            
            # Проверяем обязательные поля в зависимости от типа подключения
            required_fields_valid = (
                channels and
                ((connection_type == "Bot API" and bot_token) or 
                 (connection_type == "Пользовательский аккаунт" and phone))
            )
            

            
            # Показываем кнопку парсинга
            if st.button("Парсить комментарии из Telegram", disabled=not required_fields_valid):
                if required_fields_valid:
                    # Сохраняем параметры в session_state для повторного использования
                    st.session_state.telegram_channels = channels
                    st.session_state.telegram_posts_limit = posts_limit
                    st.session_state.telegram_api_id = telegram_api_id
                    st.session_state.telegram_api_hash = telegram_api_hash
                    st.session_state.telegram_phone = phone
                    st.session_state.telegram_bot_token = bot_token
                    
                    # Устанавливаем флаг для скрытия полей ввода
                    st.session_state.show_parsing = True
                    st.rerun()
        
        # Показываем прогресс бар внизу, если идет парсинг
        if st.session_state.get('show_parsing', False):
            st.markdown("---")
            st.subheader("Прогресс парсинга")
            
            # Показываем поле ввода кода, если нужно
            if st.session_state.show_code_input:
                st.info("📱 Telegram требует код подтверждения!")
                code_input = st.text_input(
                    "Код подтверждения",
                    placeholder="Введите код",
                    max_chars=6,
                    key="telegram_code_input"
                )
                
                if st.button("ОК"):
                    if code_input and len(code_input) >= 5:
                        # Сохраняем код и продолжаем парсинг
                        st.session_state.telegram_code = code_input
                        st.session_state.show_code_input = False
                        st.rerun()
                    else:
                        st.error("Введите корректный код (минимум 5 символов)")
            else:
                # Создаем прогресс бар
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text(f"Подключение к Telegram... ({len(st.session_state.telegram_channels)} каналов)")
                progress_bar.progress(10)
                
                # Получаем сохраненные параметры
                channels = st.session_state.telegram_channels
                posts_limit = st.session_state.telegram_posts_limit
                telegram_api_id = st.session_state.telegram_api_id
                telegram_api_hash = st.session_state.telegram_api_hash
                phone = st.session_state.telegram_phone
                bot_token = st.session_state.telegram_bot_token
                
                # Проверяем API ID
                try:
                    api_id_int = int(telegram_api_id)
                except ValueError:
                    st.error("Ошибка: API ID должен быть числом")
                    st.stop()
                
                # Проверяем API Hash
                if len(telegram_api_hash) < 10:
                    st.error("Ошибка: API Hash слишком короткий")
                    st.stop()
                
                status_text.text("Создание парсера...")
                progress_bar.progress(30)
                
                # Передаем код подтверждения, если он есть
                verification_code = st.session_state.telegram_code if st.session_state.telegram_code else None
                
                # Если код введен, очищаем его из session_state
                if verification_code:
                    st.session_state.telegram_code = None
                
                # Получаем параметры из session_state или используем текущие
                parser_channels = st.session_state.get('telegram_channels', channels)
                parser_posts_limit = st.session_state.get('telegram_posts_limit', posts_limit)
                parser_api_id = st.session_state.get('telegram_api_id', telegram_api_id)
                parser_api_hash = st.session_state.get('telegram_api_hash', telegram_api_hash)
                parser_phone = st.session_state.get('telegram_phone', phone)
                parser_bot_token = st.session_state.get('telegram_bot_token', bot_token)
                
                parser = TelegramCommentParser(
                    api_id=parser_api_id,
                    api_hash=parser_api_hash,
                    channels=parser_channels,
                    posts_limit=parser_posts_limit,
                    phone=parser_phone,
                    bot_token=parser_bot_token,
                    verification_code=verification_code
                )
                
                status_text.text("Получение комментариев...")
                progress_bar.progress(50)
                
                try:
                    comments = parser.fetch_comments()
                    
                    if comments:
                        status_text.text("Обработка результатов...")
                        progress_bar.progress(80)
                        
                        # Конвертируем в DataFrame
                        data = []
                        for comment in comments:
                            data.append({
                                'text': comment.text,
                                'author': comment.author,
                                'timestamp': comment.timestamp,
                                'source': comment.source,
                                'channel': comment.metadata.get('channel', ''),
                                'post_id': comment.metadata.get('post_id', ''),
                                'views': comment.metadata.get('views', 0)
                            })
                        
                        df = pd.DataFrame(data)
                        # Переименовываем колонку text в sentence для совместимости с алгоритмом
                        df = df.rename(columns={'text': 'sentence'})
                        
                        status_text.text("Завершение...")
                        progress_bar.progress(100)
                        
                        st.success(f"✅ Получено {len(comments)} комментариев из Telegram")
                        
                        # Сохраняем в session_state
                        st.session_state.data_for_tone = df
                        st.session_state.is_need_to_process_data = True
                        
                        # Переходим к обработке данных
                        st.info("Переходим к анализу тональности...")
                        st.session_state.show_parsing = False
                        st.rerun()
                        
                    else:
                        status_text.text("Завершение...")
                        progress_bar.progress(100)
                        
                        st.warning("Не удалось получить комментарии из Telegram")
                        st.info("Возможные причины:")
                        st.info("• Каналы недоступны или приватные")
                        st.info("• В каналах нет комментариев к постам")
                        st.info("• Комментарии отключены администраторами")
                        st.info("• Проверьте правильность названий каналов")
                        st.info("• Проверьте логи в файле parsers.log")
                        
                        # Сбрасываем флаг в случае неудачи
                        st.session_state.show_parsing = False
                        
                except Exception as e:
                    if "код подтверждения" in str(e).lower():
                        st.session_state.show_code_input = True
                        st.rerun()
                    else:
                        st.error(f"Ошибка при парсинге Telegram: {e}")
                        # Сбрасываем флаг в случае ошибки
                        st.session_state.show_parsing = False
