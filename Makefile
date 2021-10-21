COMPOSE = docker-compose
COMPOSE_BUILD_ENV = COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1
COMPOSE_BUILD_FLAGS = --progress=plain

build:
	$(COMPOSE_BUILD_ENV) $(COMPOSE) build $(COMPOSE_BUILD_FLAGS)

run:
	$(COMPOSE_BUILD_ENV) $(COMPOSE) up -d

runci:
	$(COMPOSE_BUILD_ENV) $(COMPOSE) up -d app

enter:
	$(COMPOSE) exec app bash

createsuperuser:
	$(COMPOSE) exec app python manage.py createsuperuser

lint:
	$(COMPOSE) exec -T app pre-commit run --all-files

test:
	$(COMPOSE) exec -T app python manage.py test

stop:
	$(COMPOSE) down
