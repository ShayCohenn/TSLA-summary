import os
import time
import smtplib
from typing import Final
from datetime import datetime as dt
import requests
import yfinance as yf
from dotenv import load_dotenv
from news import Articles, get_published_at

load_dotenv()

FROM_EMAIL: Final[str] = os.getenv('FROM_EMAIL')
PASSWORD: Final[str] = os.getenv('PASSWORD')
TO_EMAIL: Final[str] = os.getenv('TO_EMAIL')

NEWS_URL: Final[str] = "https://newsapi.org/v2/everything"

NEWS_PARAMS = {
    "q": "tesla",
    "sortBy": "popularity",
    "apiKey": os.getenv("NEWS_API_KEY"),
    "language": "en"
}

def get_stocks() -> dict[str: float]:
    historical_data = yf.Ticker('tsla').history(period="2d")

    today_closing_price: float = round(historical_data.iloc[-1]['Close'], 2)
    yesterday_closing_price: float = round(historical_data.iloc[-2]['Close'], 2)
    return {
        'today_closing_price': today_closing_price,
        'yesterday_closing_price': yesterday_closing_price
    }

def price_change(today: float, yesterday: float) -> dict[str, float]:
    """Returns a dictionary of the price change between today and yesterday"""
    return {
        'change': round(today - yesterday, 2),
        'percent_change': round((today - yesterday) / yesterday * 100, 2)
    }

def get_news_articles() -> list[Articles]:
    news_response = requests.get(NEWS_URL, params=NEWS_PARAMS)
    news_response.raise_for_status()

    articles = news_response.json()['articles']

    # Sort the items by publishedAt date
    articles = sorted(articles, key=get_published_at, reverse=True)
    articles = [article for article in articles if article['urlToImage'] is not None]

    # Export the articles
    return [Articles(article) for article in articles[:5]]

def create_message(prices: dict[str: float], price_changes: dict[str: float], articles: list[Articles]) -> str:
    # Constructing the email body
    message = "Subject: TSLA Stock Data\n"
    message += f"From: noreply <{FROM_EMAIL}>\n\n"

    # Header section
    message += "Here is the summary of TSLA stock and the latest articles:\n\n"

    # Stock information section
    message += "Stock Information:\n"
    message += f"Today's closing price: ${prices['today_closing_price']}\n"
    message += f"Change from yesterday: ${price_changes['change']} ({price_changes['percent_change']}%)\n\n"

    # Article section
    message += "Latest Articles:\n"
    for article in articles:
        message += f"- By: {article.name}\n"
        message += f"  {article.title}\n"
        message += f"  {article.url}\n"
        message += f"  {article.publishedAt}\n\n"

    message = message.encode('utf-8')
    return message

def get_message() -> str:
    stock_data: dict[str: float] = get_stocks()
    articles: list[Articles] = get_news_articles()
    price_changes: dict[str: float] = price_change(stock_data['today_closing_price'], stock_data['yesterday_closing_price'])
    return create_message(stock_data, price_changes, articles)

def main() -> None:
    message = get_message()
    connection = smtplib.SMTP("smtp.gmail.com")
    connection.starttls()
    connection.login(FROM_EMAIL, PASSWORD)
    connection.sendmail(from_addr=FROM_EMAIL, to_addrs=TO_EMAIL, msg=message)
    connection.quit()

if __name__ == "__main__":
    while True:
        now = dt.now()
        if now.hour == 22 and now.minute == 0:
            main()
            time.sleep(60)
        else:
            time.sleep(60)
