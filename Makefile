.PHONY: help run server dev migrate makemigrations shell superuser install test clean

help:
	@echo "Django Poll Application - Makefile Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make run          - Start development server on port 6243"
	@echo "  make server       - Alias for 'make run'"
	@echo "  make dev          - Alias for 'make run'"
	@echo "  make migrate      - Apply database migrations"
	@echo "  make makemigrations - Create new migrations"
	@echo "  make shell        - Open Django shell"
	@echo "  make superuser    - Create superuser account"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Remove cache and temporary files"
	@echo ""

run:
	@echo "Starting Django development server on port 6243..."
	@source venv/bin/activate && python manage.py runserver 0.0.0.0:6243

server: run

dev: run

migrate:
	@echo "Applying database migrations..."
	@source venv/bin/activate && python manage.py migrate

makemigrations:
	@echo "Creating new migrations..."
	@source venv/bin/activate && python manage.py makemigrations

shell:
	@echo "Opening Django shell..."
	@source venv/bin/activate && python manage.py shell

superuser:
	@echo "Creating superuser..."
	@source venv/bin/activate && python manage.py createsuperuser

install:
	@echo "Installing dependencies..."
	@source venv/bin/activate && pip install -r requirements.txt

test:
	@echo "Running tests..."
	@source venv/bin/activate && python manage.py test

clean:
	@echo "Cleaning up cache and temporary files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.log" -delete
	@echo "Clean complete!"
