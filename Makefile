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
	python main.py -s aacrjournals -t aacr -y 2026 -tk url-scraper

aacr-2026-as:
	python main.py -s aacrjournals -t aacr -y 2026 -tk abstract-scraper

aacr-2026-url-matcher:
	python main.py -s aacrjournals -t aacr -y 2026 -tk url-matcher

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