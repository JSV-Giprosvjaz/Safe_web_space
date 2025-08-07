from peewee import *

db = SqliteDatabase(
    "tone_analysis.db",
    pragmas={
        "journal_mode": "wal",
        "cache_size": -1 * 64000,  # 64MB
        "foreign_keys": 1,
        "ignore_check_constraints": 0,
        "synchronous": 0,
    },
)


class BaseModel(Model):
    class Meta:
        database = db


class Tone(BaseModel):
    name = CharField(unique=True)


class Hate(BaseModel):
    name = CharField(unique=True)


class Comment(BaseModel):
    text = CharField()
    tone_id = ForeignKeyField(Tone, backref="comments")
    hate_id = ForeignKeyField(Hate, backref="comments")


def populate_db():
    """Заполняет базу данных начальными данными, если они отсутствуют"""
    db.create_tables([Tone, Hate, Comment])

    tones = ["Оскорбление", "Нейтральное", "Позитивное"]
    hates = ["Отсутствие оскарбления", "Ксенофобия", "Гомофобия", "Cексизм", "Лукизм", "Другое"]

    # Добавляем тональности, если их нет
    for tone_name in tones:
        tone, created = Tone.get_or_create(name=tone_name)
        if created:
            print(f"Создана тональность: {tone_name}")

    # Добавляем категории ненависти, если их нет
    for hate_name in hates:
        hate, created = Hate.get_or_create(name=hate_name)
        if created:
            print(f"Создана категория ненависти: {hate_name}")


def init_db():
    """Инициализирует базу данных"""
    try:
        populate_db()
        print("База данных успешно инициализирована")
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")


# Инициализируем базу данных при импорте модуля
if __name__ == "__main__":
    init_db()

