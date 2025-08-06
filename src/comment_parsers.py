from typing import Protocol, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging
from googleapiclient.discovery import build
from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import InputPeerChannel
import re

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('parsers.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class Comment:
    """Модель комментария"""
    text: str
    author: str
    timestamp: datetime
    source: str
    metadata: Dict[str, Any] = None


class CommentParser(Protocol):
    """Протокол для парсеров комментариев"""
    
    def fetch_comments(self) -> List[Comment]:
        """Получить комментарии из источника"""
        ...


class YouTubeCommentParser:
    """Парсер комментариев из YouTube трендов"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        try:
            self.youtube = build('youtube', 'v3', developerKey=api_key)
            logger.info("YouTube API клиент успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации YouTube API: {e}")
            raise
    
    def fetch_comments(self) -> List[Comment]:
        """Получить комментарии из трендовых видео YouTube"""
        comments = []
        
        try:
            logger.info("Начинаем парсинг комментариев из YouTube трендов")
            
            # Получаем трендовые видео
            logger.info("Получаем список трендовых видео...")
            trending_videos = self._get_trending_videos()
            
            if not trending_videos:
                logger.warning("Не удалось получить трендовые видео")
                return comments
                
            logger.info(f"Найдено {len(trending_videos)} трендовых видео")
            
            for i, video in enumerate(trending_videos, 1):
                video_title = video.get('snippet', {}).get('title', 'Unknown')
                logger.info(f"Обрабатываем видео {i}/{len(trending_videos)}: {video_title[:50]}...")
                
                video_comments = self._get_video_comments(video['id'])
                comments.extend(video_comments)
                logger.info(f"Получено {len(video_comments)} комментариев к видео {video_title[:30]}")
                
            logger.info(f"Парсинг YouTube завершен. Всего получено {len(comments)} комментариев")
                
        except Exception as e:
            logger.error(f"Ошибка при парсинге YouTube: {e}")
            raise
            
        return comments
    
    def _get_trending_videos(self) -> List[Dict[str, Any]]:
        """Получить список трендовых видео"""
        try:
            request = self.youtube.videos().list(
                part='id,snippet',
                chart='mostPopular',
                regionCode='RU',
                maxResults=50
            )
            response = request.execute()
            return response.get('items', [])
        except Exception as e:
            logger.error(f"Ошибка при получении трендовых видео: {e}")
            return []
    
    def _get_video_comments(self, video_id: str) -> List[Comment]:
        """Получить комментарии к видео"""
        comments = []
        
        try:
            logger.debug(f"Запрашиваем комментарии к видео {video_id}")
            request = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=100,
                order='relevance'
            )
            response = request.execute()
            
            items = response.get('items', [])
            logger.debug(f"Получено {len(items)} комментариев к видео {video_id}")
            
            for item in items:
                try:
                    snippet = item['snippet']['topLevelComment']['snippet']
                    comment = Comment(
                        text=snippet['textDisplay'],
                        author=snippet['authorDisplayName'],
                        timestamp=datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00')),
                        source='youtube',
                        metadata={
                            'video_id': video_id,
                            'like_count': snippet.get('likeCount', 0),
                            'comment_id': item['id']
                        }
                    )
                    comments.append(comment)
                except Exception as e:
                    logger.warning(f"Ошибка при обработке комментария: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Ошибка при получении комментариев к видео {video_id}: {e}")
            
        return comments


class TelegramCommentParser:
    """Парсер комментариев из Telegram каналов"""
    
    def __init__(self, api_id: str, api_hash: str, channels: List[str], posts_limit: int = 50, phone: str = None, bot_token: str = None, verification_code: str = None):
        self.api_id = api_id
        self.api_hash = api_hash
        self.channels = channels
        self.posts_limit = posts_limit  # Количество постов для обработки
        self.phone = phone  # Номер телефона (если используется)
        self.bot_token = bot_token  # Bot token (если используется)
        self.verification_code = verification_code  # Код подтверждения
        self.client = None
    
    def set_verification_code(self, code: str):
        """Установить код подтверждения"""
        self.verification_code = code
        logger.info("Код подтверждения установлен")
    
    def _code_callback(self):
        """Callback для получения кода подтверждения"""
        if self.verification_code:
            return self.verification_code
        else:
            raise Exception("Требуется код подтверждения. Пожалуйста, введите код в интерфейсе.")
    
    async def _init_client(self):
        """Инициализировать Telegram клиент"""
        if self.client is None:
            logger.info("Инициализация Telegram клиента...")
            logger.info(f"API ID: {self.api_id}")
            logger.info(f"API Hash: {self.api_hash[:10]}...")  # Показываем только первые 10 символов
            
            try:
                if self.bot_token:
                    # Используем Bot API
                    logger.info("Используем Bot API для подключения")
                    self.client = TelegramClient(
                        'bot_session', 
                        int(self.api_id), 
                        self.api_hash,
                        system_version="4.16.30-vxCUSTOM",
                        app_version="1.0",
                        device_model="Desktop",
                        lang_code="en",
                        request_retries=0,
                        connection_retries=0
                    )
                    await self.client.start(bot_token=self.bot_token)
                    logger.info("Telegram Bot клиент успешно инициализирован")
                else:
                    # Используем обычный клиент
                    logger.info("Используем обычный клиент для подключения")
                    self.client = TelegramClient(
                        'session_name', 
                        int(self.api_id), 
                        self.api_hash,
                        system_version="4.16.30-vxCUSTOM",
                        app_version="1.0",
                        device_model="Desktop",
                        lang_code="en",
                        request_retries=0,
                        connection_retries=0
                    )
                    
                    if self.phone:
                        logger.info(f"Используем номер телефона: {self.phone}")
                        
                        # Пытаемся подключиться с callback'ом для кода
                        await self.client.start(
                            phone=self.phone,
                            code_callback=self._code_callback
                        )
                        logger.info("Telegram клиент успешно инициализирован")
                    else:
                        await self.client.start()
                        logger.info("Telegram клиент успешно инициализирован")
            except ValueError as e:
                logger.error(f"Ошибка валидации API ID: {e}")
                raise
            except Exception as e:
                logger.error(f"Ошибка инициализации Telegram клиента: {e}")
                raise
    

    
    async def _check_if_code_needed(self):
        """Проверить, нужен ли код подтверждения"""
        try:
            logger.info("Проверяем, нужен ли код подтверждения...")
            temp_client = TelegramClient('temp_session', int(self.api_id), self.api_hash)
            
            # Пытаемся подключиться без кода
            try:
                await temp_client.start(phone=self.phone)
                await temp_client.disconnect()
                logger.info("Код подтверждения не требуется")
                return False
            except Exception as e:
                if "code" in str(e).lower() or "verification" in str(e).lower():
                    logger.info("Код подтверждения требуется")
                    return True
                else:
                    logger.error(f"Ошибка при проверке кода: {e}")
                    return False
        except Exception as e:
            logger.error(f"Ошибка при проверке необходимости кода: {e}")
            return False
    
    def fetch_comments(self) -> List[Comment]:
        """Получить комментарии из Telegram каналов"""
        try:
            return asyncio.run(self._fetch_comments_async())
        except Exception as e:
            logger.error(f"Ошибка при получении комментариев из Telegram: {e}")
            raise
    
    async def _fetch_comments_async(self) -> List[Comment]:
        """Асинхронное получение комментариев"""
        await self._init_client()
        comments = []
        
        logger.info(f"Начинаем парсинг комментариев из {len(self.channels)} Telegram каналов")
        logger.info(f"Лимит постов на канал: {self.posts_limit}")
        
        for i, channel in enumerate(self.channels, 1):
            try:
                logger.info(f"Обрабатываем канал {i}/{len(self.channels)}: {channel}")
                channel_comments = await self._get_channel_comments(channel)
                comments.extend(channel_comments)
                logger.info(f"Получено {len(channel_comments)} комментариев из канала {channel}")
            except Exception as e:
                logger.error(f"Ошибка при парсинге канала {channel}: {e}")
                continue
        
        logger.info(f"Парсинг Telegram завершен. Всего получено {len(comments)} комментариев")
        return comments
    
    async def _get_channel_comments(self, channel_username: str) -> List[Comment]:
        """Получить комментарии из канала"""
        comments = []
        
        try:
            logger.info(f"Получаем информацию о канале {channel_username}")
            # Получаем информацию о канале
            entity = await self.client.get_entity(channel_username)
            logger.info(f"Канал найден: {entity.title if hasattr(entity, 'title') else channel_username}")
            
            logger.info(f"Запрашиваем сообщения из канала {channel_username}")
            # Получаем сообщения из канала
            messages = await self.client(GetHistoryRequest(
                peer=entity,
                limit=self.posts_limit,  # Используем настраиваемый лимит
                offset_date=None,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=0,
                hash=0
            ))
            
            logger.info(f"Получено {len(messages.messages)} сообщений из канала {channel_username}")
            
            # Обрабатываем каждое сообщение и получаем комментарии к нему
            for i, message in enumerate(messages.messages, 1):
                logger.info(f"Обрабатываем сообщение {i}/{len(messages.messages)} (ID: {message.id})")
                
                # Получаем комментарии к посту
                post_comments = await self._get_post_comments(entity, message.id, channel_username)
                
                if post_comments:
                    logger.info(f"Найдено {len(post_comments)} комментариев к посту {message.id}")
                    comments.extend(post_comments)
                else:
                    logger.debug(f"К посту {message.id} комментариев не найдено")
            
            logger.info(f"Обработано {len(messages.messages)} сообщений, найдено {len(comments)} комментариев")
                        
        except Exception as e:
            logger.error(f"Ошибка при получении комментариев из канала {channel_username}: {e}")
            
        return comments
    
    async def _get_post_comments(self, entity, post_id: int, channel_username: str) -> List[Comment]:
        """Получить комментарии к конкретному посту"""
        comments = []
        
        try:
            # Получаем комментарии к посту
            comment_messages = await self.client.get_messages(
                entity,
                reply_to=post_id,
                limit=20
            )
            
            for comment_msg in comment_messages:
                if comment_msg.text:
                    try:
                        comment = Comment(
                            text=comment_msg.text,
                            author=comment_msg.sender.username if hasattr(comment_msg.sender, 'username') else 'Unknown',
                            timestamp=comment_msg.date,
                            source='telegram',
                            metadata={
                                'channel': channel_username,
                                'post_id': post_id,
                                'comment_id': comment_msg.id,
                                'views': getattr(comment_msg, 'views', 0)
                            }
                        )
                        comments.append(comment)
                    except Exception as e:
                        logger.warning(f"Ошибка при обработке комментария: {e}")
                        continue
                    
        except Exception as e:
            logger.error(f"Ошибка при получении комментариев к посту {post_id}: {e}")
            
        return comments


def get_available_parsers() -> Dict[str, type]:
    """Получить доступные парсеры"""
    return {
        'youtube': YouTubeCommentParser,
        'telegram': TelegramCommentParser
    } 