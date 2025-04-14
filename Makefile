# FormAgent Makefile - Common project operations

.PHONY: help install test clean run run-firefox run-chrome run-safari lint

help:
	@echo "FormAgent - Intelligent Web Form Auto-Filling Agent"
	@echo ""
	@echo "make install    - Install dependencies"
	@echo "make test       - Run tests"
	@echo "make clean      - Clean temporary files"
	@echo "make run        - Run with default browser (Firefox)"
	@echo "make run-firefox - Run with Firefox"
	@echo "make run-chrome - Run with Chrome"
	@echo "make run-safari - Run with Safari"
	@echo "make lint       - Run linter"

install:
	pip install -r requirements.txt

test:
	python -m pytest test/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.log" -delete
	rm -rf logs/*

run:
	./start_formagent.sh

run-firefox:
	./start_formagent.sh --firefox

run-chrome:
	./start_formagent.sh --chrome

run-safari:
	./start_formagent.sh --safari

lint:
	flake8 formagent.py src/