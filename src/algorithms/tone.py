from pathlib import PurePath

import streamlit as st
import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import traceback
from torch.cuda.amp import autocast, GradScaler
import gc

from db.models import Comment

MODEL_CHECKPOINT = "DeepPavlov/rubert-base-cased"
import os
# Получаем путь к корню проекта и строим путь к моделям
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))  # Поднимаемся на два уровня вверх
MODEL_TONE_PATH = os.path.join(project_root, "models", "model_tone.pth")
MODEL_CLASS_PATH = os.path.join(project_root, "models", "model_class.pth")

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

# Проверка доступности CUDA и настройка устройства
if torch.cuda.is_available():
    DEVICE = torch.device("cuda")
    # Получаем информацию о GPU
    gpu_name = torch.cuda.get_device_name(0)
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3  # в GB
    st.success(f"🚀 Используется GPU: {gpu_name} ({gpu_memory:.1f} GB)")
    
    # Оптимизация для GPU
    torch.backends.cudnn.benchmark = True
    torch.backends.cudnn.deterministic = False
    
    # Настройка размера батча в зависимости от памяти GPU
    if gpu_memory >= 8:
        BATCH_SIZE = 16
    elif gpu_memory >= 4:
        BATCH_SIZE = 8
    else:
        BATCH_SIZE = 4
else:
    DEVICE = torch.device("cpu")
    BATCH_SIZE = 4
    st.warning("⚠️ CUDA недоступна! Используется CPU. Для ускорения работы рекомендуется:")
    st.markdown("""
    - Установить CUDA Toolkit
    - Установить PyTorch с поддержкой CUDA: `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118`
    - Убедиться, что видеокарта поддерживает CUDA
    """)
    st.info("💡 Текущая производительность может быть ниже ожидаемой")

# Включение mixed precision для ускорения
USE_AMP = torch.cuda.is_available()


@st.cache_resource(show_spinner=False)
def load_tokenizer():
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_CHECKPOINT)
        return tokenizer
    except Exception as e:
        st.error(f"Ошибка загрузки токенизатора: {e}")
        raise


@st.cache_resource(show_spinner=False)
def load_model_tone():
    try:
        model_tone = AutoModelForSequenceClassification.from_pretrained(MODEL_CHECKPOINT, num_labels=3)
        model_tone.load_state_dict(torch.load(MODEL_TONE_PATH, map_location=DEVICE))
        model_tone.to(DEVICE)
        
        # Оптимизация для GPU
        if torch.cuda.is_available():
            model_tone = model_tone.half()  # Использование float16 для экономии памяти
        
        model_tone.eval()
        return model_tone
    except Exception as e:
        st.error(f"Ошибка загрузки модели тональности: {e}")
        raise


@st.cache_resource(show_spinner=False)
def load_model_class():
    try:
        model_class = AutoModelForSequenceClassification.from_pretrained(MODEL_CHECKPOINT, num_labels=6)
        model_class.load_state_dict(torch.load(MODEL_CLASS_PATH, map_location=DEVICE))
        model_class.to(DEVICE)
        
        # Оптимизация для GPU
        if torch.cuda.is_available():
            model_class = model_class.half()  # Использование float16 для экономии памяти
        
        model_class.eval()
        return model_class
    except Exception as e:
        st.error(f"Ошибка загрузки модели классификации: {e}")
        raise


# Загружаем модели при импорте модуля
try:
    tokenizer = load_tokenizer()
    model_tone = load_model_tone()
    model_class = load_model_class()
except Exception as e:
    st.error(f"Критическая ошибка при загрузке моделей: {e}")
    st.error("Проверьте наличие файлов моделей в папке models/")
    raise


def clear_gpu_memory():
    """Очистка памяти GPU"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        gc.collect()


def predict(data):
    try:
        df_tone = data.copy()

        # Проверяем наличие колонки sentence
        if 'sentence' not in df_tone.columns:
            raise ValueError("В данных отсутствует колонка 'sentence'")

        # Проверяем, что данные не пустые
        if df_tone.empty:
            raise ValueError("Получены пустые данные для анализа")

        # Удаляем пустые строки
        df_tone = df_tone.dropna(subset=['sentence'])
        df_tone = df_tone[df_tone['sentence'].str.strip() != '']

        if df_tone.empty:
            raise ValueError("После очистки данных не осталось записей для анализа")

        # Показываем информацию о производительности
        device_info = "GPU" if torch.cuda.is_available() else "CPU"
        st.info(f"⚡ Обрабатываем {len(df_tone)} записей на {device_info} с batch_size={BATCH_SIZE}...")

        # Токенизация с оптимизацией для GPU
        tokenized_data = tokenizer(
            df_tone["sentence"].tolist(), 
            padding=True, 
            truncation=True, 
            max_length=512,
            return_tensors="pt"
        )

        # Перемещение данных на GPU
        if torch.cuda.is_available():
            tokenized_data = {k: v.to(DEVICE) for k, v in tokenized_data.items()}

        # Предсказание с использованием mixed precision
        predictions_tone = []
        predictions_class = []

        model_tone.eval()
        model_class.eval()

        # Использование autocast для mixed precision
        with torch.no_grad():
            with autocast(enabled=USE_AMP):
                # Обработка данных батчами для экономии памяти
                total_batches = (len(df_tone) + BATCH_SIZE - 1) // BATCH_SIZE
                
                # Создаем один прогресс-бар
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i in range(0, len(df_tone), BATCH_SIZE):
                    batch_end = min(i + BATCH_SIZE, len(df_tone))
                    
                    # Создание батча
                    batch_data = {
                        'input_ids': tokenized_data['input_ids'][i:batch_end],
                        'attention_mask': tokenized_data['attention_mask'][i:batch_end]
                    }
                    
                    # Предсказание тональности
                    outputs_tone = model_tone(**batch_data)
                    logits_tone = outputs_tone.logits
                    predictions_tone.extend(torch.argmax(logits_tone, dim=-1).cpu().numpy())

                    # Предсказание класса
                    outputs_class = model_class(**batch_data)
                    logits_class = outputs_class.logits
                    predictions_class.extend(torch.argmax(logits_class, dim=-1).cpu().numpy())

                    # Очистка памяти после каждого батча
                    if torch.cuda.is_available():
                        del outputs_tone, outputs_class, logits_tone, logits_class
                        torch.cuda.empty_cache()

                    # Обновляем прогресс-бар
                    if total_batches > 1:
                        current_batch = (i // BATCH_SIZE) + 1
                        progress = current_batch / total_batches
                        progress_bar.progress(progress)
                        status_text.text(f"Обработано батчей: {current_batch}/{total_batches}")

        # Очищаем прогресс-бар
        progress_bar.empty()
        status_text.empty()

        # Очистка памяти GPU
        clear_gpu_memory()

        # Сохранение предсказаний
        df_tone["tone_prediction"] = predictions_tone
        df_tone["class_prediction"] = predictions_class

        # Изменение предсказаний класса на основе предсказаний тона
        for i in range(len(df_tone)):
            if df_tone.loc[i, "tone_prediction"] in [1, 2]:
                df_tone.loc[i, "class_prediction"] = 0
            elif df_tone.loc[i, "tone_prediction"] == 0 and df_tone.loc[i, "class_prediction"] == 0:
                df_tone.loc[i, "class_prediction"] = 5

        # Добавляем колонки с наименованиями
        df_tone["tone_name"] = df_tone["tone_prediction"].map(TONE_MAPPING)
        df_tone["hate_name"] = df_tone["class_prediction"].map(HATE_MAPPING)

        # Сохраняем в базу данных
        try:
            for idx, comment in df_tone.iterrows():
                Comment.create(
                    text=comment["sentence"],
                    tone_id=comment["tone_prediction"] + 1,
                    hate_id=comment["class_prediction"] + 1
                )
        except Exception as e:
            st.warning(f"Предупреждение: не удалось сохранить в базу данных: {e}")

        # Показываем информацию о завершении
        if torch.cuda.is_available():
            st.success(f"🚀 Анализ завершен успешно! Обработано {len(df_tone)} записей на GPU.")
        else:
            st.success(f"✅ Анализ завершен успешно! Обработано {len(df_tone)} записей на CPU.")
            st.info("💡 Для ускорения работы рекомендуется настроить GPU")
        
        return df_tone

    except Exception as e:
        st.error(f"Ошибка при анализе тональности: {str(e)}")
        st.error("Подробности ошибки:")
        st.code(traceback.format_exc())
        raise
