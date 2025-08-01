# cronicas-monitor

Projeto DevOps para monitorar latência, disponibilidade e resposta HTTP de sites, com visualização no Grafana e deploy local e em nuvem.

---

## Índice

- [Descrição](#descrição)
- [Funcionalidades](#funcionalidades)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Executar Localmente](#como-executar-localmente)
- [Monitoramento e Visualização](#monitoramento-e-visualização)
- [Deploy em Nuvem](#deploy-em-nuvem)
- [Automação de Migração (Supabase)](#automação-de-migração-supabase)
- [High Level Design (HLD)](#high-level-design-hld)
- [Repositorios](#repositórios)
- [Licença](#licença)

---

## Descrição

O **cronicas-monitor** é uma solução DevOps para monitoramento de infraestrutura, realizando:
- Ping em hosts configurados
- Checagem HTTP de sites
- Coleta de métricas da API ViaIPE
- Armazenamento dos dados em PostgreSQL
- Visualização dos dados no Grafana

---

## Funcionalidades

- **Monitoramento de Latência e Perda de Pacotes:** via ping em hosts definidos.
- **Monitoramento HTTP:** mede latência e status de resposta de sites.
- **Coleta ViaIPE:** integra com a API ViaIPE para métricas de clientes.
- **Armazenamento:** todas as métricas são salvas em um banco PostgreSQL.
- **Visualização:** dashboards prontos no Grafana.
- **Automação:** deploy local via Docker Compose e migração automática para Supabase via GitHub Actions.

---

## Estrutura do Projeto

```
cronicas-monitor/ 
├── .env # Variáveis de ambiente 
├── docker-compose.yml # Deploy local (Postgres, Grafana, Agent)
├── Dockerfile 
└── requirements.txt 
├── images/ # Imagens do grafana local e cloud
├── agent/ 
│ ├── main.py # Código principal do agente de coleta 
├── db/ 
│ └── init.sql # Script de criação das tabelas 
├── .github.workflows/ 
│ └── db-migration.yml # Workflow de migração para Supabase 
└── README.md
```

---

## Como Executar Localmente

1. **Configure as variáveis de ambiente**

> O arquivo `.env` deverá ser criado na raiz do projeto, abaixo está o conteúdo a ser copiado para o arquivo criado.
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cronicas_monitor
DB_USER=postgres
DB_PASSWORD=
POSTGRES_PASSWORD=
```

   Edite o arquivo `.env` e defina:
    - `POSTGRES_PASSWORD` (senha do banco para o container)
    - `DB_PASS` (senha do banco para o agent)

2. **Suba os serviços com Docker Compose**

   ```sh
   docker-compose up --build
   ```

- O banco ficará disponível em localhost:5432
- O Grafana ficará disponível em http://localhost:5000 (ou a porta definida)

3. **Acesse o Grafana**

- Usuário padrão: admin
- Senha padrão: admin (primeiro acesso)

## Monitoramento e Visualização
- O agente (main.py) coleta métricas a cada 60 segundos e armazena no banco.
- O Grafana pode ser configurado para visualizar as tabelas ping, http_check e viaipe.
- O script SQL `init.sql` cria as tabelas necessárias automaticamente.

## Deploy em Nuvem
- Para rodar em nuvem (ex: Supabase), use o arquivo `docker-compose.cloud.yml` e configure as variáveis de ambiente dentro do Github para apontar para o banco remoto.
- O workflow db-migration.yml automatiza a aplicação do script SQL no Supabase a cada alteração em init.sql.

## Automação de Migração (AWS EC2 + Supabase + Grafana Cloud)
- A Aplicação está rodando em uma Instância EC2 na AWS, gerando o conteúdo que é enviado para as tabelas no Supabase.
> Devido a problemas em rodar a aplicação em plataformas como Railway, Fly.io, Render. Decidi subir na instância pois já tenho o ambiente pronto.
- O workflow GitHub Actions detecta mudanças em init.sql e executa a migração no banco Supabase usando as variáveis de ambiente do repositório (DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME). Que foram criados nas `Secrets` do repositório com seus respectivos valores.
- Os dashboards também serão possíveis encontrar na plataforma [Grafana Cloud](https://cronicasnv.grafana.net/).
> Snapshot do Dashboard pode ser visualizado através deste link. [CLIQUE AQUI.](https://cronicasnv.grafana.net/public-dashboards/26d2af2f4f4846528758c88ca2db600a) <br>
> Printscreens tirados do Grafana Local se encontram na pasta `images`. [CLIQUE AQUI.](./images) <br>
> Houve diferenças entre as informações de Ping e Requisições HTTP da Instância EC2 e a Máquina Local.


## High Level Design (HLD)

```mermaid
flowchart TD
    subgraph Agent Container
        A1[main.py]
    end

    subgraph Banco de Dados
        B1[(PostgreSQL)]
    end

    subgraph Visualização
        C1[Grafana]
    end

    subgraph Internet
        D1[Hosts e Sites Monitorados]
        D2[API Viaipe]
    end

    D1 -- Ping/HTTP --> A1
    D2 -- API JSON --> A1
    A1 -- Métricas (ping, http, viaipe) --> B1
    C1 -- Consulta dados --> B1
```

## Repositórios

### Crônicas
- O Crônicas App é uma aplicação web que centraliza conteúdos do projeto "Crônicas do Nada Ver". A aplicação exibe informações, links para redes sociais e outros conteúdos relacionados. O projeto utiliza uma arquitetura moderna com integração contínua (CI) e entrega contínua (CD) para garantir qualidade e automação no desenvolvimento e deploy. [Cronicas APP](https://github.com/masneto/cronicas-app)<br>
- Repositório de GitHub Actions customizadas para automação dos workflows do projeto Crônicas App. [Cronicas APP - Actions](https://github.com/masneto/cronicas-actions)<br>
- Desafio técnico SRE. [Desafio](https://github.com/masneto/sre-challenge-elo) <br>
- Projeto Bootcamp The Cloud Bootcamp. [Projeto](https://github.com/masneto/cloudmart) <br>

## Licença
MIT