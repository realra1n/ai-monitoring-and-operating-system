SHELL := /bin/bash
ROOT := $(shell pwd)
COMPOSE := docker compose -f $(ROOT)/deploy/docker-compose.yml

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f --tail=200

ps:
	$(COMPOSE) ps

restart:
	$(COMPOSE) restart
