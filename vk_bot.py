import random

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

from config import VK_GROUP_TOKEN
from database import init_db, save_search_query, get_user_queries, get_last_user_query
from demo_tenders import find_demo_tenders, format_demo_tenders
from real_tenders import search_real_tenders, format_real_tenders
from ai_analyzer import analyze_tender_simple as analyze_tender_ai
from tender_parser import parse_tender_query, format_parsed_query, is_valid_tender_query


def send_message(vk, user_id, text):
    vk.messages.send(
        user_id=user_id,
        message=text,
        random_id=random.randint(1, 1_000_000),
    )

def get_invalid_query_text():
    return (
        "Я не понял тендерный запрос.\n\n"
        "Напишите подробнее, например:\n"
        "ремонт кровли Удмуртия до 5 млн\n\n"
        "Также можно написать:\n"
        "помощь — покажу инструкцию"
    )

def get_help_text():
    return (
        "Tender Helper — тендерный помощник для бизнеса\n\n"
        "Что я умею:\n\n"
        "1. Разобрать тендерный запрос\n"
        "Пример:\n"
        "ремонт кровли Удмуртия до 5 млн\n\n"
        "2. Найти похожие демо-тендеры\n"
        "Команда:\n"
        "найти\n\n"
        "3. Объяснить, какие тендеры подойдут\n"
        "Команда:\n"
        "объяснить\n\n"
        "4. Показать историю ваших запросов\n"
        "Команда:\n"
        "мои запросы\n\n"
        "Примеры запросов:\n"
        "поставка окон Казань до 4 млн\n"
        "ремонт дороги Ижевск до 3 млн\n"
        "строительство площадки Уфа до 7 млн\n\n"
        "Важно: сейчас это MVP-версия. "
        "Демо-тендеры тестовые. Позже можно подключить реальные источники поиска."
    )

def format_user_queries(rows):
    if not rows:
        return (
            "У вас пока нет сохранённых запросов.\n\n"
            "Напишите запрос, например:\n"
            "ремонт кровли Удмуртия до 5 млн"
        )

    lines = ["Ваши последние запросы:\n"]

    for index, row in enumerate(rows, start=1):
        category, region, budget, created_at = row

        region_text = region or "регион не определён"

        if budget:
            budget_text = f"до {budget:,} ₽".replace(",", " ")
        else:
            budget_text = "бюджет не определён"

        lines.append(
            f"{index}. {category} — {region_text} — {budget_text}"
        )

    return "\n".join(lines)


def handle_message(user_id, text):
    text = text.strip()
    text_lower = text.lower()

    
    if text_lower in ["привет", "начать", "старт"]:
        return (
            "Привет! Я Tender Helper — тендерный помощник для бизнеса.\n\n"
            "Напиши тендерный запрос простыми словами, например:\n"
            "ремонт кровли Удмуртия до 5 млн\n\n"
            "После запроса можно написать:\n"
            "найти — покажу похожие демо-тендеры\n"
            "объяснить — объясню, какие тендеры подойдут\n"
            "мои запросы — покажу историю запросов\n"
            "помощь — покажу инструкцию"
        )
    
    if text_lower in ["помощь", "help", "команды", "что ты умеешь"]:
        return get_help_text()

    if text_lower in ["мои запросы", "история", "показать запросы"]:
        rows = get_user_queries(user_id)
        return format_user_queries(rows)
    
    if text_lower in ["реальные тендеры", "реальный поиск", "настоящие тендеры"]:
        last_query = get_last_user_query(user_id)

        if not last_query:
            return (
                "У вас пока нет сохранённых запросов.\n\n"
                "Сначала напишите запрос, например:\n"
                "ремонт кровли Удмуртия до 5 млн"
            )

        category, region, budget = last_query

        tenders = search_real_tenders(
            category=category,
            region=region,
            budget=budget,
        )

        return format_real_tenders(tenders)

    if text_lower in ["найти", "найти похожие тендеры", "похожие тендеры"]:
        last_query = get_last_user_query(user_id)

        if not last_query:
            return (
                "У вас пока нет сохранённых запросов.\n\n"
                "Сначала напишите запрос, например:\n"
                "ремонт кровли Удмуртия до 5 млн"
            )

        category, region, budget = last_query

        tenders = find_demo_tenders(
            category=category,
            region=region,
            budget=budget,
        )

        return format_demo_tenders(tenders)
    
    if text_lower in ["объяснить", "разобрать", "анализ", "какие тендеры подойдут"]:
        last_query = get_last_user_query(user_id)

        if not last_query:
            return (
                "У вас пока нет сохранённых запросов.\n\n"
                "Сначала напишите запрос, например:\n"
                "ремонт кровли Удмуртия до 5 млн"
            )

        category, region, budget = last_query

        tenders = find_demo_tenders(
            category=category,
            region=region,
            budget=budget,
            limit=1,
        )

        if not tenders:
            tender = {
                "title": category,
                "region": region or "Регион не указан",
                "price": budget or 0,
                "customer": "Заказчик не указан в демо-запросе",
            }

            return analyze_tender_ai(tender)

        return analyze_tender_ai(tenders[0])
    
    parsed_data = parse_tender_query(text)

    if not is_valid_tender_query(parsed_data):
        return get_invalid_query_text()

    if text.lower().startswith("найти"):
        tenders = find_demo_tenders(
            category=parsed_data["category"],
            region=parsed_data["region"],
            budget=parsed_data["budget"],
        )

        return format_demo_tenders(tenders)

    save_search_query(
        user_id=user_id,
        original_text=text,
        category=parsed_data["category"],
        region=parsed_data["region"],
        budget=parsed_data["budget"],
    )

    return format_parsed_query(parsed_data)

def main():
    init_db()

    vk_session = vk_api.VkApi(token=VK_GROUP_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    print("Tender Helper VK bot запущен...")

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = event.user_id
            text = event.text

            answer = handle_message(user_id, text)
            send_message(vk, user_id, answer)


if __name__ == "__main__":
    main()