const API_KEY = "19875b679e1b4acabd381e4213cdfcf3";
const url = "https://newsapi.org/v2/everything?q=";

window.addEventListener("load", async () => {
    const defaultLanguage = "en"; // Set default language
    const userId = getQueryParams().user; // Get user ID from query params
    fetchNews("India", defaultLanguage);
    fetchRecommendations(userId); // Fetch recommendations with user ID
});

// Function to reload the page
function reload() {
    window.location.reload();
}

// Fetch news articles based on the query and language
async function fetchNews(query, language) {
    try {
        const res = await fetch(`${url}${query}&apiKey=${API_KEY}&language=${language}`);
        const data = await res.json();
        if (data.articles) {
            bindData(data.articles);
        } else {
            console.error("No articles found:", data);
        }
    } catch (error) {
        console.error("Error fetching news:", error);
    }
}

// Fetch personalized recommendations from the server
async function fetchRecommendations(userId) {
    try {
        const res = await fetch(`/recommendations?user=${userId}`); // Include user ID in the request
        if (res.ok) {
            const recommendations = await res.json();
            console.log("Personalized Recommendations:", recommendations);

            // Display recommendations
            const recContainer = document.getElementById("recommendations-container");
            recContainer.innerHTML = ""; // Clear previous recommendations

            recommendations.forEach((rec) => {
                const recItem = document.createElement("div");
                recItem.className = "recommendation-item";
                recItem.innerText = `${rec[0]} - Category: ${rec[1]}`;
                recContainer.appendChild(recItem);
            });
        } else {
            console.error("Failed to fetch recommendations:", res.statusText);
        }
    } catch (error) {
        console.error("Error fetching recommendations:", error);
    }
}

// Bind fetched articles to the DOM
function bindData(articles) {
    const cardsContainer = document.getElementById("cards-container");
    const newsCardTemplate = document.getElementById("template-news-card");

    cardsContainer.innerHTML = ""; // Clear the container before adding new cards

    // Sort articles by publication date (most recent first)
    articles.sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt));

    // Exclude articles with irrelevant keywords
    const adKeywords = [
        'sponsored', 'advertisement', 'promotion', 'advertorial', 'paid content', 
        'partnered', 'affiliate', 'clickbait', 'subscribe', 'deal', 'discount', 
        'sale', 'offer', 'shop now', 'buy now', 'sweepstakes'
    ];

    const filteredArticles = articles.filter(article => {
        return !adKeywords.some(keyword =>
            (article.title && article.title.toLowerCase().includes(keyword)) ||
            (article.description && article.description.toLowerCase().includes(keyword))
        );
    });

    filteredArticles.forEach((article) => {
        if (!article.urlToImage) return; // Skip articles without an image
        const cardClone = newsCardTemplate.content.cloneNode(true);
        fillDataInCard(cardClone, article);
        cardsContainer.appendChild(cardClone);
    });
}

// Fill individual news card with article data
function fillDataInCard(cardClone, article) {
    const newsImg = cardClone.querySelector("#news-img");
    const newsTitle = cardClone.querySelector("#news-title");
    const newsSource = cardClone.querySelector("#news-source");
    const newsDesc = cardClone.querySelector("#news-desc");

    newsImg.src = article.urlToImage || "https://via.placeholder.com/400x200";
    newsTitle.innerHTML = article.title;
    newsDesc.innerHTML = article.description || "No description available.";

    const date = new Date(article.publishedAt).toLocaleString("en-US", {
        timeZone: "Asia/Jakarta",
    });

    newsSource.innerHTML = `${article.source.name} · ${date}`;

    // Add click event to track interaction and open the article link
    cardClone.firstElementChild.addEventListener("click", () => {
        window.open(article.url, "_blank");
        const userId = getQueryParams().user; // Get user ID
        trackUserInteraction(userId, article); // Track user interaction with user ID
    });
}

// Track user interaction with articles
function trackUserInteraction(userId, article) {
    fetch('/track', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            user_id: userId, // Include user ID
            title: article.title,
            category: article.source.name,
            description: article.description,
        }),
    })
    .then(response => {
        if (!response.ok) {
            console.error("Error tracking interaction:", response.statusText);
        }
    })
    .catch((error) => console.error("Error tracking interaction:", error));
}

// Navigation item click handler
let curSelectedNav = null;
function onNavItemClick(id) {
    const language = document.getElementById("language-select").value; // Get selected language
    fetchNews(id, language);
    const navItem = document.getElementById(id);
    curSelectedNav?.classList.remove("active");
    curSelectedNav = navItem;
    curSelectedNav.classList.add("active");
}

// Search button click handler
const searchButton = document.getElementById("search-button");
const searchText = document.getElementById("search-text");

searchButton.addEventListener("click", () => {
    const query = searchText.value;
    const language = document.getElementById("language-select").value; // Get selected language
    if (!query) return;
    fetchNews(query, language);
    curSelectedNav?.classList.remove("active");
    curSelectedNav = null;
});

// Language selection event listener
const languageSelect = document.getElementById("language-select");
languageSelect.addEventListener("change", () => {
    const query = searchText.value || "India"; // Default to "India" if no search
    const selectedLanguage = languageSelect.value;
    fetchNews(query, selectedLanguage);
});

// Utility function to get query parameters
function getQueryParams() {
    const params = new URLSearchParams(window.location.search);
    return {
        user: params.get('user'),
    };
}
