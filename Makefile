.PHONY: install test check compile js-check lint migration-check run seed

install:
	python3 -m pip install -r requirements.txt

compile:
	python3 -m compileall app bot tests

js-check:
	find app/static/js -name '*.js' -print -exec node --check {} \;

lint:
	npm run lint

migration-check:
	DATABASE_URL=sqlite:////tmp/skillflow_migration_check.db alembic upgrade head

test:
	pytest -q

check: compile migration-check js-check test

run:
	uvicorn app.main:app --reload

seed:
	python3 -m app.dev_seed
