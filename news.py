from datetime import datetime as dt

def get_published_at(article: dict[str, str]) -> dt:
    return dt.fromisoformat(article['publishedAt']).date()

class Articles():

    def __init__(self, article):
        self.name = article['source']['name']
        self.title = article['title']
        self.publishedAt = get_published_at(article)
        self.url = article['url']