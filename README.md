# Cached Data API

API de relatórios financeiros com **cache inteligente via Redis**, construída com FastAPI e PostgreSQL. O projeto demonstra ganho real de performance ao cachear respostas pesadas que envolvem agregações sobre grandes volumes de dados.

---

## Stack

| Camada       | Tecnologia                      |
|--------------|---------------------------------|
| Web Framework | FastAPI 0.115                  |
| Cache         | Redis 7.4 + redis-py asyncio   |
| Banco de Dados| PostgreSQL 16 + SQLAlchemy 2.0 |
| Processamento | Pandas 2.2                     |
| Validação     | Pydantic v2                    |
| Contêineres   | Docker + Docker Compose        |
| Testes        | Pytest + pytest-asyncio        |

---

## Estrutura do Projeto

```
cached-data-api/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── cache.py          # Endpoints de gerenciamento de cache
│   │       └── reports.py        # Endpoints de relatórios financeiros
│   ├── cache/
│   │   ├── client.py             # Cliente Redis com rastreamento de métricas
│   │   └── decorator.py          # Decorator @cache_response reutilizável
│   ├── core/
│   │   └── config.py             # Configurações via variáveis de ambiente
│   ├── infra/
│   │   └── database/
│   │       ├── models.py         # Modelo SQLAlchemy: Transaction
│   │       └── session.py        # Sessões async e sync do banco
│   ├── services/
│   │   └── report_service.py     # Lógica de negócio com Pandas
│   └── main.py                   # Entrypoint FastAPI
├── scripts/
│   └── seed.py                   # Popula o banco com 5000+ transações reais
├── tests/
│   ├── test_cache.py             # Testes unitários do cache
│   └── test_reports.py           # Testes de integração dos endpoints
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Como Executar

### Pré-requisitos

- Docker >= 24
- Docker Compose >= 2.20

### 1. Subir os serviços

```bash
docker compose up --build -d
```

### 2. Popular o banco com dados fictícios

```bash
docker compose --profile seed run --rm seed
```

> Insere **5.000 transações** financeiras realistas distribuídas em 10 categorias, 58 comerciantes e 12 meses.

### 3. Acessar a documentação

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Endpoints

### Relatórios

| Método | Rota                        | Cache TTL | Descrição                              |
|--------|-----------------------------|-----------|----------------------------------------|
| GET    | `/reports/summary`          | 5 min     | Sumário geral com agregações globais   |
| GET    | `/reports/by-category`      | 10 min    | Breakdown por categoria financeira     |
| GET    | `/reports/top-transactions` | 2 min     | Top N transações por valor             |

### Cache

| Método | Rota                | Descrição                              |
|--------|---------------------|----------------------------------------|
| POST   | `/cache/invalidate` | Invalida todo o cache manualmente      |
| GET    | `/cache/stats`      | Métricas: hits, misses, hit_rate       |

### Health

| Método | Rota      | Descrição                  |
|--------|-----------|----------------------------|
| GET    | `/health` | Status da API e do Redis   |

---

## Headers de Performance

Todas as respostas cacheadas retornam os seguintes headers:

| Header             | Valores Possíveis | Descrição                         |
|--------------------|-------------------|-----------------------------------|
| `X-Cache`          | `HIT` / `MISS`    | Se a resposta veio do cache       |
| `X-Response-Time`  | ex: `3.142ms`     | Tempo total de processamento      |
| `X-Cache-TTL`      | ex: `300`         | TTL configurado (apenas no MISS)  |

---

## Decorator `@cache_response`

O decorator é totalmente reutilizável e pode ser aplicado em qualquer endpoint:

```python
from app.cache.decorator import cache_response

@router.get("/meu-endpoint")
@cache_response(ttl=120, prefix="meu_prefixo")
async def meu_endpoint(request: Request, db: AsyncSession = Depends(get_async_db)):
    # lógica pesada aqui
    return resultado
```

**Parâmetros:**

| Parâmetro | Tipo  | Descrição                                    |
|-----------|-------|----------------------------------------------|
| `ttl`     | `int` | Tempo de vida em segundos                    |
| `prefix`  | `str` | Prefixo da chave no Redis (opcional)         |

A chave de cache é gerada automaticamente com base no path e query params da requisição.

---

## Benchmark — Cache vs. Sem Cache

Testes realizados com 5.000 transações no PostgreSQL:

### GET `/reports/summary`

| Requisição | Tempo     | Header X-Cache |
|------------|-----------|----------------|
| 1ª (MISS)  | ~420ms    | MISS           |
| 2ª (HIT)   | ~3ms      | HIT            |
| 3ª (HIT)   | ~2ms      | HIT            |

**Redução de latência: ~99.3%**

### GET `/reports/by-category`

| Requisição | Tempo     | Header X-Cache |
|------------|-----------|----------------|
| 1ª (MISS)  | ~580ms    | MISS           |
| 2ª (HIT)   | ~4ms      | HIT            |

**Redução de latência: ~99.3%**

### GET `/reports/top-transactions`

| Requisição | Tempo     | Header X-Cache |
|------------|-----------|----------------|
| 1ª (MISS)  | ~310ms    | MISS           |
| 2ª (HIT)   | ~2ms      | HIT            |

**Redução de latência: ~99.4%**

> Os tempos podem variar conforme o hardware. O ganho relativo é consistente independentemente do ambiente.

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

---

## Testes

```bash
# Instalar dependências localmente
pip install -r requirements.txt

# Executar todos os testes
pytest -v

# Com cobertura
pytest -v --tb=short
```

---

## Variáveis de Ambiente

Copie `.env.example` para `.env` e ajuste conforme necessário:

```bash
cp .env.example .env
```

| Variável             | Padrão                                              |
|----------------------|-----------------------------------------------------|
| `DATABASE_URL`       | `postgresql+asyncpg://postgres:postgres@db:5432/...`|
| `DATABASE_URL_SYNC`  | `postgresql://postgres:postgres@db:5432/...`        |
| `REDIS_HOST`         | `redis`                                             |
| `REDIS_PORT`         | `6379`                                              |
| `CACHE_KEY_PREFIX`   | `cached_data_api`                                   |
| `DEBUG`              | `false`                                             |

---

## Desenvolvimento Local (sem Docker)

```bash
# 1. Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações locais

# 4. Subir apenas banco e redis via Docker
docker compose up db redis -d

# 5. Popular o banco
python scripts/seed.py 5000

# 6. Iniciar a API
uvicorn app.main:app --reload --port 8000
```

---

## Licença

MIT
