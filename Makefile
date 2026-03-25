SHELL := /bin/bash

.PHONY: help up down build seed test logs shell clean

help:
	@echo ""
	@echo "  Cached Data API — Comandos disponíveis"
	@echo "  ──────────────────────────────────────"
	@echo "  make up      Sobe todos os serviços em background"
	@echo "  make down    Para e remove os contêineres"
	@echo "  make build   Reconstrói as imagens Docker"
	@echo "  make seed    Popula o banco com 5000 transações"
	@echo "  make test    Executa a suíte de testes"
	@echo "  make logs    Exibe logs da API em tempo real"
	@echo "  make shell   Abre um shell dentro do contêiner da API"
	@echo "  make clean   Remove volumes, imagens e contêineres"
	@echo ""

up:
	docker compose up --build -d
	@echo ""
	@echo "  API disponível em: http://localhost:8000"
	@echo "  Docs (Swagger):    http://localhost:8000/docs"
	@echo ""

down:
	docker compose down

build:
	docker compose build --no-cache

seed:
	docker compose --profile seed run --rm seed

test:
	pytest -v --tb=short

logs:
	docker compose logs -f api

shell:
	docker compose exec api bash

clean:
	docker compose down -v --rmi local
	@echo "Volumes e imagens locais removidos."
