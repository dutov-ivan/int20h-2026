from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import Optional


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"  # or "production"

    # Required Secrets
    BOT_TOKEN: str
    FORUM_GROUP_ID: int
    WEBHOOK_SECRET_TOKEN: str = "secret-token"

    # Defaults
    DATABASE_URL: str = "sqlite+aiosqlite:///./bot.db"

    # 2. Networking
    WEB_SERVER_HOST: str = "0.0.0.0"

    # Azure injects 'WEBSITES_PORT', but standard naming is often 'PORT'.
    # We default to 8080 if not set.
    WEBSITES_PORT: int = 8080

    # Azure injects this automatically (e.g., 'myapp.azurewebsites.net')
    WEBSITE_HOSTNAME: str = "localhost"

    # We make this Optional because we might calculate it dynamically
    BASE_WEBHOOK_URL: Optional[str] = None
    WEBHOOK_PATH: str = "/webhook"

    # 3. The Fix: Use model_validator (mode='after')
    # This runs AFTER all individual fields are loaded and validated.
    @model_validator(mode="after")
    def build_webhook_url(self) -> "Settings":
        # If BASE_WEBHOOK_URL was explicitly set in env vars (e.g. for ngrok), keep it.
        if self.BASE_WEBHOOK_URL:
            return self

        # Otherwise, construct it from the hostname (Azure logic)
        if self.WEBSITE_HOSTNAME == "localhost":
            # Localhost usually implies http, not https
            self.BASE_WEBHOOK_URL = (
                f"http://{self.WEBSITE_HOSTNAME}:{self.WEBSITES_PORT}"
            )
        else:
            # Azure / Production is always HTTPS
            self.BASE_WEBHOOK_URL = f"https://{self.WEBSITE_HOSTNAME}"

        return self
