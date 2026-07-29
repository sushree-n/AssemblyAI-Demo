import os

from dotenv import load_dotenv

load_dotenv()

REQUIRED_KEYS = ["ASSEMBLYAI_API_KEY", "DEEPL_API_KEY", "ELEVENLABS_API_KEY"]


def mask(value: str) -> str:
    if not value:
        return "MISSING"
    return f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"


def main():
    print("iTranslate demo — env check")
    for key in REQUIRED_KEYS:
        print(f"  {key}: {mask(os.getenv(key))}")

    lang_a = os.getenv("LANG_A", "en")
    lang_b = os.getenv("LANG_B", "hi")
    print(f"  Language pair: {lang_a} <-> {lang_b}")


if __name__ == "__main__":
    main()
