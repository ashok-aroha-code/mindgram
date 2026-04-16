import argparse
from scrapers.sciencedirect.ase.ase_2024_scraper import ASEScraper2024
from scrapers.sciencedirect.ase.ase_2025_scraper import ASEScraper2025


SCRAPERS = {
    ("sciencedirect", "ase", "2024"): ASEScraper2024,
    ("sciencedirect", "ase", "2025"): ASEScraper2025
}

def run(source: str, topic: str, year: str):
    key = (source, topic, year)
    scraper_class = SCRAPERS.get(key)

    if not scraper_class:
        print(f"[ERROR] No scraper found for: source={source}, topic={topic}, year={year}")
        print(f"Available scrapers: {list(SCRAPERS.keys())}")
        return

    print(f"[INFO] Running scraper: {source} -> {topic} -> {year}")
    scraper_class().run()
    print(f"[INFO] Done.")

def main():
    parser = argparse.ArgumentParser(
        description="Mindgram Scraper - Run any registered scraper",
        epilog="Example: python main.py -s sciencedirect -t aes -y 2025"
    )
    parser.add_argument("-s", "--source", required=True, help="Data source (e.g. sciencedirect)")
    parser.add_argument("-t", "--topic",  required=True, help="Topic/journal (e.g. aes)")
    parser.add_argument("-y", "--year",   required=True, help="Year (e.g. 2025)")
    parser.add_argument("--all", action="store_true",    help="Run all registered scrapers")

    args = parser.parse_args()

    if args.all:
        print(f"[INFO] Running all {len(SCRAPERS)} scrapers...")
        for (source, topic, year) in SCRAPERS:
            run(source, topic, year)
    else:
        run(args.source, args.topic, args.year)

if __name__ == "__main__":
    main()