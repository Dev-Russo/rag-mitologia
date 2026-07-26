from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from src.workflow import RAGWorkflow, WorkflowResponse, create_rag_workflow

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Mapa Mitológico RAG",
    description="Mapa mental vivo de mitologia com fontes rastreáveis.",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class ExpandRequest(BaseModel):
    node_id: str = Field(min_length=3, max_length=100)
    concept: str = Field(min_length=2, max_length=100)


@lru_cache
def _cached_workflow() -> RAGWorkflow:
    return create_rag_workflow()


def get_workflow() -> RAGWorkflow:
    """Recria o workflow se a coleção tiver sido substituída por um rebuild."""
    workflow = _cached_workflow()
    try:
        workflow.vector_store.get(limit=1, include=[])
    except Exception:
        _cached_workflow.cache_clear()
        workflow = _cached_workflow()
    return workflow


def _api_response(result: WorkflowResponse) -> WorkflowResponse | JSONResponse:
    if result.status != "error":
        return result
    return JSONResponse(
        status_code=503,
        content=result.model_dump(mode="json"),
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": app.title},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/query", response_model=WorkflowResponse)
async def query(
    payload: QueryRequest,
    workflow: RAGWorkflow = Depends(get_workflow),
) -> WorkflowResponse | JSONResponse:
    result = await run_in_threadpool(workflow.run, payload.question)
    return _api_response(result)


@app.post("/expand", response_model=WorkflowResponse)
async def expand(
    payload: ExpandRequest,
    workflow: RAGWorkflow = Depends(get_workflow),
) -> WorkflowResponse | JSONResponse:
    implicit_question = (
        f"O que é relevante sobre {payload.concept} segundo o documento?"
    )
    result = await run_in_threadpool(workflow.run, implicit_question)
    if result.status == "ok":
        root_ids = {node.id for node in result.nodes if node.type == "pergunta"}
        result.nodes = [node for node in result.nodes if node.id not in root_ids]
        for edge in result.edges:
            if edge.source in root_ids:
                edge.source = payload.node_id
    return _api_response(result)
