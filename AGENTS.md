# Repository Guidelines

## Project Structure & Module Organization

This is a Python/FastAPI RAG application for an interactive Greek mythology map. The main API and web routes live in `app.py`. Core modules are in `src/`: `ingest.py` prepares the PDF corpus, `vector_store.py` manages Chroma/FastEmbed persistence, `retrieval.py` handles search, `generation.py` calls Anthropic, `grounding.py` validates citations, `graph_extraction.py` builds graph concepts, and `workflow.py` orchestrates LangGraph. Frontend assets are split between `templates/index.html` and `static/`. Tests live in `tests/`, and source documents live in `data/`. Generated runtime state such as `chroma_db/`, `.venv/`, and `.env` should stay unversioned.

## Build, Test, and Development Commands

Create and activate a local environment, then install dependencies:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Prepare the vector database after configuring `.env` from `.env.example`:

```powershell
python -m src.ingest data/ageoffableorstor00bulf_0.pdf --rebuild
```

Run locally with:

```powershell
uvicorn app:app --reload
```

Run the test suite with:

```powershell
python -m unittest
```

## Coding Style & Naming Conventions

Use standard Python style with 4-space indentation, type hints where useful, and small modules with clear responsibilities. Prefer `snake_case` for functions, variables, and modules; use `PascalCase` for Pydantic models, dataclasses, and test classes. Keep configuration in `src/config.py` and read secrets from environment variables. Frontend behavior belongs in `static/graph.js`; presentation belongs in `static/style.css`.

## Testing Guidelines

Tests use `unittest` plus FastAPI `TestClient`, with mocks for external services and workflow dependencies. Add tests under `tests/` using the `test_*.py` naming pattern. Keep unit tests deterministic: mock Anthropic calls, vector store access, and expensive ingestion work. For route changes, assert status codes and JSON contracts; for workflow changes, cover successful and insufficient-context paths.

## Commit & Pull Request Guidelines

Recent history uses Conventional Commits such as `feat:`, `fix:`, `test:`, `style:`, and `docs:`. Keep commits focused and written in the imperative mood, for example `fix: valida citações sem duplicar nós`. Pull requests should include a short description, tests run, linked issue or challenge requirement when applicable, and screenshots or notes for UI changes. Mention any required `.env` keys or ingestion steps when behavior depends on local configuration.

## Security & Configuration Tips

Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY` locally. Never commit `.env`, generated Chroma data, virtual environments, or downloaded model artifacts. When changing retrieval or grounding thresholds, document the rationale in the PR because those values affect answer quality and hallucination risk.
