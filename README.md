# CIC Digital — API de leitura

API HTTP para leitura do **Catecismo da Igreja Católica**, pensada para servir clientes mobile (Android em fase inicial) e outros consumidores HTTP.

## O que é

Serviço de **núcleo de leitura**: entrega de conteúdo estático estruturado (sumário, capítulos, blocos de texto e assets), no padrão de soluções de ebook. A primeira versão cobre apenas leitura; funcionalidades adicionais virão em módulos futuros.

## Contrato e versionamento

- API documentada em **OpenAPI 3**
- Rotas públicas sob o prefixo **`/v1/`**, para evolução sem quebrar clientes desatualizados
- Documentação interativa disponível na própria API (Swagger UI / ReDoc) quando o serviço estiver em execução

## Stack (resumo)

- **Python** + **FastAPI**
- **PostgreSQL** + **SQLAlchemy** + **Alembic** — API e banco na mesma rede Docker
- Conteúdo estruturado no schema **`content`** (hierarquia CIC + parágrafos numerados)

## Status

Projeto em fase inicial — implementação do núcleo de leitura em andamento.
