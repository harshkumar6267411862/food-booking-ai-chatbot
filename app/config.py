from pydantic_settings import BaseSettings, SettingsConfigDict
#BaseSettings automaticcaly read values from environment variables..

class Settings(BaseSettings):
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_NAME: str

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore" #pydantic ignores unknown variables...
    )


settings = Settings()