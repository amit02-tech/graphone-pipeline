import asyncio
from src.scrapers.news import scrape_news
from src.scrapers.jobs import scrape_jobs


async def main():
    print("Starting Phase II 24-Hour Fresh Signal Ingestion...")
    news_count, jobs_count = await asyncio.gather(scrape_news(), scrape_jobs())
    print(f"\nPhase II Complete! Fresh News: {news_count}, Fresh Jobs: {jobs_count}")


if __name__ == "__main__":
    asyncio.run(main())