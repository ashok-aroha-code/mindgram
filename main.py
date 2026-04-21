import argparse
from scrapers.sciencedirect.ase.ase_2024_scraper import ASEScraper2024
from scrapers.sciencedirect.ase.ase_2025_scraper import ASEScraper2025
from scrapers.aacrjournals.aacr.aacr_2026_url_scraper import AACR2026URLScraper
from scrapers.aacrjournals.aacr.aacr_2026_abstract_scraper import AACR2026AbstractScraper
from scrapers.aacrjournals.aacr.aacr_2026_url_matcher import AACR2026URLMatcher


SCRAPERS = {
    ("sciencedirect", "ase", "2024", "default"): ASEScraper2024,
    ("sciencedirect", "ase", "2025", "default"): ASEScraper2025,
    ("aacrjournals", "aacr", "2026", "url-scraper"): AACR2026URLScraper,
    ("aacrjournals", "aacr", "2026", "abstract-scraper"): AACR2026AbstractScraper,
    ("aacrjournals", "aacr", "2026", "url-matcher"): AACR2026URLMatcher,
}


def run(source: str, topic: str, year: str, task: str = "default"):
    key = (source, topic, year, task)
    scraper_class = SCRAPERS.get(key)

    if not scraper_class:
        print(
            f"[ERROR] No scraper found for: source={source}, topic={topic}, year={year}, task={task}"
        )
        print(f"Available scrapers: {list(SCRAPERS.keys())}")
        return

    print(f"[INFO] Running scraper: {source} -> {topic} -> {year} [Task: {task}]")
    scraper_class().run()
    print(f"[INFO] Done.")


def main():
    parser = argparse.ArgumentParser(
        description="Mindgram Scraper - Run any registered scraper",
        epilog="Example: python main.py -s sciencedirect -t ase -y 2025"
    )
    parser.add_argument(
        "-s", "--source", required=True, help="Data source (e.g. sciencedirect)"
    )
    parser.add_argument(
        "-t", "--topic", required=True, help="Topic/journal (e.g. ase)"
    )
    parser.add_argument("-y", "--year", required=True, help="Year (e.g. 2025)")
    parser.add_argument(
        "-tk", "--task", default="default", help="Task type (e.g. url-scraper, abstract-scraper)"
    )
    parser.add_argument("--all", action="store_true", help="Run all registered scrapers")

    args = parser.parse_args()

    if args.all:
        print(f"[INFO] Running all {len(SCRAPERS)} scrapers...")
        for source, topic, year, task in SCRAPERS:
            run(source, topic, year, task)
    else:
        run(args.source, args.topic, args.year, args.task)


if __name__ == "__main__":
    main()