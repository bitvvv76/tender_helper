from openai import OpenAI

from config import OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)


def analyze_tender_with_ai(tender):
    title = tender.get("title", "Без названия")
    price = tender.get("price", 0)
    customer = tender.get("customer", "Заказчик не указан")
    source = tender.get("source", "Источник не указан")
    url = tender.get("url", "Ссылка не указана")
    region = tender.get("region", "Не указан")
    number = tender.get("number", "Не указан")
    law = tender.get("law", "Не указан")

    prompt = f"""
Проанализируй тендер простыми словами для предпринимателя.

Данные тендера:

Название: {title}
Номер закупки: {number}
Регион: {region}
Закон: {law}
Цена: {price}
Заказчик: {customer}
Источник: {source}
Ссылка: {url}

Дай ответ строго по структуре:

1. Что это за тендер простыми словами
2. Кому он может подойти
3. Основные риски
4. На что обратить внимание в документах
5. Предварительный вывод: стоит ли смотреть тендер дальше
6. Оцени привлекательность тендера по шкале от 1 до 5 звёзд
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )

    return response.output_text