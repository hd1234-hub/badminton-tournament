import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "sqlite:///./data/badminton.db"
    environment: str = "development"
    run_auto_migrate: bool = True
    secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 7
    anthropic_api_key: str = ""
    anthropic_auth_token: str = ""
    anthropic_base_url: str = ""
    anthropic_model: str = ""
    agent_model: str = "claude-sonnet-4-6"
    
    # 生产环境安全设置
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"
    max_requests_per_minute: int = 60  # 每分钟最大请求数
    admin_usernames: str = ""  # 逗号分隔的管理员用户名，启动时自动授予 is_admin
    log_level: str = "INFO"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        env = (self.environment or "development").lower()
        # 生产环境必须显式配置 SECRET_KEY
        if env == "production" and not self.secret_key:
            raise ValueError("SECRET_KEY is required in production environment")
        # 开发环境兜底随机密钥
        if env != "production" and not self.secret_key:
            self.secret_key = secrets.token_hex(32)
            import logging
            logging.getLogger("badminton").warning(
                "WARNING: SECRET_KEY not set, using random key. "
                "Sessions will not persist across restarts. "
                "Please set SECRET_KEY in production!"
            )


settings = Settings()
