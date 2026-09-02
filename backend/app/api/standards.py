from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_standard_service
from app.api.schemas import RelationshipResponse, StandardCreate, StandardListResponse, StandardResponse, StandardSummary, StandardUpdate, VersionResponse
from app.application.standards import StandardService


router = APIRouter(prefix="/standards", tags=["standards"])
SessionDependency = Annotated[AsyncSession, Depends(get_session)]
ServiceDependency = Annotated[StandardService, Depends(get_standard_service)]


@router.post("", response_model=StandardResponse, status_code=status.HTTP_201_CREATED, summary="Create a standard record")
async def create_standard(payload: StandardCreate, service: ServiceDependency) -> StandardResponse:
    standard = await service.create(**payload.model_dump())
    await service.session.commit()
    return standard


@router.get("", response_model=StandardListResponse, summary="List standard records")
async def list_standards(service: ServiceDependency, offset: int = Query(default=0, ge=0), limit: int = Query(default=20, ge=1, le=100), status_filter: str | None = Query(default=None, alias="status"), search: str | None = Query(default=None, min_length=1)) -> StandardListResponse:
    standards, total = await service.list(offset=offset, limit=limit, status=status_filter, search=search)
    return StandardListResponse(items=[StandardSummary.model_validate(item) for item in standards], total=total, offset=offset, limit=limit)


@router.get("/{standard_id}", response_model=StandardResponse, summary="Get a standard")
async def get_standard(standard_id: str, service: ServiceDependency) -> StandardResponse:
    return await service.get(standard_id)


@router.patch("/{standard_id}", response_model=StandardResponse, summary="Update a standard")
async def update_standard(standard_id: str, payload: StandardUpdate, service: ServiceDependency) -> StandardResponse:
    standard = await service.update(standard_id, payload.model_dump(exclude_unset=True))
    await service.session.commit()
    return standard


@router.delete("/{standard_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a standard")
async def delete_standard(standard_id: str, service: ServiceDependency) -> Response:
    await service.delete(standard_id)
    await service.session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{standard_id}/versions", response_model=list[VersionResponse], summary="List standard versions")
async def list_versions(standard_id: str, service: ServiceDependency) -> list[VersionResponse]:
    return await service.versions(standard_id)


@router.get("/{standard_id}/relationships", response_model=list[RelationshipResponse], summary="List standard relationships")
async def list_relationships(standard_id: str, service: ServiceDependency) -> list[RelationshipResponse]:
    return await service.relationships(standard_id)