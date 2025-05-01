import requests
import os
from datetime import datetime, timedelta
import json

# You should replace this with your actual API key
NEWS_API_KEY = "6c9ee70e9f204cf7a0de08474533c0dd"  # Get from https://newsapi.org/
GNEWS_API_KEY = "a0f522900143cb477e5f9183389f002b"  # Alternative: https://gnews.io/


def get_trending_news(count=10, country="us", category="general"):
    """
    Fetch trending news articles using NewsAPI.org.
    Falls back to GNews API if NewsAPI fails.

    Args:
        count (int): Number of news articles to fetch (default: 10)
        country (str): Country code (default: 'us')
        category (str): News category (default: 'general')

    Returns:
        list: List of news article objects with title, source, url, etc.
    """
    articles = []

    # Try NewsAPI first
    try:
        articles = get_news_from_newsapi(count, country, category)
    except Exception as e:
        print(f"NewsAPI error: {e}")

        # Fall back to GNews API
        try:
            articles = get_news_from_gnews(count, country, category)
        except Exception as e:
            print(f"GNews API error: {e}")

            # If both APIs fail, fall back to mock data in development
            articles = get_mock_news()

    return articles


def get_news_from_newsapi(count=10, country="us", category="general"):
    """
    Fetch news from NewsAPI.org

    Args:
        count (int): Number of news articles to fetch
        country (str): Country code
        category (str): News category

    Returns:
        list: List of news article objects
    """
    base_url = "https://newsapi.org/v2/top-headlines"

    params = {
        "apiKey": NEWS_API_KEY,
        "country": country,
        "category": category,
        "pageSize": count
    }

    response = requests.get(base_url, params=params)

    if response.status_code != 200:
        raise Exception(f"NewsAPI request failed with status code {response.status_code}: {response.text}")

    data = response.json()

    # Transform the response to our standard format
    articles = []
    for article in data.get("articles", []):
        articles.append({
            "title": article.get("title", ""),
            "description": article.get("description", ""),
            "url": article.get("url", ""),
            "image_url": article.get("urlToImage", ""),
            "source": article.get("source", {}).get("name", "Unknown"),
            "published_at": article.get("publishedAt", ""),
            "content": article.get("content", "")
        })

    return articles


def get_news_from_gnews(count=10, country="us", category="general"):
    """
    Fetch news from GNews API

    Args:
        count (int): Number of news articles to fetch
        country (str): Country code
        category (str): News category

    Returns:
        list: List of news article objects
    """
    base_url = "https://gnews.io/api/v4/top-headlines"

    params = {
        "token": GNEWS_API_KEY,
        "country": country,
        "topic": category,
        "max": count
    }

    response = requests.get(base_url, params=params)

    if response.status_code != 200:
        raise Exception(f"GNews API request failed with status code {response.status_code}: {response.text}")

    data = response.json()

    # Transform the response to our standard format
    articles = []
    for article in data.get("articles", []):
        articles.append({
            "title": article.get("title", ""),
            "description": article.get("description", ""),
            "url": article.get("url", ""),
            "image_url": article.get("image", ""),
            "source": article.get("source", {}).get("name", "Unknown"),
            "published_at": article.get("publishedAt", ""),
            "content": article.get("content", "")
        })

    return articles


def get_mock_news():
    """
    Generate mock news data for development or when APIs fail

    Returns:
        list: List of mock news article objects
    """
    mock_news = [
        {
            "title": "Scientists Make Breakthrough in Renewable Energy Research",
            "description": "A team of scientists has developed a new solar panel that is 50% more efficient than current models.",
            "url": "#",
            "image_url": "https://via.placeholder.com/300x200",
            "source": "Science Daily",
            "published_at": datetime.now().isoformat(),
            "content": "Researchers have developed a new type of solar panel that converts sunlight to electricity with 50% more efficiency than current commercial models. This breakthrough could significantly reduce the cost of solar energy."
        },
        {
            "title": "Global Economy Shows Signs of Recovery After Pandemic",
            "description": "Economic indicators suggest that the global economy is rebounding faster than expected.",
            "url": "#",
            "image_url": "https://via.placeholder.com/300x200",
            "source": "Financial Times",
            "published_at": (datetime.now() - timedelta(hours=2)).isoformat(),
            "content": "Recent economic data suggests that the global economy is recovering more quickly than analysts had predicted. GDP growth in several major economies has exceeded expectations for the second quarter."
        },
        {
            "title": "New Medical Treatment Shows Promise in Clinical Trials",
            "description": "A new treatment for chronic diseases has shown positive results in early clinical trials.",
            "url": "#",
            "image_url": "https://via.placeholder.com/300x200",
            "source": "Health News",
            "published_at": (datetime.now() - timedelta(hours=5)).isoformat(),
            "content": "A novel treatment approach for several chronic diseases has shown promising results in phase II clinical trials. The treatment targets inflammation pathways and could help millions of patients worldwide."
        },
        {
            "title": "Tech Company Announces New Smartphone Features",
            "description": "The latest smartphone update will include enhanced privacy features and AI capabilities.",
            "url": "#",
            "image_url": "https://via.placeholder.com/300x200",
            "source": "Tech Today",
            "published_at": (datetime.now() - timedelta(hours=8)).isoformat(),
            "content": "A major technology company has announced that its next smartphone update will include advanced privacy controls and new AI-powered features designed to improve user experience and security."
        },
        {
            "title": "Environmental Study Reveals Declining Pollution Levels",
            "description": "A new study shows that air pollution levels have decreased in major cities worldwide.",
            "url": "#",
            "image_url": "https://via.placeholder.com/300x200",
            "source": "Environment Watch",
            "published_at": (datetime.now() - timedelta(days=1)).isoformat(),
            "content": "According to a comprehensive environmental study, air pollution levels in major urban centers have decreased significantly over the past five years, likely due to stricter regulations and the adoption of cleaner technologies."
        },
        {
            "title": "Sports Team Wins Championship After Decades-Long Drought",
            "description": "Fans celebrate as their favorite team finally wins a major championship.",
            "url": "#",
            "image_url": "https://via.placeholder.com/300x200",
            "source": "Sports Network",
            "published_at": (datetime.now() - timedelta(days=2)).isoformat(),
            "content": "After a 50-year drought, the team has finally won the championship, bringing joy to millions of long-suffering fans. The victory came after a nail-biting final match that went into overtime."
        },
        {
            "title": "Education Reform Bill Passes in Senate",
            "description": "A major education reform bill has been approved and will take effect next year.",
            "url": "#",
            "image_url": "https://via.placeholder.com/300x200",
            "source": "Policy News",
            "published_at": (datetime.now() - timedelta(days=3)).isoformat(),
            "content": "The Senate has passed a comprehensive education reform bill that aims to improve access to quality education and reduce student debt. The bill includes provisions for increased funding for public schools and expanded scholarship programs."
        },
        {
            "title": "New Archaeological Discovery Changes Historical Timeline",
            "description": "Archaeologists have found artifacts that challenge current understanding of ancient civilizations.",
            "url": "#",
            "image_url": "https://via.placeholder.com/300x200",
            "source": "History Channel",
            "published_at": (datetime.now() - timedelta(days=4)).isoformat(),
            "content": "A recent archaeological discovery has unearthed artifacts that suggest human civilization may be thousands of years older than previously thought. The findings challenge existing historical timelines and theories about the development of early societies."
        },
        {
            "title": "International Space Station Reports Successful Experiment",
            "description": "Astronauts on the ISS have completed a groundbreaking scientific experiment.",
            "url": "#",
            "image_url": "https://via.placeholder.com/300x200",
            "source": "Space News",
            "published_at": (datetime.now() - timedelta(days=5)).isoformat(),
            "content": "Astronauts aboard the International Space Station have successfully completed an experiment that could pave the way for long-duration space travel. The experiment involved testing new life support systems designed for deep space missions."
        },
        {
            "title": "Cultural Festival Celebrates Diversity in Community",
            "description": "A weekend festival brought together different cultures for a celebration of diversity.",
            "url": "#",
            "image_url": "https://via.placeholder.com/300x200",
            "source": "Local News",
            "published_at": (datetime.now() - timedelta(days=6)).isoformat(),
            "content": "A vibrant cultural festival brought thousands of people together to celebrate the diverse heritage of the community. The event featured traditional music, dance, cuisine, and crafts from dozens of cultures represented in the region."
        }
    ]

    return mock_news


def search_news(query, from_date=None, to_date=None, count=10):
    """
    Search for news articles on a specific topic.

    Args:
        query (str): Search query
        from_date (str): Start date in YYYY-MM-DD format
        to_date (str): End date in YYYY-MM-DD format
        count (int): Number of results to return

    Returns:
        list: List of news article objects matching the query
    """
    if not from_date:
        from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    if not to_date:
        to_date = datetime.now().strftime('%Y-%m-%d')

    base_url = "https://newsapi.org/v2/everything"

    params = {
        "apiKey": NEWS_API_KEY,
        "q": query,
        "from": from_date,
        "to": to_date,
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": count
    }

    try:
        response = requests.get(base_url, params=params)

        if response.status_code != 200:
            return []

        data = response.json()

        # Transform the response to our standard format
        articles = []
        for article in data.get("articles", []):
            articles.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "url": article.get("url", ""),
                "image_url": article.get("urlToImage", ""),
                "source": article.get("source", {}).get("name", "Unknown"),
                "published_at": article.get("publishedAt", ""),
                "content": article.get("content", "")
            })

        return articles

    except Exception as e:
        print(f"Error searching news: {e}")
        return []