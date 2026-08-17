# Mapa Mitológico RAG

Agente inteligente que transforma perguntas sobre mitologia grega em respostas fundamentadas, citações rastreáveis e um mapa visual de conceitos relacionados.

**Demonstração pública:** http://137.131.224.135
**Health check:** http://137.131.224.135/health
**Desafio:** Alura/Oracle Next Education — Challenge Agente de IA

## Visão geral

O sistema usa como fonte o livro público *The Age of Fable, or, Stories of Gods and Heroes*, de Thomas Bulfinch. A pessoa faz uma pergunta, o agente recupera os trechos mais relevantes do PDF, gera uma resposta com o Claude e apresenta os conceitos encontrados em um grafo interativo.

A resposta só é aceita quando:

- há contexto suficiente no documento;
- as citações correspondem literalmente aos trechos recuperados;
- cada fonte mantém o arquivo e a página de origem;
- o conteúdo pode ser visualmente explorado e expandido.

O corpus possui 495 páginas e é versionado no projeto em:

    data/ageoffableorstor00bulf_0.pdf

## Entregáveis do Challenge

- Repositório público com código-fonte organizado.
- Histórico de commits representando a evolução do projeto.
- README com arquitetura, tecnologias, execução e exemplos.
- Agente funcional baseado em documento PDF.
- Pipeline de leitura, normalização, chunking, embeddings e recuperação.
- Respostas geradas com evidências e validação de grounding.
- Interface visual com mapa de conceitos, relações e fontes.
- Deploy público realizado na OCI.
- Demonstração acessível em http://137.131.224.135.

## Arquitetura

    Pergunta
        │
        ▼
    FastAPI
        │
        ▼
    Workflow LangGraph
        │
        ├── Recuperação semântica no ChromaDB
        │       └── FastEmbed/ONNX
        │
        ├── Avaliação de suficiência do contexto
        │       └── Reformulação da busca quando necessário
        │
        ├── Geração estruturada com Anthropic Claude
        │
        ├── Validação literal das citações
        │
        └── Extração de conceitos e relações
                │
                ▼
        Interface HTML/CSS/JavaScript
        └── Mapa interativo com fontes

### Módulos principais

- app.py: rotas FastAPI, health check e entrega da interface.
- src/ingest.py: leitura do PDF, normalização e divisão em chunks.
- src/vector_store.py: embeddings FastEmbed e persistência ChromaDB.
- src/retrieval.py: busca semântica e avaliação de relevância.
- src/generation.py: geração de respostas com Claude e validação de citações.
- src/grounding.py: conferência literal das evidências.
- src/graph_extraction.py: extração dos conceitos e relações do grafo.
- src/workflow.py: orquestração do fluxo RAG com LangGraph.
- static/: comportamento e apresentação do mapa.
- templates/: página principal da aplicação.
- tests/: testes determinísticos com unittest e mocks.

## Tecnologias

| Camada | Tecnologia |
| --- | --- |
| API | Python 3.14 e FastAPI |
| Servidor | Uvicorn |
| Orquestração | LangGraph |
| Modelo generativo | Anthropic Claude Haiku |
| Embeddings | FastEmbed/ONNX |
| Banco vetorial | ChromaDB |
| Documento | PDF processado com pypdf |
| Interface | HTML, CSS, JavaScript e SVG |
| Deploy | Docker Compose, Caddy e Oracle Cloud Infrastructure |
| Testes | unittest, FastAPI TestClient e mocks |

## Como executar localmente

### Pré-requisitos

- Docker Desktop com o engine Linux ativo;
- uma chave da API Anthropic;
- Git, caso o projeto seja clonado.

### Configuração

No PowerShell:

    Copy-Item .env.example .env

Edite o arquivo .env e preencha:

    ANTHROPIC_API_KEY=sua_chave_anthropic

O arquivo .env não deve ser versionado.

### Execução recomendada com Docker

    docker compose up --build -d
    docker compose ps
    docker compose logs -f app

A aplicação ficará disponível em:

- Interface: http://localhost:8080
- Health check: http://localhost:8080/health
- Documentação OpenAPI: http://localhost:8080/docs

A primeira inicialização baixa o modelo de embeddings e cria o índice persistente do ChromaDB. As próximas inicializações reutilizam os volumes Docker.

Para parar os containers sem apagar os dados:

    docker compose down

Para remover também o índice e forçar uma nova ingestão:

    docker compose down -v

### Execução sem Docker

No PowerShell:

    py -3.14 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    python -m src.ingest data/ageoffableorstor00bulf_0.pdf --rebuild
    uvicorn app:app --reload

No Linux:

    python3.14 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    python -m src.ingest data/ageoffableorstor00bulf_0.pdf --rebuild
    uvicorn app:app --reload

## Exemplos de perguntas

O agente consegue responder perguntas como:

- Quem ajudou Perseu a derrotar a Medusa?
- Qual é a relação entre Perséfone e Hades?
- Quem são os filhos de Zeus?
- O que aconteceu durante a Guerra de Troia?
- Qual é a origem de Minerva segundo o documento?
- Quais personagens aparecem relacionados a Hércules?

Quando o PDF não fornece evidência suficiente, o sistema informa que não encontrou contexto aprovado em vez de inventar uma resposta.

## Exemplo de resposta gerada

Pergunta:

    Quem ajudou Perseu a derrotar a Medusa?

Resposta produzida pela demonstração pública:

    Perseu foi ajudado por Minerva e Mercúrio a derrotar a Medusa.
    Minerva lhe emprestou seu escudo e Mercúrio lhe emprestou seus
    sapatos alados. Com a ajuda desses deuses, Perseu se aproximou da
    Medusa enquanto ela dormia e, guiando-se pela imagem dela refletida
    no escudo brilhante que portava, cortou sua cabeça.

Evidência retornada pelo sistema:

- Status: ok
- Contexto suficiente: true
- Fonte: ageoffableorstor00bulf_0.pdf
- Página: 172
- Citações e conceitos disponíveis no mapa interativo

A interface também exibe os nós extraídos, suas relações, os trechos literais e as páginas de origem.

## API

### POST /query

Cria um mapa a partir de uma pergunta.

    {
      "question": "Quem são os filhos de Zeus?"
    }

### POST /expand

Expande um conceito existente.

    {
      "node_id": "concept:2fd805bb52808616",
      "concept": "Zeus"
    }

As duas rotas retornam um contrato semelhante:

    {
      "status": "ok",
      "answer": "Resposta fundamentada em português.",
      "evaluation": {
        "sufficient": true,
        "attempts": 1,
        "final_query": "consulta utilizada",
        "max_score": 0.61
      },
      "nodes": [],
      "edges": [],
      "sources": []
    }

Rotas auxiliares:

- GET /health: verifica se a API está disponível.
- GET /docs: documentação OpenAPI interativa.

## Deploy na OCI

A aplicação está publicada em uma VM Compute da OCI com Ubuntu 24.04, Docker Engine, Docker Compose, Caddy e volumes persistentes para o índice vetorial e o cache do modelo.

### Configuração usada

- Região: Brazil East (São Paulo)
- Forma: VM.Standard.E2.1.Micro
- Memória: 1 GB
- IP público: 137.131.224.135
- Porta pública em uso: 80 (HTTP)
- Porta interna da API: 8000, não exposta diretamente
- Proxy: Caddy
- Reinício automático: habilitado no Docker

A demonstração pode ser acessada em:

    http://137.131.224.135

O endereço atual usa HTTP. A porta 443 está reservada no proxy, mas o HTTPS automático depende de um domínio apontado para o IP público.

### Ajustes para a VM pequena

Para manter o sistema funcional em uma VM de 1 GB, o deploy utiliza:

    EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
    CHUNK_SIZE=2000
    CHUNK_OVERLAP=200
    OMP_NUM_THREADS=1
    OPENBLAS_NUM_THREADS=1
    MKL_NUM_THREADS=1
    NUMEXPR_NUM_THREADS=1
    ORT_NUM_THREADS=1

O modelo multilíngue configurado por padrão oferece melhor busca entre idiomas, mas exige mais recursos. Em uma VM maior, ele pode ser reativado removendo o override do .env.

### Atualização do deploy

Na VM, depois de transferir uma nova versão:

    cd /home/ubuntu/rag-mitologia
    docker compose up -d --build
    docker compose ps
    docker compose logs -f app

As portas 80 e 443 precisam estar liberadas na Security List ou Network Security Group da VCN. A porta interna 8000 não deve ser aberta para a Internet.

## Validação

Testes automatizados:

    python -m unittest discover -s tests -v
    python -m pip check

Validações do deploy:

    docker compose config -q
    curl http://localhost/health

O fluxo público foi validado com:

- página principal respondendo HTTP 200;
- health check respondendo status ok;
- pergunta em inglês retornando resposta fundamentada;
- pergunta em português retornando status ok, contexto suficiente e fontes;
- containers app e proxy em estado saudável.

## Configuração

As principais variáveis são:

| Variável | Finalidade |
| --- | --- |
| ANTHROPIC_API_KEY | Chave da API Anthropic |
| ANTHROPIC_MODEL | Modelo de geração |
| EMBEDDING_MODEL | Modelo de embeddings |
| CHROMA_PATH | Diretório persistente do ChromaDB |
| CHROMA_COLLECTION | Nome da coleção vetorial |
| PDF_PATH | Caminho do documento-fonte |
| RETRIEVAL_TOP_K | Quantidade de chunks recuperados |
| RETRIEVAL_MIN_SCORE | Score mínimo de relevância |
| MAX_RETRIEVAL_ATTEMPTS | Limite de tentativas de recuperação |
| CHUNK_SIZE | Tamanho dos chunks na ingestão |
| CHUNK_OVERLAP | Sobreposição entre chunks |

## Segurança e limitações

- A chave Anthropic é lida somente por variável de ambiente.
- O arquivo .env é ignorado pelo Git.
- A API interna não é publicada diretamente.
- As respostas dependem da cobertura do documento-fonte.
- O IP público atual pode mudar se a VM for recriada sem um endereço reservado.
- O projeto é uma demonstração educacional de RAG, não uma fonte histórica definitiva.

## Licença e fonte

O corpus utilizado é o livro *The Age of Fable, or, Stories of Gods and Heroes*, de Thomas Bulfinch, disponível em domínio público no Internet Archive:

https://archive.org/details/ageoffableorstor00bulf_0

O código deste projeto é destinado ao Challenge Alura/Oracle Next Education.
