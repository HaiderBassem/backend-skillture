# CommerceCore: one place to run every layer.  Run these from the repository root.
#
#   make install                  one shared .venv for all four projects (needs uv)
#   make migrate                  bring the dev AND the test database to the latest migration
#   make check                    can the app reach the dev database?
#   make test                     run the tests of every layer: DAL -> services -> API
#   make lint                     ruff on every project
#   make run                      start the API: http://127.0.0.1:8000/docs
#   make seed                     fill an EMPTY dev database with demo data
#   make admin EMAIL=you@x.com    make a registered user an administrator
#
# Settings live in ONE file: .env here at the root (cp .env.example .env), read by every layer.

PY := $(CURDIR)/.venv/bin/python
export PYTHONPATH := $(CURDIR)/commercecore-api:$(CURDIR)/commercecore-services:$(CURDIR)/commercecore-dal

# Reads one URL from .env, so the migrations use the same database as the app.
db_url = $(shell $(PY) -c "from dotenv import dotenv_values; print(dotenv_values('.env')['$(1)'])")

.PHONY: install migrate check test lint run seed admin

install:
	uv venv --python 3.12 .venv
	uv pip install --python $(PY) -r requirements-dev.txt

migrate:
	@echo "== dev database";  cd commercecore-migrations && DATABASE_URL='$(call db_url,DATABASE_URL)' $(PY) -m alembic upgrade head
	@echo "== test database"; cd commercecore-migrations && DATABASE_URL='$(call db_url,TEST_DATABASE_URL)' $(PY) -m alembic upgrade head

check:
	$(PY) -m dal.check

test:
	cd commercecore-dal      && $(PY) -m pytest -q
	cd commercecore-services && $(PY) -m pytest -q
	cd commercecore-api      && $(PY) -m pytest -q

lint:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .

run:
	cd commercecore-api && $(PY) -m uvicorn api.main:create_app --factory --reload \
		--reload-dir . --reload-dir ../commercecore-services --reload-dir ../commercecore-dal

seed:
	$(PY) -m api.seed

admin:
	$(PY) -m api.manage make-admin $(EMAIL)
