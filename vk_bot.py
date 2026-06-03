import random

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

from config import VK_GROUP_TOKEN
from database import (
    init_db,
    save_search_query,
    get_user_queries,
    get_last_user_query,
    save_tender,
    get_saved_tenders,
    save_last_found_tenders,
    get_last_found_tender,
    delete_saved_tender,
    clear_saved_tenders,
    save_subscription,
    get_subscriptions,
    delete_subscription,
    clear_subscriptions
)
from real_tenders import search_real_tenders, format_real_tenders
from ai_analyzer import analyze_tender_simple as analyze_tender_ai
from tender_parser import parse_tender_query, format_parsed_query, is_valid_tender_query
from ai_client import analyze_tender_with_ai


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
        "ремонт кровли Башкортостан до 10 млн\n\n"
        "2. Найти реальные тендеры из ЕИС\n"
        "Команда:\n"
        "найти\n\n"
        "3. Сделать базовый анализ найденного тендера\n"
        "Команда:\n"
        "объяснить\n\n"
        "4. Сделать AI-анализ через OpenAI\n"
        "Команда:\n"
        "ии анализ\n\n"
        "5. Показать историю ваших запросов\n"
        "Команда:\n"
        "мои запросы\n\n"
        "Примеры запросов:\n"
        "ремонт кровли Башкортостан до 10 млн\n"
        "защита от БПЛА до 50 млн\n"
        "защита нефтебазы до 50 млн\n"
        "поставка окон Татарстан до 4 млн\n\n"
        "Важно: это MVP-версия. "
        "Поиск работает через ЕИС, поэтому часть карточек может отображаться упрощённо."
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

def format_saved_tenders(rows):
    if not rows:
        return (
            "У вас пока нет сохранённых тендеров.\n\n"
            "Сначала найдите тендеры командой:\n"
            "найти\n\n"
            "Потом сохраните нужный тендер командой:\n"
            "сохранить 1"
        )

    lines = ["Ваши сохранённые тендеры:\n"]

    for index, row in enumerate(rows, start=1):
        title, price, customer, url, source, number, created_at = row

        price_text = f"{price:,.2f} ₽".replace(",", " ")

        lines.append(
            f"{index}. {title}\n"
            f"📌 Номер: {number}\n"
            f"💰 Цена: {price_text}\n"
            f"🏢 Заказчик: {customer}\n"
            f"🔗 Ссылка: {url}\n"
            f"Источник: {source}\n"
        )

    return "\n".join(lines)

def format_subscriptions(rows):
    if not rows:
        return (
            "У вас пока нет подписок на мониторинг тендеров.\n\n"
            "Чтобы создать подписку, напишите:\n"
            "следить ремонт кровли Башкортостан до 10 млн"
        )

    lines = ["Ваши подписки на мониторинг:\n"]

    for index, row in enumerate(rows, start=1):
        original_text, category, region, budget, created_at = row

        region_text = region or "регион не определён"

        if budget:
            budget_text = f"до {budget:,} ₽".replace(",", " ")
        else:
            budget_text = "бюджет не определён"

        lines.append(
            f"{index}. {category} — {region_text} — {budget_text}\n"
            f"Запрос: {original_text}"
        )

    return "\n\n".join(lines)


def handle_message(user_id, text):
    text = text.strip()
    text_lower = text.lower()

    
    if text_lower in ["привет", "начать", "старт"]:
        return (
            "Привет! Я Tender Helper — тендерный помощник для бизнеса.\n\n"
            "Напиши тендерный запрос простыми словами, например:\n"
            "ремонт кровли Удмуртия до 5 млн\n\n"
            "После запроса можно написать:\n"
            "найти — покажу реальные тендеры из ЕИС\n"
            "объяснить — объясню, какие тендеры подойдут\n"
            "ии анализ — сделаю AI-анализ через OpenAI\n"
            "мои запросы — покажу историю запросов\n"
            "помощь — покажу инструкцию"
        )
    
    if text_lower in ["помощь", "help", "команды", "что ты умеешь"]:
        return get_help_text()

    if text_lower in ["мои запросы", "история", "показать запросы"]:
        rows = get_user_queries(user_id)
        return format_user_queries(rows)
    
    if text_lower in ["мои подписки", "подписки", "мониторинг"]:
        rows = get_subscriptions(user_id)
        return format_subscriptions(rows)
    
    if text_lower.startswith("удалить подписку "):
        parts = text_lower.split()

        if len(parts) != 3 or not parts[2].isdigit():
            return (
                "Не понял, какую подписку удалить.\n\n"
                "Напишите так:\n"
                "удалить подписку 1"
            )

        position = int(parts[2])

        deleted = delete_subscription(user_id, position)

        if not deleted:
            return (
                "Я не нашёл подписку с таким номером.\n\n"
                "Проверьте список командой:\n"
                "мои подписки"
            )

        return "Подписка удалена ✅"
    
    if text_lower in ["очистить подписки", "удалить все подписки"]:
        deleted_count = clear_subscriptions(user_id)

        if deleted_count == 0:
            return "У вас пока нет подписок."

        return f"Подписки очищены ✅\nУдалено: {deleted_count}"
    
    if text_lower in ["мои тендеры", "сохранённые тендеры", "сохраненные тендеры", "избранное"]:
        rows = get_saved_tenders(user_id)
        return format_saved_tenders(rows)
    
    if text_lower.startswith("удалить тендер "):
        parts = text_lower.split()

        if len(parts) != 3 or not parts[2].isdigit():
            return (
                "Не понял, какой тендер удалить.\n\n"
                "Напишите так:\n"
                "удалить тендер 1"
            )

        position = int(parts[2])

        deleted = delete_saved_tender(user_id, position)

        if not deleted:
            return (
                "Я не нашёл сохранённый тендер с таким номером.\n\n"
                "Проверьте список командой:\n"
                "мои тендеры"
            )

        return "Тендер удалён ✅"
    
    if text_lower in ["очистить тендеры", "очистить избранное", "удалить все тендеры"]:
        deleted_count = clear_saved_tenders(user_id)

        if deleted_count == 0:
            return "У вас пока нет сохранённых тендеров."

        return f"Сохранённые тендеры очищены ✅\nУдалено: {deleted_count}"
        
    if text_lower.startswith("сохранить "):
        parts = text_lower.split()

        if len(parts) != 2 or not parts[1].isdigit():
            return (
                "Не понял, какой тендер сохранить.\n\n"
                "Напишите так:\n"
                "сохранить 1"
            )

        position = int(parts[1])

        tender = get_last_found_tender(user_id, position)

        if not tender:
            return (
                "Я не нашёл тендер с таким номером.\n\n"
                "Сначала выполните поиск командой:\n"
                "найти"
            )

        title, price, customer, url, source, number = tender

        saved = save_tender(
            user_id=user_id,
            title=title,
            price=price,
            customer=customer,
            url=url,
            source=source,
            number=number,
        )

        if not saved:
            return (
                "Этот тендер уже сохранён ✅\n\n"
                f"{title}\n"
                f"📌 Номер: {number}"
            )

        return (
            "Тендер сохранён ✅\n\n"
            f"{title}\n"
            f"📌 Номер: {number}"
        )
        
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

        save_last_found_tenders(user_id, tenders)

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

        tenders = search_real_tenders(
            category=category,
            region=region,
            budget=budget,
        )

        save_last_found_tenders(user_id, tenders)

        return format_real_tenders(tenders)
    
    if text_lower in ["объяснить", "разобрать", "анализ", "какие тендеры подойдут"]:
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
            limit=1,
        )

        if not tenders:
            tender = {
                "title": category,
                "region": region or "Регион не указан",
                "price": budget or 0,
                "customer": "Заказчик не найден в данных ЕИС",
            }

            return analyze_tender_ai(tender)

        return analyze_tender_ai(tenders[0])
    
    if text_lower in ["ии анализ", "ai анализ", "нейро анализ", "глубокий анализ"]:
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
            limit=1,
        )

        if not tenders:
            return (
                "Я не нашёл реальный тендер для AI-анализа.\n\n"
                "Попробуйте изменить запрос или убрать регион."
            )

        return analyze_tender_with_ai(tenders[0])
    if text_lower.startswith("следить "):
        subscription_text = text[8:].strip()

        if not subscription_text:
            return (
                "Не понял, за каким запросом следить.\n\n"
                "Напишите так:\n"
                "следить ремонт кровли Башкортостан до 10 млн"
            )

        parsed_data = parse_tender_query(subscription_text)

        if not is_valid_tender_query(parsed_data):
            return (
                "Не понял запрос для подписки.\n\n"
                "Напишите подробнее, например:\n"
                "следить ремонт кровли Башкортостан до 10 млн"
            )
        saved = save_subscription(
            user_id=user_id,
            original_text=subscription_text,
            category=parsed_data["category"],
            region=parsed_data["region"],
            budget=parsed_data["budget"],
        )

        if not saved:
            return (
                "Такая подписка уже существует ✅\n\n"
                f"Категория: {parsed_data['category']}\n"
                f"Регион: {parsed_data['region'] or 'не определён'}"
            )

        budget = parsed_data["budget"]

        if budget:
            budget_text = f"до {budget:,} ₽".replace(",", " ")
        else:
            budget_text = "не определён"

        return (
            "Подписка создана ✅\n\n"
            f"Категория: {parsed_data['category']}\n"
            f"Регион: {parsed_data['region'] or 'не определён'}\n"
            f"Бюджет: {budget_text}\n\n"
            "Теперь бот сможет использовать этот запрос для мониторинга новых тендеров."
        )
        
    parsed_data = parse_tender_query(text)

    if not is_valid_tender_query(parsed_data):
        return get_invalid_query_text()

   
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