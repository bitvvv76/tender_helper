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
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 10px;">{sub[2]}</td>
            <td style="padding: 10px;">{sub[3]}</td>
            <td style="padding: 10px;">{f"{sub[4]:,}".replace(",", " ")} ₽</td>
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
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 10px; text-align:center;">{q[0]}</td>
            <td style="padding: 10px; text-align:center;">{q[1]}</td>
            <td style="padding: 10px; text-align:center;">{q[2]}</td>
            <td style="padding: 10px; text-align:center;">{q[3]}</td>
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
    queries = get_user_queries(1113849253, 1000)
    saved_tenders = get_saved_tenders(1113849253, 1000)

    html = f"""
    <div style="
    background:#1f4e79;
    color:white;
    padding:20px;
    border-radius:10px;
    margin-bottom:20px;
    ">

    <h1>Tender Helper Dashboard</h1>

    <p>
    Поиск и мониторинг тендеров для бизнеса
    </p>

    </div>

    <nav>
        <a href="/" style="padding:8px 15px;background:#1f4e79;color:white;text-decoration:none;border-radius:5px;">Главная</a>

        <a href="/subscriptions" style="padding:8px 15px;background:#1f4e79;color:white;text-decoration:none;border-radius:5px;">Подписки</a>

        <a href="/queries" style="padding:8px 15px;background:#1f4e79;color:white;text-decoration:none;border-radius:5px;">Запросы</a>

        <a href="/tenders" style="padding:8px 15px;background:#1f4e79;color:white;text-decoration:none;border-radius:5px;">Тендеры</a>

        <a href="/" style="padding:8px 15px;background:#1f4e79;color:white;text-decoration:none;border-radius:5px;">Статистика</a>
            </nav>

    <hr>

    <h2>📊 Статистика</h2>

<div style="display:flex; gap:15px; margin-bottom:20px;">

    <div style="background:white; padding:20px; border-radius:10px; border:1px solid #ddd; min-width:150px;">
        <h3>Подписки</h3>
        <p style="font-size:28px; font-weight:bold;">{len(subscriptions)}</p>
    </div>

    <div style="background:white; padding:20px; border-radius:10px; border:1px solid #ddd; min-width:150px;">
        <h3>Запросы</h3>
        <p style="font-size:28px; font-weight:bold;">{len(queries)}</p>
    </div>

    <div style="background:white; padding:20px; border-radius:10px; border:1px solid #ddd; min-width:150px;">
        <h3>Тендеры</h3>
        <p style="font-size:28px; font-weight:bold;">{len(saved_tenders)}</p>
    </div>

    <div style="background:white; padding:20px; border-radius:10px; border:1px solid #ddd; min-width:150px;">
        <h3>Система</h3>
        <p style="font-size:20px;">Онлайн ✅</p>
    </div>

</div>

<p>База данных: Подключена ✅</p>
<p>Версия: Web v1.5</p>

    <hr>

    <h2>Подписки</h2>
    """

    html += """
    <table style="
    border-collapse: collapse;
    background: white;
    width: 800px;
    border: 1px solid #ddd;
    table-layout: fixed;
    ">

    <tr style="
    background:#1f4e79;
    color:white;
    ">

    <th style="padding:12px;">Категория</th>
    <th style="padding:12px;">Регион</th>
    <th style="padding:12px;">Бюджет</th>

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