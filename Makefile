.PHONY: install test lint format typecheck run frontend

install:
	python -m pip install -e ".[dev]"

test:
	pytest --cov=opentrace --cov-report=term-missing

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy src/opentrace

run:
	uvicorn opentrace.api.app:app --reload --host 127.0.0.1

frontend:
	cd frontend && npm install && npm run dev
