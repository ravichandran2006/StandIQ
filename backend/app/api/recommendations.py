from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

from app.api.dependencies import get_recommendation_service
from app.api.schemas import (
    DetailContextRequest,
    ExplanationRequest,
    RecommendationRequest,
    RecommendationResponse,
    RefineRequest,
    TenderRequest,
)
from app.application.documents import DocumentInput, DocumentMetadata, DocumentProcessingError, DocumentType
from app.application.input import PDFOCRProcessor
from app.application.recommendations import RecommendationService


router = APIRouter(prefix="/recommendations", tags=["recommendations"])
ServiceDependency = Annotated[RecommendationService, Depends(get_recommendation_service)]
pdf_processor = PDFOCRProcessor()


@router.post("", response_model=RecommendationResponse)
async def create_recommendation(payload: RecommendationRequest, service: ServiceDependency) -> RecommendationResponse:
    result = await service.recommend(payload.text, payload.language)
    return RecommendationResponse.model_validate(result.__dict__)


@router.post("/upload", response_model=RecommendationResponse)
async def upload_document(
    file: UploadFile = File(...),
    language: str | None = Form(default=None),
    service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendationResponse:
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided for upload.")

    filename = file.filename
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="No readable text found in the uploaded document.")

    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds the 20 MB limit.")

    is_pdf = filename.lower().endswith(".pdf") or (file.content_type and "pdf" in file.content_type) or content.startswith(b"%PDF")
    if not is_pdf:
        raise HTTPException(status_code=400, detail="Unsupported document format. Only PDF files are supported.")

    doc_id = str(uuid4())
    doc_metadata = DocumentMetadata(
        document_id=doc_id,
        filename=filename,
        media_type="application/pdf",
        document_type=DocumentType.PDF,
        size_bytes=len(content),
        source="upload",
    )
    doc_input = DocumentInput(metadata=doc_metadata, content=content)

    try:
        ocr_result = await pdf_processor.process(doc_input)
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Unable to extract text from the uploaded PDF.") from exc

    extracted_text = ocr_result.metadata.get("full_text", "").strip()
    if not extracted_text:
        raise HTTPException(status_code=400, detail="No readable text found in the uploaded document.")

    doc_info = {
        "filename": filename,
        "media_type": "application/pdf",
        "page_count": ocr_result.metadata.get("total_pages", len(ocr_result.pages)),
        "extracted_text_length": len(extracted_text),
        "size_bytes": len(content),
    }

    result = await service.recommend(extracted_text, language=language, document=doc_info)
    return RecommendationResponse.model_validate(result.__dict__)


@router.post("/refine", response_model=RecommendationResponse)
async def refine_recommendation(payload: RefineRequest, service: ServiceDependency) -> RecommendationResponse:
    try:
        result = await service.refine(payload.original_text, payload.refinement, payload.language)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RecommendationResponse.model_validate(result.__dict__)


@router.post("/explanation")
async def create_explanation(payload: ExplanationRequest, service: ServiceDependency) -> dict:
    recommendation = await service.recommend(payload.text, payload.language)
    standard = next((item for item in recommendation.standards if item["standard_id"] == payload.standard_id), None)
    if standard is None:
        standard = next((item for item in recommendation.standards if item["standard_id"]), None)
    if standard is None:
        return {"status": "no_data", "message": "No recommended standard is available for explanation.", "explanation": None, "source": None}
    context = {
        "original_text": recommendation.requirement.get("original_text"),
        "normalized_text": recommendation.requirement.get("normalized_text"),
        "detected_language": recommendation.requirement.get("detected_language"),
        "detected_language_label": recommendation.requirement.get("detected_language_label"),
        "technical_keywords": recommendation.requirement.get("technical_keywords", []),
        "standard": standard,
    }
    return await service.details.explanation(context)


@router.post("/tender")
async def create_tender_specification(payload: TenderRequest, service: ServiceDependency) -> dict:
    recommendation = await service.recommend(payload.text, payload.language)
    return await service.details.tender(recommendation.requirement, recommendation.standards)


@router.get("/standards/{standard_id}/related")
async def get_related_standards(standard_id: str, service: ServiceDependency) -> dict:
    return await service.details.related_standards(standard_id)


@router.get("/standards/{standard_id}/version-history")
async def get_version_history(standard_id: str, service: ServiceDependency) -> dict:
    return await service.details.version_history(standard_id)


@router.get("/standards/{standard_id}/compliance")
async def get_compliance_details(standard_id: str, service: ServiceDependency) -> dict:
    return await service.details.compliance_details(standard_id)


@router.post("/standards/{standard_id}/mapping")
async def get_requirement_mapping(standard_id: str, payload: DetailContextRequest, service: ServiceDependency) -> dict:
    recommendation = await service.recommend(payload.text) if payload.text.strip() else None
    if recommendation and recommendation.standards:
        standard = next((item for item in recommendation.standards if item["standard_id"] == standard_id), recommendation.standards[0])
        return {
            "status": "success",
            "message": None,
            "items": standard.get("mapping") or [],
        }
    return await service.details.requirement_mapping(standard_id, payload.text, [], [])


@router.get("/standards/{standard_id}/sources")
async def get_source_documents(standard_id: str, service: ServiceDependency) -> dict:
    return await service.details.source_documents(standard_id)


@router.post("/standards/{standard_id}/evidence")
async def get_all_evidence(
    standard_id: str,
    payload: DetailContextRequest,
    service: ServiceDependency,
    text: str | None = Query(default=None),
) -> dict:
    requirement_text = payload.text or text or ""
    recommendation = await service.recommend(requirement_text) if requirement_text.strip() else None
    reasons: list[str] = []
    terms: list[str] = []
    if recommendation:
        terms = recommendation.requirement.get("technical_keywords", [])
        standard = next((item for item in recommendation.standards if item["standard_id"] == standard_id), None)
        if standard:
            reasons = standard.get("reasons", [])
    return await service.details.all_evidence(standard_id, requirement_text, terms, reasons)
