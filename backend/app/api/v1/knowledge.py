import os
import shutil
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel, ConfigDict

from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.ticket import Ticket
from app.models.knowledge import KnowledgeDocument, DocumentChunk
from app.api.deps import get_current_user, get_support_or_admin
from app.services.rag.extractor import extract_text_from_file
from app.services.rag.chunker import chunk_text
from app.services.rag.embeddings import EmbeddingService
from app.services.rag.retriever import KnowledgeRetriever
from app.services.rag.grounding import GroundedSolutionService, GroundedSolutionResult
from app.services.audit.audit_service import record_audit_event
from app.core.config import settings
from app.core.logging import logger

router = APIRouter(tags=["Knowledge Base (RAG)"])

class SearchQueryRequest(BaseModel):
    query: str
    service: Optional[str] = None
    category: Optional[str] = None
    top_k: int = 5

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    doc_type: str
    service: str
    category: str
    version: str
    owner: str
    file_name: Optional[str] = None
    file_size_bytes: int
    status: str
    error_message: Optional[str] = None
    chunk_count: int
    created_at: datetime

class DocumentDetailResponse(DocumentResponse):
    chunks: List[dict] = []

@router.get("/knowledge/documents", response_model=List[DocumentResponse])
def list_documents(
    category: Optional[str] = None,
    service: Optional[str] = None,
    doc_type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(KnowledgeDocument)
    if category:
        query = query.filter(KnowledgeDocument.category == category)
    if service:
        query = query.filter(KnowledgeDocument.service == service)
    if doc_type:
        query = query.filter(KnowledgeDocument.doc_type == doc_type)
    if search:
        query = query.filter(KnowledgeDocument.title.ilike(f"%{search}%"))

    return query.order_by(desc(KnowledgeDocument.created_at)).all()

@router.post("/knowledge/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    title: str = Form(...),
    doc_type: str = Form(...),
    service: str = Form(...),
    category: str = Form(...),
    version: str = Form("1.0"),
    owner: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_support_or_admin)
):
    # Enforce file extensions and size
    ext = os.path.splitext(file.filename)[1].lower()
    allowed_exts = [".pdf", ".md", ".txt", ".json", ".log", ".docx"]
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' not supported. Allowed: {allowed_exts}"
        )

    docs_dir = os.path.join(settings.UPLOAD_DIR, "knowledge")
    os.makedirs(docs_dir, exist_ok=True)
    safe_filename = f"{int(datetime.now(timezone.utc).timestamp())}_{file.filename}"
    file_path = os.path.join(docs_dir, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)
    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum permitted size of {settings.MAX_UPLOAD_SIZE_BYTES / (1024*1024)}MB"
        )

    doc = KnowledgeDocument(
        title=title,
        doc_type=doc_type,
        service=service,
        category=category,
        version=version,
        owner=owner,
        file_path=file_path,
        file_name=file.filename,
        file_size_bytes=file_size,
        status="INDEXING",
        chunk_count=0
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        # Extract text and chunk
        text, _ = extract_text_from_file(file_path)
        chunks = chunk_text(
            text=text,
            chunk_size=500,
            chunk_overlap=100,
            doc_metadata={
                "document_id": doc.id,
                "title": doc.title,
                "service": doc.service,
                "category": doc.category
            }
        )

        embedding_service = EmbeddingService()
        for ch in chunks:
            vector = await embedding_service.get_embedding(ch.content)
            chunk_record = DocumentChunk(
                document_id=doc.id,
                chunk_index=ch.chunk_index,
                content=ch.content,
                metadata_json=ch.metadata,
                embedding_vector=vector
            )
            db.add(chunk_record)

        doc.chunk_count = len(chunks)
        doc.status = "INDEXED"
        db.commit()
        db.refresh(doc)

        record_audit_event(
            db=db,
            entity_type="KNOWLEDGE",
            entity_id=str(doc.id),
            action="DOCUMENT_INGESTED",
            actor_id=current_user.id,
            details={"title": doc.title, "chunk_count": doc.chunk_count}
        )
    except Exception as e:
        logger.error(f"Failed to index document #{doc.id}: {str(e)}")
        doc.status = "FAILED"
        doc.error_message = str(e)
        db.commit()
        db.refresh(doc)

    return doc

@router.get("/knowledge/documents/{document_id}")
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document #{document_id} not found")

    chunks_data = [
        {
            "id": ch.id,
            "chunk_index": ch.chunk_index,
            "content": ch.content,
            "metadata": ch.metadata_json
        }
        for ch in doc.chunks
    ]
    return {
        "id": doc.id,
        "title": doc.title,
        "doc_type": doc.doc_type,
        "service": doc.service,
        "category": doc.category,
        "version": doc.version,
        "owner": doc.owner,
        "file_name": doc.file_name,
        "file_size_bytes": doc.file_size_bytes,
        "status": doc.status,
        "error_message": doc.error_message,
        "chunk_count": doc.chunk_count,
        "created_at": doc.created_at,
        "chunks": chunks_data
    }

@router.delete("/knowledge/documents/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_support_or_admin)
):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document #{document_id} not found")

    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    db.delete(doc)
    db.commit()

    record_audit_event(
        db=db,
        entity_type="KNOWLEDGE",
        entity_id=str(document_id),
        action="DOCUMENT_DELETED",
        actor_id=current_user.id,
        details={"title": doc.title}
    )
    return {"success": True, "message": f"Document #{document_id} removed"}

@router.post("/knowledge/documents/{document_id}/reindex")
async def reindex_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_support_or_admin)
):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document #{document_id} not found")

    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source file missing on server disk")

    # Clear old chunks
    db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
    doc.status = "INDEXING"
    db.commit()

    text, _ = extract_text_from_file(doc.file_path)
    chunks = chunk_text(
        text=text,
        chunk_size=500,
        chunk_overlap=100,
        doc_metadata={"document_id": doc.id, "title": doc.title, "service": doc.service, "category": doc.category}
    )

    embedding_service = EmbeddingService()
    for ch in chunks:
        vector = await embedding_service.get_embedding(ch.content)
        chunk_record = DocumentChunk(
            document_id=doc.id,
            chunk_index=ch.chunk_index,
            content=ch.content,
            metadata_json=ch.metadata,
            embedding_vector=vector
        )
        db.add(chunk_record)

    doc.chunk_count = len(chunks)
    doc.status = "INDEXED"
    doc.error_message = None
    db.commit()
    db.refresh(doc)

    return {"success": True, "chunk_count": doc.chunk_count, "status": doc.status}

@router.post("/knowledge/search")
async def search_knowledge(
    search_req: SearchQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    retriever = KnowledgeRetriever(db)
    results = await retriever.search_query(
        query=search_req.query,
        service=search_req.service,
        category=search_req.category,
        top_k=search_req.top_k
    )
    sources = [
        {
            "chunk_id": r.chunk_id,
            "document_id": r.document_id,
            "document_title": r.document_title,
            "service": r.service,
            "category": r.category,
            "chunk_index": r.chunk_index,
            "similarity_score": round(r.combined_score * 100, 1),
            "content": r.content
        }
        for r in results
    ]
    return {"sources": sources, "count": len(sources)}

@router.post("/tickets/{ticket_id}/solution", response_model=GroundedSolutionResult)
async def generate_ticket_solution(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ticket #{ticket_id} not found")

    retriever = KnowledgeRetriever(db)
    retrieved = await retriever.retrieve_for_ticket(
        title=ticket.title,
        description=ticket.description,
        affected_service=ticket.affected_service,
        category=ticket.category,
        error_logs=ticket.error_logs,
        top_k=4
    )

    grounding_service = GroundedSolutionService()
    priority = ticket.classification.priority if ticket.classification else "P3 Medium"
    solution = grounding_service.generate_grounded_solution(
        ticket_id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        affected_service=ticket.affected_service,
        category=ticket.category,
        priority=priority,
        retrieved_chunks=retrieved
    )

    record_audit_event(
        db=db,
        entity_type="TICKET_SOLUTION",
        entity_id=str(ticket.id),
        action="RAG_SOLUTION_GENERATED",
        actor_id=current_user.id,
        details={
            "evidence_quality": solution.evidence_quality,
            "confidence": solution.solution_confidence,
            "citations_count": len(solution.supporting_citations)
        }
    )

    return solution

@router.get("/tickets/{ticket_id}/solution", response_model=GroundedSolutionResult)
async def get_ticket_solution(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await generate_ticket_solution(ticket_id=ticket_id, db=db, current_user=current_user)

async def auto_seed_sample_documents(db: Session):
    """
    Ingests sample runbooks on startup so RAG is demonstrable out of the box.
    """
    sample_dir = os.path.join("..", "knowledge_documents", "sample")
    if not os.path.exists(sample_dir):
        sample_dir = os.path.join("knowledge_documents", "sample")
    if not os.path.exists(sample_dir):
        return

    sample_meta = {
        "airline_booking_and_reservation_policy.md": {
            "title": "AeroAssist Airline Policy: Booking & Reservation Management",
            "doc_type": "Policy",
            "service": "Passenger Ticketing & PNR Servicing",
            "category": "Booking and Reservation",
            "owner": "Commercial Ticketing Standards"
        },
        "airline_cancellation_and_refund_procedure.md": {
            "title": "AeroAssist Airline Policy: Cancellation & Refund Procedures",
            "doc_type": "Procedure",
            "service": "Passenger Revenue Accounting & Claims",
            "category": "Cancellation and Refund",
            "owner": "Revenue Protection & Passenger Rights"
        },
        "airline_baggage_allowance_and_claims.md": {
            "title": "AeroAssist Airline Policy: Baggage Allowances, Lost & Delayed Claims",
            "doc_type": "Guideline",
            "service": "Airport Baggage Services & WorldTracer",
            "category": "Baggage",
            "owner": "Central Baggage Resolution Unit"
        },
        "airline_checkin_and_boarding_requirements.md": {
            "title": "AeroAssist Airline Policy: Check-in & Boarding Requirements",
            "doc_type": "Requirements",
            "service": "Airport Terminal Operations & Gate Control",
            "category": "Check-in and Boarding",
            "owner": "Airport Customer Experience"
        },
        "airline_flight_delay_and_disruption_assistance.md": {
            "title": "AeroAssist Airline Policy: Flight Delays & Disruption Assistance",
            "doc_type": "Assistance Guide",
            "service": "Integrated Operations Control Center (IOCC)",
            "category": "Flight Delay",
            "owner": "Passenger Disruption Care Unit"
        },
        "airline_seat_selection_and_upgrades.md": {
            "title": "AeroAssist Airline Policy: Seat Selection & Cabin Upgrades",
            "doc_type": "Guideline",
            "service": "Ancillary Services & Cabin Experience",
            "category": "Seat Selection",
            "owner": "Commercial Product Management"
        },
        "airline_special_assistance_procedure.md": {
            "title": "AeroAssist Airline Policy: Special Assistance & Accessibility Services",
            "doc_type": "Procedure",
            "service": "Accessibility Services & Special Handling",
            "category": "Special Assistance",
            "owner": "Passenger Accessibility Directorate"
        },
        "airline_passenger_support_escalation_guide.md": {
            "title": "AeroAssist Airline Policy: Passenger Support Escalation & Governance Guide",
            "doc_type": "Governance Guide",
            "service": "Customer Relations & Duty Station Management",
            "category": "Other",
            "owner": "Global Customer Service Operations"
        },
        "k8s_oomkilled_remediation.md": {
            "title": "Kubernetes Pod OOMKilled and CrashLoopBackOff Runbook",
            "doc_type": "Runbook",
            "service": "Kubernetes / Container Platform",
            "category": "Infrastructure",
            "owner": "Cloud SRE Team"
        },
        "postgres_deadlock_resolution.md": {
            "title": "PostgreSQL Connection Pool & Deadlock Resolution Procedure",
            "doc_type": "Procedure",
            "service": "PostgreSQL Core & RDS",
            "category": "Database",
            "owner": "DBRE Team"
        },
        "vpn_gateway_packet_loss.md": {
            "title": "Enterprise VPN Gateway Drops & Latency Troubleshooting Guide",
            "doc_type": "Guide",
            "service": "Corporate VPN Gateway",
            "category": "Network",
            "owner": "Network Engineering"
        },
        "auth_sso_saml_troubleshooting.md": {
            "title": "SSO & SAML 2.0 Authentication Token Failure Runbook",
            "doc_type": "Runbook",
            "service": "Okta SSO & SAML Identity Provider",
            "category": "Authentication and access",
            "owner": "IAM Operations"
        },
        "sec_sql_injection_containment.md": {
            "title": "Incident Postmortem & Runbook: WAF SQL Injection Attack Mitigation",
            "doc_type": "Postmortem",
            "service": "Web Application Firewall & API Gateway",
            "category": "Security",
            "owner": "SecOps Team"
        }
    }

    embedding_service = EmbeddingService()
    for filename, meta in sample_meta.items():
        file_path = os.path.join(sample_dir, filename)
        if not os.path.exists(file_path):
            continue
        existing = db.query(KnowledgeDocument).filter(KnowledgeDocument.title == meta["title"]).first()
        if not existing:
            text, _ = extract_text_from_file(file_path)
            doc = KnowledgeDocument(
                title=meta["title"],
                doc_type=meta["doc_type"],
                service=meta["service"],
                category=meta["category"],
                version="1.0",
                owner=meta["owner"],
                file_path=file_path,
                file_name=filename,
                file_size_bytes=os.path.getsize(file_path),
                status="INDEXED",
                chunk_count=0
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)

            chunks = chunk_text(
                text=text,
                chunk_size=500,
                chunk_overlap=100,
                doc_metadata={"document_id": doc.id, "title": doc.title, "service": doc.service, "category": doc.category}
            )
            for ch in chunks:
                vector = await embedding_service.get_embedding(ch.content)
                chunk_record = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=ch.chunk_index,
                    content=ch.content,
                    metadata_json=ch.metadata,
                    embedding_vector=vector
                )
                db.add(chunk_record)

            doc.chunk_count = len(chunks)
            db.commit()
            logger.info(f"Sample knowledge doc indexed: '{doc.title}' ({doc.chunk_count} chunks)")
