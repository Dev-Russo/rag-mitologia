# Mapa Mitológico RAG

Mapa mental vivo de mitologia grega que transforma respostas fundamentadas em um
grafo interativo. Cada conceito exibido no mapa será vinculado ao trecho exato do
documento usado pelo pipeline RAG.

O projeto está sendo desenvolvido para o **Challenge Alura/Oracle Next Education —
Track Tech AI Builder**.

> **Estado atual:** pipeline RAG implementado e coberto por testes automatizados.
> Falta adicionar e indexar o PDF real de *Bulfinch's Mythology*.

## Tecnologias definidas

- Python 3.14
- FastAPI e Uvicorn
- ChromaDB
- LangChain e LangGraph
- FastEmbed/ONNX com `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Claude Haiku 4.5 por meio do SDK da Anthropic
- HTML, CSS e JavaScript

## Estrutura

```text
.
├── app.py
├── data/
├── screenshots/
├── src/
│   ├── generation.py
│   ├── graph_extraction.py
│   ├── ingest.py
│   ├── retrieval.py
│   ├── vector_store.py
│   └── workflow.py
├── static/
│   ├── graph.js
│   └── style.css
├── templates/
│   └── index.html
├── .env.example
└── requirements.txt
```

## Execução local

### Pré-requisitos

- Python 3.14
- Git

Confirme que o interpretador ativo é o correto:

```bash
python --version
```

### Instalação

Crie e ative um ambiente virtual.

No Linux ou macOS:

```bash
python3.14 -m venv .venv
source .venv/bin/activate
```

No Windows PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Copie o arquivo de configuração:

```bash
cp .env.example .env
```

No Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

A aplicação web inicia mesmo sem uma chave da Anthropic. A chave é obrigatória
para executar o workflow RAG e nunca deve ser versionada.

### Inicialização

```bash
uvicorn app:app --reload
```

Acesse:

- Interface: <http://127.0.0.1:8000>
- Health check: <http://127.0.0.1:8000/health>
- Documentação automática: <http://127.0.0.1:8000/docs>

O health check deve responder:

```json
{"status": "ok"}
```

## Configuração

| Variável | Finalidade | Valor inicial |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | Credencial da API da Anthropic | sem valor |
| `ANTHROPIC_MODEL` | Modelo usado para geração | `claude-haiku-4-5` |
| `CHROMA_PATH` | Diretório do banco vetorial | `./chroma_db` |
| `CHROMA_COLLECTION` | Nome da coleção persistente | `bulfinch_mythology` |
| `EMBEDDING_MODEL` | Modelo local de embeddings | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| `PDF_PATH` | Caminho padrão do corpus | `./data/bulfinch-mythology.pdf` |
| `RETRIEVAL_TOP_K` | Número de chunks recuperados | `5` |
| `RETRIEVAL_MIN_SCORE` | Relevância mínima aceita | `0.45` |
| `MAX_RETRIEVAL_ATTEMPTS` | Limite total de buscas | `3` |

Nunca versione o arquivo `.env` ou chaves de API.

## Pipeline RAG

O workflow usa LangGraph para manter explícito e limitado o ciclo de recuperação:

```text
pergunta
   ↓
recuperação no Chroma
   ↓
avaliação por score
   ├── insuficiente → Claude reformula → nova recuperação (máximo 3)
   ├── insuficiente após a 3ª tentativa → resposta de insuficiência
   └── suficiente → resposta fundamentada → conceitos do grafo
```

As citações da resposta e dos conceitos são validadas contra o conteúdo real dos
chunks. Uma citação inventada ou vinculada ao chunk errado é rejeitada.

## Preparação do corpus

Adicione a edição em domínio público como:

```text
data/bulfinch-mythology.pdf
```

Se o arquivo tiver até 50 MB, ele pode ser versionado junto com a referência de
origem e licença. Para verificar apenas a extração e o chunking:

```bash
python -m src.ingest data/bulfinch-mythology.pdf --prepare-only
```

Para extrair, gerar os embeddings e fazer upsert no Chroma:

```bash
python -m src.ingest data/bulfinch-mythology.pdf
```

Os IDs são determinísticos. Executar a ingestão novamente atualiza os mesmos
chunks, em vez de duplicá-los.

## Testes

Execute a suíte sem consumir a API da Anthropic:

```bash
python -m unittest discover -v
python -m pip check
```

Os testes cobrem chunking, IDs estáveis, indexação, retrieval, avaliação, limite
de tentativas, citações, conceitos e falhas controladas. As integrações com Claude
são mockadas para evitar custo acidental.

## Desenvolvimento

O histórico segue Conventional Commits com mensagens em português. Mudanças
independentes devem ser registradas em commits pequenos e verificados.

Exemplos:

```text
feat: implementa ingestão do documento
fix: preserva metadados ao recuperar chunks
docs: adiciona instruções de deploy na OCI
test: cobre expansão dos nós do grafo
chore: atualiza dependências do projeto
```

## Próximas etapas

1. Adicionar e indexar o PDF real de *Bulfinch's Mythology*.
2. Calibrar o score mínimo com perguntas reais em português.
3. Conectar `/query` e `/expand` ao workflow.
4. Renderizar os nós e fontes no grafo interativo.
5. Preparar evidências e deploy na OCI.
