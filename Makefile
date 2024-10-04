#Makefile

help:
	@echo "Available commands:"
	@echo "  makemigrations   - Create migration files for Django models. Usage: 'make makemigrations'"
	@echo "  migrate          - Apply database migrations. Usage: 'make migrate'"
	@echo "  lint             - Run flake8 to lint the code. Usage: 'make lint'"
	@echo "  black         - Format code using black. Usage: 'make format_code'"
	@echo "  test             - Run tests. Usage: 'make test'"
	@echo "  coverage_report  - Generate coverage report. Usage: 'make coverage_report'"
	@echo "  createsuperuser  - Create admin/super user. Usage: 'make createsuperuser'"
	@echo "  install_pre_commit - Install pre commits on local system. Usage: 'make install_pre_commit'"
	@echo "  create_auctions  - Generate 201 auction records using the management command. Usage:'make create_auctions'"


# Create migration files
makemigrations:
	@echo "Making migration files..."
	docker compose run --rm auctions python manage.py makemigrations

# Run migrations
migrate:
	@echo "Running migrations in Docker..."
	docker compose run --rm auctions python manage.py migrate

# Lint the code with flake8
lint:
	@echo "Running flake8 for code linting..."
	docker compose run --rm auctions flake8

# Format code using black
black:
	@echo "Formatting code with black..."
	docker compose run --rm auctions black .

# Test the code
test:
	@echo "Running Tests..."
	docker compose run --rm auctions python manage.py test --parallel

# Generate coverage report
coverage_report:
	@echo "Running Django tests with coverage and generating report..."
	docker compose run --rm auctions sh -c "coverage run manage.py test && coverage report && coverage html"

# Create a Django superuser
createsuperuser:
	@echo "Creating a Django superuser..."
	docker compose run --rm auctions python manage.py createsuperuser

# Install pre-commit on the local system
install_pre_commit:
	@echo "Installing pre-commit on the local system..."
	pre-commit install

# Run the create_auctions management command
create_auctions:
	@echo "Creating 201 auction records using management command..."
	docker compose run --rm auctions python manage.py create_auctions
