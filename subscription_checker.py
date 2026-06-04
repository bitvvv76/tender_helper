from config import VK_GROUP_TOKEN
from database import get_all_subscriptions, update_subscription_last_seen
from real_tenders import search_real_tenders

import vk_api


def send_vk_message(vk, user_id, text):
    vk.messages.send(
        user_id=user_id,
        message=text,
        random_id=0,
    )


def check_all_subscriptions():
    vk_session = vk_api.VkApi(token=VK_GROUP_TOKEN)
    vk = vk_session.get_api()

    subscriptions = get_all_subscriptions()

    if not subscriptions:
        print("Нет подписок для проверки.")
        return

    for subscription in subscriptions:
        subscription_id, user_id, category, region, budget, last_seen_number = subscription

        tenders = search_real_tenders(
            category=category,
            region=region,
            budget=budget,
            limit=1,
        )

        if not tenders:
            continue

        tender = tenders[0]
        tender_number = tender["number"]

        if last_seen_number == tender_number:
            continue

        update_subscription_last_seen(subscription_id, tender_number)

        message = (
            "🔔 Новый тендер по вашей подписке\n\n"
            f"Категория: {category}\n"
            f"{tender['title']}\n"
            f"📌 Номер: {tender['number']}\n"
            f"💰 Цена: {tender['price']:,.2f} ₽".replace(",", " ") + "\n"
            f"🔗 Ссылка: {tender['url']}"
        )

        send_vk_message(vk, user_id, message)

    print("Проверка подписок завершена.")


if __name__ == "__main__":
    check_all_subscriptions()