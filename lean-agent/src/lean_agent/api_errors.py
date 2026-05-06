"""Domain → HTTP exception translation (registered on the FastAPI app)."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from lean_agent.commands.errors import (
    HypothesisNotFoundError,
    InterviewNotFoundError,
    LLMOutputInvalid,
    PersonaIdConflict,
    PersonaInUseByPreset,
    PersonaNotFound,
    PresetNameConflict,
    PresetNotFound,
    ProjectNotFoundError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProjectNotFoundError)
    async def _project_404(request: Request, exc: ProjectNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(HypothesisNotFoundError)
    async def _hypothesis_404(request: Request, exc: HypothesisNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(InterviewNotFoundError)
    async def _interview_404(request: Request, exc: InterviewNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(PersonaNotFound)
    async def _persona_not_found(request: Request, exc: PersonaNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(PersonaIdConflict)
    async def _persona_id_conflict(request: Request, exc: PersonaIdConflict) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(PersonaInUseByPreset)
    async def _persona_in_use(request: Request, exc: PersonaInUseByPreset) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc), "referenced_by": exc.referenced_by},
        )

    @app.exception_handler(PresetNotFound)
    async def _preset_not_found(request: Request, exc: PresetNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(PresetNameConflict)
    async def _preset_name_conflict(request: Request, exc: PresetNameConflict) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(LLMOutputInvalid)
    async def _llm_output_invalid(request: Request, exc: LLMOutputInvalid) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc), "errors": exc.errors})
