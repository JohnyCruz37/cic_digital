# CIC Digital — API de leitura

API HTTP para leitura do **Catecismo da Igreja Católica**, pensada para servir clientes mobile (Android em fase inicial) e outros consumidores HTTP.

## O que é

Serviço de **núcleo de leitura**: entrega de conteúdo estático estruturado (sumário, capítulos, blocos de texto e assets), no padrão de soluções de ebook. A primeira versão cobre apenas leitura; funcionalidades adicionais virão em módulos futuros.

## Contrato e versionamento

- API documentada em **OpenAPI 3**
- Rotas públicas sob o prefixo **`/api/v1/`**
- Documentação interativa: `/docs` (Swagger) e `/redoc` (ReDoc)
- Probes operacionais: `GET /health` (liveness) e `GET /ready` (readiness)

## Stack

- **Python 3.12** + **FastAPI**
- **PostgreSQL** + **SQLAlchemy 2** + **Alembic**
- **Pydantic Settings** para configuração via `.env`
- **Docker Compose** — API e banco na mesma rede

## Estrutura do projeto

```
src/cic_digital/
├── main.py                 # entry point (setup_logger + app)
├── api/
│   ├── factory.py          # create_app()
│   ├── router.py           # agregador de rotas
│   ├── middleware.py       # logging, correlation ID, timing
│   ├── exception_handlers.py
│   ├── endpoints/          # rotas de infra (/health, /ready)
│   └── v1/                 # rotas versionadas
├── core/
│   ├── config.py           # Pydantic Settings
│   ├── logger.py
│   ├── exceptions.py
│   └── security.py         # JWT (preparado)
├── db/
│   └── connection.py       # SQLAlchemy engine + session factory
├── models/                 # entidades ORM (SQLAlchemy)
├── dtos/                   # objetos de transferência internos (Service ↔ Repository)
├── schemas/                # contratos HTTP (request/response da API)
├── repositories/           # acesso a dados
├── services/               # regras de negócio
└── utils/
```

### Camadas de dados

| Camada | Pacote | Responsabilidade |
|--------|--------|------------------|
| ORM | `models/` | Mapeamento tabelas ↔ classes SQLAlchemy |
| DTO | `dtos/` | Dados internos entre Repository e Service |
| Schema | `schemas/` | Contrato exposto na API (OpenAPI) |

**DTO vs Schema:** DTOs não vazam para HTTP — encapsulam o domínio internamente. Schemas traduzem DTOs (ou agregados de serviço) para o formato da resposta/request da API. Endpoints de infraestrutura (ex.: `/health`) podem usar schemas diretamente, sem passar por Service.

**Fluxo de camadas (negócio):**

```
Router → Schema → Service → DTO → Repository → ORM Model → Database
```

1. **Router** recebe/valida schema de entrada e devolve schema de saída.
2. **Service** aplica regras de negócio sobre DTOs.
3. **Repository** lê/grava ORM models e retorna DTOs (ou ORM models convertidos no service).
4. **Mapper** (no service ou endpoint): `DTO → Schema` na resposta; `Schema → DTO` na entrada.

DTOs herdam de `BaseDTO` (`frozen=True`, `from_attributes=True`) para imutabilidade e conversão a partir de entidades ORM.

## Configuração

```bash
cp .env.example .env
```

Principais variáveis:

| Variável | Descrição |
|----------|-----------|
| `APP_ENV` | `development` ou `production` |
| `LOG_LEVEL` | Nível de log da aplicação |
| `LOG_FILE` | Caminho do arquivo de log |
| `POSTGRES_*` | Conexão **admin** — Alembic, seeds e manutenção |
| `POSTGRES_READ_*` | Conexão **read-only** — padrão da API e `/ready` |
| `DATABASE_URL` | (opcional) sobrescreve URL admin |
| `DATABASE_READ_URL` | (opcional) sobrescreve URL read-only |
| `JWT_*` | Configurações de segurança (JWT) |

A API usa por padrão o usuário `cic_read` (somente `SELECT` no schema `content`). Migrations e operações de manutenção usam o usuário admin `cic`.

## Execução local

```bash
pip install -e ".[dev]"
docker compose up -d postgres
```

**Migrations** — escolha uma opção:

```bash
# Recomendado com Docker: roda dentro do container (POSTGRES_HOST=postgres)
docker compose exec api alembic upgrade head

# Ou no host: exige POSTGRES_HOST=localhost no .env e Postgres exposto na porta 5432
alembic upgrade head
```

```bash
uvicorn cic_digital.main:app --host 0.0.0.0 --port 8000 --reload --log-level critical
```

O `alembic upgrade head` cria o schema `content`, as tabelas e o usuário `cic_read` com permissões de leitura (migration 002).

> Se aparecer `could not translate host name "postgres"`, você rodou Alembic **no host** com `POSTGRES_HOST=postgres`. Use `localhost` no `.env` ou execute via `docker compose exec api`.

## Docker

```bash
docker compose up --build
```

Dentro do container `api`, rode as migrations antes do primeiro uso (se ainda não aplicadas):

```bash
docker compose exec api alembic upgrade head
```

- API: `http://localhost:8000`
- Health: `http://localhost:8000/health`
- Ready: `http://localhost:8000/ready`
- Índice: `http://localhost:8000/api/v1/read/index`
- Docs: `http://localhost:8000/docs`

## Testes

```bash
pytest
RUN_DB_TESTS=1 pytest   # smoke tests de schema (requer Postgres)
```

## Status

Infraestrutura base da API implementada. Primeiro endpoint de negócio: `GET /api/v1/read/index` (árvore estrutural de navegação).
