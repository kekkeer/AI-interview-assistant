from pydantic_settings import BaseSettings


class Settings(BaseSettings):
  app_name: str = "AI Interview Assistant"
  database_url: str = "sqlite:///./data.db"
  secret_key: str = "change-me-to-a-random-secret"
  algorithm: str = "HS256"
  access_token_expire_minutes: int = 60 * 24
  deepseek_api_key: str = ""
  deepseek_base_url: str = "https://api.deepseek.com"
  model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

  @property
  def is_sqlite(self) -> bool:
    return self.database_url.startswith("sqlite")


settings = Settings()
