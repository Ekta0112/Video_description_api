from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Video Description API"
    PROJECT_VERSION: str = "1.0.0"
    GEMINI_API_KEY: str = "AIzaSyDfqbez2TeOZ2vSe22Th0oGJeurFKORCcU"
    EMPOWERVERSE_API_KEY: str = "empowerverse"
    WEMOTIONS_API_KEY: str = "wemotions"
    EMPOWERVERSE_API_PATH: str = "http://localhost:9000/view"
    WEMOTIONS_API_PATH: str = "http://localhost:9001/view"
    VIDEO_DESCRIPTION_KEY: str = "video_description"

    class Config:
        env_file = ".env"

settings = Settings()
print(f"GOOGLE_API_KEY loaded: {'*' * len(settings.GEMINI_API_KEY)}")