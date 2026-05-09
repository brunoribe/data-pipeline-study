COMPOSE=docker compose
PYTHON ?= python
DATASET_ARGS ?=

.PHONY: build up down destroy restart logs ps validate bootstrap dagster-shell generate-datasets

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

destroy:
	$(COMPOSE) down -v

restart:
	$(COMPOSE) down
	$(COMPOSE) up -d

logs:
	$(COMPOSE) logs -f --tail=200

ps:
	$(COMPOSE) ps

validate:
	$(COMPOSE) config

bootstrap:
	$(COMPOSE) exec -T dagster dagster job execute -m atlas_pipeline.definitions -j atlas_bootstrap_job

dagster-shell:
	$(COMPOSE) exec dagster sh

generate-datasets:
	$(PYTHON) scripts/run_generate_practice_datasets.py $(DATASET_ARGS)