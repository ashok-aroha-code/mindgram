.PHONY: install run all aes-2024 aes-2025 clean lint test

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