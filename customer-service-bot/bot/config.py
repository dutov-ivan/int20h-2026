from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    FORUM_GROUP_ID: int
    DATABASE_URL: str = "sqlite+aiosqlite:///./bot.db"
