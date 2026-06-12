from flask import Flask
from database import get_all_subscriptions

app = Flask(__name__)


@app.route("/")
def index():

    subscriptions = get_all_subscriptions()

    html = f"""
    <h1>Tender Helper Web Panel</h1>

    <p>Статус: Онлайн ✅</p>

    <p>Всего подписок: {len(subscriptions)}</p>

    <h2>Подписки</h2>
    """

    for sub in subscriptions:
        html += f"""
        <p>
        Категория: {sub[2]}<br>
        Регион: {sub[3]}<br>
        Бюджет: {sub[4]} ₽
        </p>
        <hr>
        """

    return html


if __name__ == "__main__":
    app.run(debug=True)