from flask import Flask
from database import get_all_subscriptions

app = Flask(__name__)


@app.route("/")
def index():

    subscriptions = get_all_subscriptions()

    html = f"""
    <h1>Tender Helper Dashboard</h1>

    <nav>
        <a href="/">Главная</a> |
        <a href="/">Подписки</a> |
        <a href="/">Запросы</a> |
        <a href="/">Тендеры</a> |
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