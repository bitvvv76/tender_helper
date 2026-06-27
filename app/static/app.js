let allTenders = [];

// загрузка данных
fetch("/tenders")
    .then((response) => {
        if (!response.ok) {
            throw new Error("Не удалось загрузить тендеры");
        }
        return response.json();
    })
    .then((data) => {
        allTenders = data.tenders || [];

        renderTenders(allTenders);
        connectSearch();
    })
    .catch((error) => {
        const list = document.getElementById("list");

        list.innerHTML = `
            <div class="error">
                ${error.message}
            </div>
        `;
    });


// =====================
// ПОИСК + ФИЛЬТРЫ + СОРТИРОВКА
// =====================
function connectSearch() {
    const searchInput = document.getElementById("search-input");
    const priceFromInput = document.getElementById("price-from");
    const priceToInput = document.getElementById("price-to");
    const sortSelect = document.getElementById("sort-select");
    const sourceButtons = document.querySelectorAll(".source-btn");
    const searchButton = document.getElementById("search-button");
    let selectedSource = "all";

    if (!searchInput || !priceFromInput || !priceToInput || !sortSelect) {
        return;
    }

    const runServerSearch = () => {
        const query = searchInput.value.trim();
        const budget = priceToInput.value.trim();

        if (!query || query.length < 3) {
            renderTenders(allTenders);
            return;
        }

        const params = new URLSearchParams();
        params.set("query", query);

        if (budget) {
            params.set("budget", budget);
        }

        const list = document.getElementById("list");

        list.innerHTML = `
            <div class="message">
                Идёт поиск тендеров...
            </div>
        `;

        fetch(`/search?${params.toString()}`)
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Не удалось выполнить поиск тендеров");
                }

                return response.json();
            })
            .then((data) => {
                allTenders = data.tenders || [];
                renderTenders(allTenders);
            })
            .catch((error) => {
                list.innerHTML = `
                    <div class="error">
                        ${error.message}
                    </div>
                `;
            });
    };

    if (searchButton) {
        searchButton.addEventListener("click", runServerSearch);
    }

    searchInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            runServerSearch();
        }
    });

    sourceButtons.forEach((btn) => {
    btn.addEventListener("click", () => {

        sourceButtons.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");

        selectedSource = btn.dataset.source;

        applyFilters();
    });
});

    const applyFilters = () => {
    const searchText = searchInput.value.trim().toLowerCase();

    const priceFrom = Number(priceFromInput.value);
    const priceTo = Number(priceToInput.value);

    // 1. ФИЛЬТРАЦИЯ
    let filtered = allTenders.filter((tender) => {

        const title = String(tender.title || "").toLowerCase();
        const customer = String(tender.customer || "").toLowerCase();
        const number = String(tender.number || "").toLowerCase();

        const price = Number(tender.price || 0);

        const matchesText =
            !searchText ||
            title.includes(searchText) ||
            customer.includes(searchText) ||
            number.includes(searchText);

        const matchesPrice =
            (!priceFrom || price >= priceFrom) &&
            (!priceTo || price <= priceTo);

        const matchesSource =
            selectedSource === "all" ||
            (selectedSource === "44" && (tender.source || "").includes("44")) ||
            (selectedSource === "223" && (tender.source || "").includes("223"));

        return matchesText && matchesPrice && matchesSource;
    });

    // 2. СЧЁТ РЕЙТИНГА (score)
    let sorted = filtered.map((tender) => {

        const today = new Date();
        const deadlineDate = tender.deadline
            ? new Date(tender.deadline)
            : new Date();

        const diffDays = Math.ceil(
            (deadlineDate - today) / (1000 * 60 * 60 * 24)
        );

        let urgencyScore = 0;

        if (diffDays <= 2) urgencyScore = 100;
        else if (diffDays <= 5) urgencyScore = 60;
        else urgencyScore = 20;

        let priceScore = 0;

        if (tender.price) {
            if (tender.price < 1000000) priceScore = 80;
            else if (tender.price < 5000000) priceScore = 60;
            else priceScore = 30;
        }

        let text = ((tender.title || "") + " " + (tender.customer || "")).toLowerCase();

        let relevanceScore = 0;

        if (text.includes("ремонт")) relevanceScore += 30;
        if (text.includes("поставка")) relevanceScore += 20;
        if (text.includes("строительство")) relevanceScore += 40;

        return {
            ...tender,
            score: urgencyScore + priceScore + relevanceScore
        };
    });

    // 3. ГЛАВНАЯ СОРТИРОВКА
    sorted.sort((a, b) => (b.score || 0) - (a.score || 0));

    // 4. РЕНДЕР
    renderTenders(sorted);
};

    searchInput.addEventListener("input", applyFilters);
    priceFromInput.addEventListener("input", applyFilters);
    priceToInput.addEventListener("input", applyFilters);
    sortSelect.addEventListener("change", applyFilters);
}


// =====================
// ОТРИСОВКА
// =====================
function renderTenders(tenders) {
    const list = document.getElementById("list");
    const resultsCount = document.getElementById("results-count");

    if (resultsCount) {
        resultsCount.textContent = `Найдено тендеров: ${tenders.length}`;
    }

    list.innerHTML = "";

    if (!tenders || tenders.length === 0) {
        list.innerHTML = `
            <div class="message">
                По вашему запросу тендеры не найдены.
            </div>
        `;
        return;
    }

    tenders.forEach((tender) => {

        const today = new Date();
        const deadlineDate = tender.deadline
            ? new Date(tender.deadline)
            : new Date();

        const diffDays = Math.ceil(
            (deadlineDate - today) / (1000 * 60 * 60 * 24)
        );

        let urgency = "normal";
        let urgencyText = "Норм";

        if (diffDays <= 2) {
            urgency = "urgent";
            urgencyText = "СРОЧНО";
        } else if (diffDays <= 5) {
            urgency = "soon";
            urgencyText = "СКОРО";
        }

        const card = document.createElement("div");
        card.className = "card";

        const badge = document.createElement("div");
        badge.textContent = urgencyText;
        badge.className = "badge " + urgency;

        const title = document.createElement("h3");
        title.textContent = tender.title;

        const price = document.createElement("div");
        price.className = "price";
        price.textContent = formatPrice(tender.price) + " ₽";

        const customer = createMetaRow("Заказчик", tender.customer);
        const source = createMetaRow("Источник", tender.source);
        const number = createMetaRow("Номер", tender.number);

        const deadline = document.createElement("div");
        deadline.className = "deadline";
        deadline.textContent =
            "Окончание подачи заявок: " +
            formatDeadline(tender.deadline);

        card.appendChild(badge);
        card.appendChild(title);
        card.appendChild(price);
        card.appendChild(customer);
        card.appendChild(source);
        card.appendChild(number);
        card.appendChild(deadline);

        if (tender.url) {
            const link = document.createElement("a");
            link.className = "open-link";
            link.href = tender.url;
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            link.textContent = "Открыть тендер";
            card.appendChild(link);
        }

        list.appendChild(card);
    });
}


// =====================
// ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
// =====================
function createMetaRow(label, value) {
    const row = document.createElement("div");
    row.className = "meta";

    const strong = document.createElement("strong");
    strong.textContent = label + ": ";

    const text = document.createTextNode(value || "Не указано");

    row.appendChild(strong);
    row.appendChild(text);

    return row;
}

function formatPrice(value) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "Цена не указана";
    }

    return number.toLocaleString("ru-RU", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function formatDeadline(value) {
    if (!value) return "Срок не указан";

    const parts = value.split("-");
    if (parts.length !== 3) return value;

    return `${parts[2]}.${parts[1]}.${parts[0]}`;
}