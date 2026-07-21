import os
from pathlib import Path
from google import genai


def load_api_key_from_env_file():
    base_dir = Path(__file__).resolve().parent.parent
    env_path = base_dir / ".env"

    if not env_path.exists():
        return None

    with open(env_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip()

    return None


class GeminiAI:
    def __init__(self):
        api_key = load_api_key_from_env_file()

        if not api_key:
            raise ValueError("GEMINI_API_KEY was not found. Please check your .env file.")

        self.client = genai.Client(api_key=api_key)

    def ask(self, user_message):
        system_prompt = """
You are a cute desktop assistant inside a student project.
Answer clearly and shortly.
You can help with reminders, tasks, files, document conversion, and simple questions.
If the user asks for DOCX/PDF conversion, explain that the app can do it with its file tools.
Do not give very long answers unless necessary.
"""

        prompt = f"{system_prompt}\nUser: {user_message}\nGhost AI:"

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text