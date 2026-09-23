# Development environment helpers

COMPOSE := docker compose
COMPOSE_AMAVIS := $(COMPOSE) -f docker-compose.yml -f docker/compose.amavis.yml

.PHONY: up up-amavis down test

## Start the development environment without amavis
up:
	$(COMPOSE) up $(ARGS)

## Start the development environment with amavis (MariaDB + amavisd)
up-amavis:
	$(COMPOSE_AMAVIS) up $(ARGS)

## Stop the development environment (both variants)
down:
	$(COMPOSE_AMAVIS) down $(ARGS)

## Run the python test suite in the running api container
test:
	docker exec modoboa_api sh -c 'cd test_project && python manage.py test --keepdb $(or $(TESTS),modoboa)'
