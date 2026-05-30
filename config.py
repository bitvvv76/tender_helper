import os
from dotenv import load_dotenv


load_dotenv()

VK_GROUP_TOKEN = os.getenv("VK_GROUP_TOKEN")


if not VK_GROUP_TOKEN:
    raise ValueError("Не найден VK_GROUP_TOKEN в файле .env")