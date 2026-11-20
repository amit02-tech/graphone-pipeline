import asyncio
from src.scrapers.startups import scrape_startups
from src.scrapers.products import scrape_products
from src.scrapers.papers import scrape_papers


async def main():
    print("Starting Phase I Bulk Acquisition...")
    results = await asyncio.gather(
        scrape_startups(1200),
        scrape_products(1200),
        scrape_papers(1050),
    )
    print(f"\nPhase I Complete! Startups: {results[0]}, Products: {results[1]}, Papers: {results[2]}")


if __name__ == "__main__":
    asyncio.run(main())