.PHONY: install run all ase-2024 ase-2025 aacr-2026-url-scraper aacr-2026-abstract-scraper aacr-2026-url-matcher clean lint test

install:
	pip install -r requirements.txt

# Flexible run
run:
	python main.py -s $(s) -t $(t) -y $(y)

# Named aliases — just: make ase-2025
ase-2024:
	python main.py -s sciencedirect -t ase -y 2024

ase-2025:
	python main.py -s sciencedirect -t ase -y 2025

aacr-2026-us:
	python scrapers/aacrjournals/aacr/aacr_2026_url_scraper.py

aacr-2026-as:
	python scrapers/aacrjournals/aacr/aacr_2026_abstract_scraper.py

aacr-2026-url-matcher:
	python scrapers/aacrjournals/aacr/aacr_2026_url_matcher.py

# Run everything
all:
	python main.py --all

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +

lint:
	flake8 scrapers/ main.py

test:
	pytest tests/