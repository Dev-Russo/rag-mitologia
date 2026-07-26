# Mapa Mitológico RAG

Mapa mental vivo de mitologia grega que transforma respostas fundamentadas em um
grafo interativo. Cada conceito exibido no mapa será vinculado ao trecho exato do
documento usado pelo pipeline RAG.

O projeto está sendo desenvolvido para o **Challenge Alura/Oracle Next Education —
Track Tech AI Builder**.

> **Estado atual:** esqueleto da aplicação concluído. A ingestão do corpus, a busca
> vetorial e a integração com o LLM serão implementadas nas próximas etapas.

## Tecnologias definidas

- Python 3.11
- FastAPI e Uvicorn
- ChromaDB
- Sentence Transformers com `intfloat/multilingual-e5-small`
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
│   └── retrieval.py
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

- Python 3.11
- Git

Confirme que o interpretador ativo é o correto:

```bash
python --version
```

### Instalação

Crie e ative um ambiente virtual.

No Linux ou macOS:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

No Windows PowerShell:

```powershell
py -3.11 -m venv .venv
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

Nesta primeira etapa, a aplicação inicia mesmo sem uma chave da Anthropic. A
variável `ANTHROPIC_API_KEY` será necessária quando a geração for implementada.

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
| `EMBEDDING_MODEL` | Modelo local de embeddings | `intfloat/multilingual-e5-small` |

Nunca versione o arquivo `.env` ou chaves de API.

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

1. Implementar extração, chunking e indexação do documento.
2. Adicionar recuperação semântica e geração fundamentada.
3. Extrair conceitos e relacionamentos em JSON estruturado.
4. Conectar as rotas de consulta e expansão ao grafo interativo.
5. Preparar testes, documentação completa e deploy na OCI.
