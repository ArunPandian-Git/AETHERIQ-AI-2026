import os
from dotenv import load_dotenv

load_dotenv()


class Settings:

    APP_NAME = "AETHERIQ AI"
    APP_VERSION = "1.0.0"

    DEFAULT_PROVIDER = os.getenv(
        "DEFAULT_PROVIDER",
        "groq"
    )

    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

    GROQ_MODEL = os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile"
    )

    GEMINI_MODEL = os.getenv(
        "GEMINI_MODEL",
        "gemini-2.5-flash"
    )

    OPENROUTER_MODEL = os.getenv(
        "OPENROUTER_MODEL",
        "openai/gpt-oss-120b"
    )


settings = Settings()