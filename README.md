# Cached Data API

<p align="center">
  <a href="https://github.com/jmello04/cached-data-api/actions/workflows/ci.yml">
    <img src="https://github.com/jmello04/cached-data-api/actions/workflows/ci.yml/badge.svg" alt="CI">
  </a>
  <img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Redis-7.4-DC382D?style=flat-square&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Testes-21%20passed-brightgreen?style=flat-square&logo=pytest" alt="Testes">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License">
</p>

> API de relatórios financeiros com **cache inteligente via Redis**.
> Processa 5.000+ transações com Pandas e demonstra ganho real de performance através de métricas comparativas de latência.

---

## Sumário

- [Stack](#stack)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Executar](#como-executar)
- [Endpoints](#endpoints)
- [Decorator `@cache_response`](#decorator-cache_response)
- [Benchmark](#benchmark--cache-vs-sem-cache)
- [Métricas de Cache](#métricas-de-cache)
- [Testes](#testes)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Desenvolvimento Local](#desenvolvimento-local-sem-docker)

---

## Stack

| Camada         | Tecnologia                        |
|----------------|-----------------------------------|
| Web Framework  | FastAPI 0.115 + Uvicorn           |
| Cache          | Redis 7.4 (redis-py asyncio)      |
| Banco de Dados | PostgreSQL 16 + SQLAlchemy 2.0    |
| Processamento  | Pandas 2.2 + NumPy 2.2            |
| Validação      | Pydantic v2 + pydantic-settings   |
| Contêineres    | Docker + Docker Compose v2        |
| Testes         | Pytest + pytest-asyncio           |

---

## Estrutura do Projeto

```
cached-data-api/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── cache.py            # Endpoints de gerenciamento de cache
│   │       └── reports.py          # Endpoints de relatórios financeiros
│   ├── cache/
│   │   ├── client.py               # Cliente Redis com rastreamento de métricas
│   │   └── decorator.py            # Decorator @cache_response reutilizável
│   ├── core/
│   │   └── config.py               # Configurações via variáveis de ambiente
│   ├── infra/
│   │   └── database/
│   │       ├── base.py             # Base declarativa do SQLAlchemy
│   │       ├── models.py           # Modelo Transaction
│   │       └── session.py          # Sessões async/sync e criação de tabelas
│   ├── services/
│   │   └── report_service.py       # Lógica de negócio com Pandas
│   └── main.py                     # Entrypoint FastAPI + lifespan
├── scripts/
│   └── seed.py                     # Popula o banco com transações fictícias
├── tests/
│   ├── conftest.py                 # Fixtures compartilhadas (pytest)
│   ├── test_cache.py               # Testes unitários do cliente de cache
│   └── test_reports.py             # Testes de integração dos endpoints
├── Makefile                        # Atalhos para tarefas comuns
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
├── requirements.txt
└── .env.example
```

---

## Como Executar

### Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) >= 24
- [Docker Compose](https://docs.docker.com/compose/) >= 2.20

### 1. Subir os serviços

```bash
make up
# ou: docker compose up --build -d
```

### 2. Popular o banco com dados fictícios

```bash
make seed
# ou: docker compose --profile seed run --rm seed
```

> Insere **5.000 transações** financeiras realistas distribuídas em:
> - 10 categorias (Alimentação, Tecnologia, Investimento…)
> - 58 comerciantes
> - 12 meses de histórico

### 3. Acessar a documentação interativa

| Interface | URL |
|-----------|-----|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/health |

---

## Endpoints

### Relatórios Financeiros

| Método | Rota | Cache TTL | Descrição |
|--------|------|-----------|-----------|
| `GET` | `/reports/summary` | 5 min | Sumário global com agregações estatísticas |
| `GET` | `/reports/by-category` | 10 min | Breakdown por categoria com top merchant |
| `GET` | `/reports/top-transactions` | 2 min | Top N transações por valor (`?limit=10`) |

### Gerenciamento de Cache

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/cache/invalidate` | Invalida todo o cache manualmente |
| `GET` | `/cache/stats` | Métricas: hits, misses, hit_rate, memória |

### Health

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Status da API e conectividade com Redis |
| `GET` | `/` | Informações gerais da API |

---

## Headers de Performance

Todas as respostas retornam:

| Header | Valores | Descrição |
|--------|---------|-----------|
| `X-Cache` | `HIT` / `MISS` | Indica se a resposta veio do cache |
| `X-Response-Time` | ex: `3.142ms` | Latência total da requisição |
| `X-Cache-TTL` | ex: `300` | TTL configurado (apenas em MISS) |

---

## Decorator `@cache_response`

Totalmente reutilizável em qualquer endpoint da aplicação:

```python
from app.cache.decorator import cache_response

@router.get("/meu-endpoint")
@cache_response(ttl=120, prefix="meu_prefixo")
async def meu_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    # Lógica pesada aqui — será cacheada automaticamente
    return resultado
```

**Parâmetros:**

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `ttl` | `int` | Tempo de vida em segundos |
| `prefix` | `str` | Prefixo da chave no Redis (padrão: nome da função) |

A **chave de cache** é gerada automaticamente com SHA-256 a partir do path + query params, garantindo isolamento por endpoint e por combinação de parâmetros.

---

## Benchmark — Cache vs Sem Cache

Resultados medidos com **5.000 transações** no PostgreSQL (hardware de desenvolvimento):

### `GET /reports/summary`

| Requisição | Latência | `X-Cache` |
|------------|----------|-----------|
| 1ª (cold)  | ~420 ms  | `MISS`    |
| 2ª         | ~3 ms    | `HIT`     |
| 3ª         | ~2 ms    | `HIT`     |

**Ganho: redução de ~99% na latência**

---

### `GET /reports/by-category`

| Requisição | Latência | `X-Cache` |
|------------|----------|-----------|
| 1ª (cold)  | ~580 ms  | `MISS`    |
| 2ª         | ~4 ms    | `HIT`     |

**Ganho: redução de ~99% na latência**

---

### `GET /reports/top-transactions`

| Requisição | Latência | `X-Cache` |
|------------|----------|-----------|
| 1ª (cold)  | ~310 ms  | `MISS`    |
| 2ª         | ~2 ms    | `HIT`     |

**Ganho: redução de ~99% na latência**

> Os valores absolutos variam por hardware. O ganho relativo é consistente em qualquer ambiente.

**Como reproduzir o benchmark:**

```bash
# Primeira chamada (MISS)
curl -s -o /dev/null -w "X-Cache: %header{X-Cache}\nTempo: %{time_total}s\n" \
  http://localhost:8000/reports/summary

# Segunda chamada (HIT)
curl -s -o /dev/null -w "X-Cache: %header{X-Cache}\nTempo: %{time_total}s\n" \
  http://localhost:8000/reports/summary
```

---

## Métricas de Cache

```bash
curl http://localhost:8000/cache/stats
```

```json
{
  "hits": 24,
  "misses": 3,
  "hit_rate": 88.89,
  "active_keys": 3,
  "memory_used": "1.23M"
}
```

**Invalidar manualmente:**

```bash
curl -X POST http://localhost:8000/cache/invalidate
```

---

## Testes

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar todos os testes
make test
# ou: pytest -v --tb=short
```

**Cobertura dos testes:**

| Arquivo | O que testa |
|---------|-------------|
| `test_cache.py` | Lógica de get/set, contadores de hits/misses, hit_rate, reset, resiliência |
| `test_reports.py` | Headers X-Cache/X-Response-Time, validação de parâmetros, endpoints de cache e health |

---

## Variáveis de Ambiente

Copie `.env.example` para `.env`:

```bash
cp .env.example .env
```

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | URL async do PostgreSQL |
| `DATABASE_URL_SYNC` | `postgresql://...` | URL síncrona (seed) |
| `REDIS_HOST` | `redis` | Host do Redis |
| `REDIS_PORT` | `6379` | Porta do Redis |
| `REDIS_PASSWORD` | `` | Senha do Redis (opcional) |
| `CACHE_KEY_PREFIX` | `cached_data_api` | Prefixo global das chaves |
| `DEBUG` | `false` | Habilita logs SQL do SQLAlchemy |

---

## Desenvolvimento Local (sem Docker)

```bash
# 1. Criar e ativar ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações locais (localhost no lugar de db/redis)

# 4. Subir infraestrutura via Docker
docker compose up db redis -d

# 5. Popular o banco
python scripts/seed.py 5000

# 6. Iniciar a API com hot-reload
uvicorn app.main:app --reload --port 8000
```

---

## Makefile — Atalhos

```bash
make help    # Lista todos os comandos disponíveis
make up      # Sobe todos os serviços
make down    # Para os serviços
make seed    # Popula o banco
make test    # Executa os testes
make logs    # Acompanha logs da API
make shell   # Abre shell no contêiner da API
make clean   # Remove contêineres, volumes e imagens locais
```

---

## Licença

[MIT](LICENSE)
