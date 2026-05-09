COMPOSE=docker compose

.PHONY: build up down destroy restart logs ps validate bootstrap dagster-shell

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