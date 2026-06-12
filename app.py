from flask import Flask
from database import get_all_subscriptions, get_user_queries, get_saved_tenders

app = Flask(__name__)

@app.route("/subscriptions")
def subscriptions_page():

    subscriptions = get_all_subscriptions()

    html = """
    <h1>Подписки Tender Helper</h1>

    <a href="/">← Назад в Dashboard</a>

    <hr>

    <table border="1" cellpadding="10">
    <tr>
        <th>Категория</th>
        <th>Регион</th>
        <th>Бюджет</th>
    </tr>
    """

    for sub in subscriptions:
        html += f"""
        <tr>
            <td>{sub[2]}</td>
            <td>{sub[3]}</td>
            <td>{f"{sub[4]:,}".replace(",", " ")} ₽</td>
        </tr>
        """

    html += "</table>"

    return html

@app.route("/queries")
def queries_page():

    queries = get_user_queries(1113849253, 20)

    html = """
    <h1>История запросов</h1>

    <a href="/">← Назад в Dashboard</a>

    <hr>

    <table border="1" cellpadding="10">
    <tr>
        <th>Категория</th>
        <th>Регион</th>
        <th>Бюджет</th>
        <th>Дата</th>
    </tr>
    """

    for q in queries:
        html += f"""
        <tr>
            <td>{q[0]}</td>
            <td>{q[1]}</td>
            <td>{q[2]}</td>
            <td>{q[3]}</td>
        </tr>
        """

    html += "</table>"

    return html

@app.route("/tenders")
def tenders_page():

    tenders = get_saved_tenders(1113849253, 20)

    if not tenders:
        return """
        <h1>Сохранённые тендеры</h1>
        <a href="/">← Назад в Dashboard</a>
        <hr>
        <p>Сохранённых тендеров пока нет.</p>
        """

    html = """
    <h1>Сохранённые тендеры</h1>

    <a href="/">← Назад в Dashboard</a>

    <hr>

    <table border="1" cellpadding="10">
    <tr>
        <th>Название</th>
        <th>Цена</th>
        <th>Заказчик</th>
        <th>Номер</th>
        <th>Источник</th>
        <th>Дата</th>
    </tr>
    """

    for tender in tenders:
        price = tender[1]

        if price:
            price_text = f"{price:,.2f}".replace(",", " ") + " ₽"
        else:
            price_text = "не указана"

        html += f"""
        <tr>
            <td>{tender[0]}</td>
            <td>{price_text}</td>
            <td>{tender[2]}</td>
            <td>{tender[5]}</td>
            <td>{tender[4]}</td>
            <td>{tender[6]}</td>
        </tr>
        """

    html += "</table>"

    return html


@app.route("/")
def index():

    subscriptions = get_all_subscriptions()

    html = f"""
    <h1>Tender Helper Dashboard</h1>

    <nav>
        <a href="/">Главная</a> |
        <a href="/subscriptions">Подписки</a> |
        <a href="/queries">Запросы</a>
        <a href="/tenders">Тендеры</a>
        <a href="/">Статистика</a>
    </nav>

    <hr>

    <h2>📊 Статистика</h2>

    <ul>
        <li>Всего подписок: {len(subscriptions)}</li>
        <li>Статус системы: Онлайн ✅</li>
        <li>База данных: Подключена ✅</li>
        <li>Версия: Web v0.6</li>
    </ul>

    <hr>

    <h2>Подписки</h2>
    """

    html += """
    <table border="1" cellpadding="10">
    <tr>
        <th>Категория</th>
        <th>Регион</th>
        <th>Бюджет</th>
    </tr>
    """

    for sub in subscriptions:
        html += f"""
        <tr>
            <td>{sub[2]}</td>
            <td>{sub[3]}</td>
            <td>{f"{sub[4]:,}".replace(",", " ")} ₽</td>
        </tr>
        """

    html += "</table>"

    return html


if __name__ == "__main__":
    app.run(debug=True)