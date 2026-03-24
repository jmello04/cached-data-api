# Changelog

Todas as mudanças relevantes deste projeto estão documentadas aqui.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/)
e o versionamento segue [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [1.0.0] — 2026-03-24

### Adicionado

- **API FastAPI assíncrona** com 3 endpoints de relatórios financeiros
  - `GET /reports/summary` — resumo geral com cache de 5 minutos
  - `GET /reports/by-category` — agrupamento por categoria com cache de 10 minutos
  - `GET /reports/top-transactions` — top N transações com cache de 2 minutos e parâmetros `limit` e `order_by`
- **Cache inteligente via Redis assíncrono** com decorator reutilizável `@cache_response(ttl, prefix)`
- **Headers automáticos** `X-Cache: HIT | MISS`, `X-Response-Time` e `X-Cache-TTL` em todas as respostas
- **Schemas Pydantic v2** para validação e documentação Swagger completa
- **SQLAlchemy 2.0 assíncrono** com `AsyncSession` e `AsyncEngine`
- **Script de seed** com 5.000 transações fictícias em 10 categorias brasileiras
- **Endpoints de gerenciamento** `POST /cache/invalidate` e `GET /cache/stats`
- **Endpoint raiz** `GET /` com informações da API e link para docs
- **Health check** `GET /health` com verificação de conectividade Redis
- **Suite de testes** com 21 testes assíncronos (pytest + pytest-asyncio)
- **GitHub Actions CI** executando testes em Python 3.12 e 3.13 a cada push
- **Arquivos de comunidade GitHub**
  - `.github/CONTRIBUTING.md` — guia de contribuição
  - `.github/SECURITY.md` — política de segurança
  - `.github/PULL_REQUEST_TEMPLATE.md` — template de pull request
  - `.github/ISSUE_TEMPLATE/bug_report.md` — template de bug report
  - `.github/ISSUE_TEMPLATE/feature_request.md` — template de feature request
- **Docker Compose** com serviços `api`, `db` (PostgreSQL 16), `redis` (Redis 7.4) e `seed`
- **Makefile** com atalhos para as tarefas mais comuns
- **Licença MIT**

### Técnico

- Redis assíncrono via `redis.asyncio` com conexão lazy e fechamento no lifespan
- Chave de cache gerada com SHA-256 do path + query params ordenados
- Contadores de hits/misses em memória com reset manual via `POST /cache/invalidate`
- `pytest.ini` com `asyncio_mode = auto` e fixtures compartilhadas em `conftest.py`
- Variáveis de ambiente com validação e defaults via pydantic-settings
