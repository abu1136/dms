from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = Field(default="DMS", alias="APP_NAME")
    env: str = Field(default="development", alias="ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    mysql_host: str = Field(default="localhost", alias="MYSQL_HOST")
    mysql_port: int = Field(default=3306, alias="MYSQL_PORT")
    mysql_db: str = Field(default="dms", alias="MYSQL_DB")
    mysql_user: str = Field(default="dms_user", alias="MYSQL_USER")
    mysql_password: str = Field(default="dms_password", alias="MYSQL_PASSWORD")

    jwt_secret_key: str = Field(default="change_me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="admin123", alias="ADMIN_PASSWORD")
    admin_email: str = Field(default="admin@example.com", alias="ADMIN_EMAIL")

    company_name: str = Field(default="Example Company Ltd.", alias="COMPANY_NAME")
    company_address: str = Field(default="123 Business Road, City, Country", alias="COMPANY_ADDRESS")

    storage_dir: str = Field(default="/app/storage/uploads", alias="STORAGE_DIR")
    
    # SMB/NAS Configuration
    smb_enabled: bool = Field(default=False, alias="SMB_ENABLED")
    smb_host: str = Field(default="", alias="SMB_HOST")
    smb_port: int = Field(default=445, alias="SMB_PORT")
    smb_username: str = Field(default="", alias="SMB_USERNAME")
    smb_password: str = Field(default="", alias="SMB_PASSWORD")
    smb_share: str = Field(default="", alias="SMB_SHARE")
    smb_path: str = Field(default="/DMS", alias="SMB_PATH")

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}"
        )

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
