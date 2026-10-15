import os
import sys

# Ensure backend root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.session import SessionLocal, Base, engine
from app.models import User, UserRole, Ticket, TicketStatus, AppSetting
from app.core.security import hash_password
from app.services.classification.engine import ClassificationEngine
from app.api.v1.knowledge import auto_seed_sample_documents
from app.services.workflows.airline_orchestrator import AirlineWorkflowOrchestrator
import asyncio

async def seed_everything():
    print("Initializing AeroAssist AI Airline Platform Database...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Users (Admin, Support Agent, Passenger)
        users = [
            ("admin@aeroassistant.com", "AdminPass123!", "System Administrator", UserRole.ADMIN),
            ("engineer@aeroassistant.com", "EngineerPass123!", "Sarah Connor (Lead Support Agent)", UserRole.SUPPORT_AGENT),
            ("agent@aeroassistant.com", "AgentPass123!", "Alex Rivera (Support Agent)", UserRole.SUPPORT_AGENT),
            ("passenger@aeroassistant.com", "PassengerPass123!", "Marcus Vance (Frequent Flyer)", UserRole.PASSENGER),
            ("requester@aeroassistant.com", "RequesterPass123!", "Emily Watson (Passenger)", UserRole.PASSENGER)
        ]

        created_users = {}
        for email, pwd, name, role in users:
            u = db.query(User).filter(User.email == email).first()
            if not u:
                u = User(
                    email=email,
                    hashed_password=hash_password(pwd),
                    full_name=name,
                    role=role,
                    is_active=True
                )
                db.add(u)
                db.commit()
                db.refresh(u)
                print(f"Created user: {email} ({role.value})")
            created_users[email] = u

        # 2. Ingest Sample Runbooks into Knowledge Base
        print("Ingesting airline policies and runbooks into RAG vector index...")
        await auto_seed_sample_documents(db)

        # 3. Create Sample Airline Tickets & Classify
        passenger_user = created_users["passenger@aeroassistant.com"]
        engine_clf = ClassificationEngine(threshold=70.0)

        airline_sample_tickets = [
            {
                "title": "Checked baggage not arrived on carousel for flight FL-342 (JFK)",
                "description": "Passenger arrived on flight FL-342 at JFK airport Terminal 4. Checked suitcase was not delivered to carousel 3. Filed PIR report JFKAA12345. Need emergency toiletry allowance and delivery update.",
                "affected_service": "Baggage Services",
                "category": "Baggage",
                "business_impact": "Single passenger",
                "urgency": "High",
                "environment": "production",
                "affected_users": 1,
                "passenger_name": "Marcus Vance",
                "passenger_email": "passenger@aeroassistant.com",
                "booking_reference": "AA-78942",
                "flight_number": "FL-342",
                "travel_date": "2026-10-14",
                "error_logs": "PIR: JFKAA12345, Bag Tag: AA984120"
            },
            {
                "title": "Flight FL-802 cancelled in Chicago - immediate rebooking requested",
                "description": "Flight FL-802 from ORD to SFO was cancelled due to crew scheduling disruption. Passenger is stranded at airport and requires rebooking on the next flight or partner airline, plus meal voucher.",
                "affected_service": "Flight Operations",
                "category": "Flight Cancellation",
                "business_impact": "Department-wide",
                "urgency": "High",
                "environment": "production",
                "affected_users": 180,
                "passenger_name": "Sophia Martinez",
                "passenger_email": "sophia.martinez@example.com",
                "booking_reference": "FL-90218",
                "flight_number": "FL-802",
                "travel_date": "2026-10-15",
                "error_logs": "FLIGHT DISRUPTION: FL-802 CANCELLED (AIRCRAFT_AOG)"
            },
            {
                "title": "Wheelchair ramp assistance (WCHR) request for elderly traveler on FL-118",
                "description": "Requesting airport wheelchair ramp assistance (WCHR) for elderly mother traveling on flight FL-118 from LAX to JFK on November 2nd. She can walk inside the cabin but cannot navigate long terminal concourses.",
                "affected_service": "Special Services",
                "category": "Special Assistance",
                "business_impact": "Single passenger",
                "urgency": "Medium",
                "environment": "production",
                "affected_users": 1,
                "passenger_name": "David Chen",
                "passenger_email": "dchen@example.com",
                "booking_reference": "WCH-4412",
                "flight_number": "FL-118",
                "travel_date": "2026-11-02",
                "error_logs": "SSR: WCHR requested"
            },
            {
                "title": "24-Hour flexible booking cancellation and full refund inquiry",
                "description": "Purchased ticket 4 hours ago on booking reference REF-2219 for flight FL-610. Due to meeting rescheduling, I need to cancel the flight under the 24-hour flexible rule for a 100% card refund.",
                "affected_service": "Ticketing & Refunds",
                "category": "Cancellation and Refund",
                "business_impact": "Single passenger",
                "urgency": "Medium",
                "environment": "production",
                "affected_users": 1,
                "passenger_name": "Elena Rostova",
                "passenger_email": "elena.r@example.com",
                "booking_reference": "REF-2219",
                "flight_number": "FL-610",
                "travel_date": "2026-11-18",
                "error_logs": ""
            },
            {
                "title": "Emergency exit row seat selection rules and verification for flight FL-505",
                "description": "I would like to reserve seat 14A (emergency exit row) on upcoming flight FL-505 from BOS to MIA. Want to confirm minimum age and physical capability criteria.",
                "affected_service": "Cabin Seating",
                "category": "Seat Selection",
                "business_impact": "Single passenger",
                "urgency": "Low",
                "environment": "production",
                "affected_users": 1,
                "passenger_name": "James Wilson",
                "passenger_email": "jwilson@example.com",
                "booking_reference": "SEAT-8812",
                "flight_number": "FL-505",
                "travel_date": "2026-10-25",
                "error_logs": ""
            },
            {
                "title": "4-Hour tarmac delay on flight FL-410 - meal voucher and duty of care claim",
                "description": "Flight FL-410 was delayed on the tarmac and at the gate in Dallas for 4 hours and 15 minutes before departure. Requesting compensation meal vouchers and delay certificate for travel insurance.",
                "affected_service": "Customer Relations",
                "category": "Flight Delay",
                "business_impact": "Single passenger",
                "urgency": "Medium",
                "environment": "production",
                "affected_users": 140,
                "passenger_name": "Robert Taylor",
                "passenger_email": "rtaylor@example.com",
                "booking_reference": "DFW-6631",
                "flight_number": "FL-410",
                "travel_date": "2026-10-13",
                "error_logs": "DELAY LOG: FL-410 DEP DELAY 255 MIN"
            }
        ]

        airline_orchestrator = AirlineWorkflowOrchestrator(db)

        for t_data in airline_sample_tickets:
            existing = db.query(Ticket).filter(Ticket.title == t_data["title"]).first()
            if not existing:
                t = Ticket(
                    title=t_data["title"],
                    description=t_data["description"],
                    affected_service=t_data["affected_service"],
                    category=t_data["category"],
                    business_impact=t_data["business_impact"],
                    urgency=t_data["urgency"],
                    environment=t_data["environment"],
                    affected_users=t_data["affected_users"],
                    error_logs=t_data["error_logs"],
                    passenger_name=t_data["passenger_name"],
                    passenger_email=t_data["passenger_email"],
                    booking_reference=t_data["booking_reference"],
                    flight_number=t_data["flight_number"],
                    travel_date=t_data["travel_date"],
                    status=TicketStatus.SUBMITTED,
                    reporter_id=passenger_user.id
                )
                db.add(t)
                db.commit()
                db.refresh(t)

                t.ticket_number = f"TK-{t.id:04d}"
                db.commit()

                clf = await engine_clf.classify_ticket(
                    ticket_id=t.id,
                    title=t.title,
                    description=t.description,
                    affected_service=t.affected_service,
                    reported_category=t.category,
                    urgency=t.urgency,
                    business_impact=t.business_impact,
                    environment=t.environment,
                    affected_users=t.affected_users,
                    error_logs=t.error_logs or ""
                )

                from app.models.classification import TicketClassification
                tc = TicketClassification(
                    ticket_id=t.id,
                    predicted_category=clf.predicted_category,
                    priority=clf.priority,
                    criticality=clf.criticality,
                    confidence_score=clf.confidence_score,
                    explanation=clf.explanation,
                    detected_keywords=clf.detected_keywords,
                    potential_business_impact=clf.potential_business_impact,
                    recommended_next_action=clf.recommended_next_action,
                    missing_information=clf.missing_information,
                    requires_human_review=clf.requires_human_review,
                    review_reason=clf.review_reason,
                    model_name=clf.model_name,
                    confidence_breakdown=clf.confidence_breakdown
                )
                db.add(tc)
                t.status = TicketStatus(clf.status)
                t.ai_confidence = int(clf.confidence_score)
                db.commit()
                print(f"Created & Classified ticket #{t.id} ({t.ticket_number}) -> Category: {clf.predicted_category}, Status: {t.status.value} ({clf.confidence_score}%)")

        # 4. Seed AI Evaluations and Human Feedback for Analytics
        from app.models.evaluation import AIEvaluation, EvaluationFeedback
        from datetime import datetime, timezone, timedelta
        
        if db.query(AIEvaluation).count() < 10:
            print("Seeding baseline AI evaluations and human ground-truth feedback...")
            all_tickets = db.query(Ticket).all()
            sample_evals = [
                (0, "AeroAssist-Agentic-v1", 89.5, "PASS", "RESOLVED", None, 142, 4),
                (1, "AeroAssist-Agentic-v1", 62.0, "NEEDS_REVISION", "ESCALATED", "Connecting flight rebooking requires human supervisor approval", 210, 3),
                (2, "AeroAssist-Agentic-v1", 94.0, "PASS", "RESOLVED", None, 115, 5),
                (3, "AeroAssist-Agentic-v1", 87.5, "PASS", "RESOLVED", None, 130, 4),
                (4, "AeroAssist-Agentic-v1", 48.0, "FAIL", "ESCALATED", "Confidence below 70% threshold; missing passenger booking reference", 95, 1),
                (5, "AeroAssist-Agentic-v1", 73.0, "PASS", "RESOLVED", None, 160, 3),
                (0, "Deterministic-Policy-Engine", 78.0, "PASS", "RESOLVED", None, 45, 2),
                (1, "Deterministic-Policy-Engine", 55.0, "NEEDS_REVISION", "ESCALATED", "Policy ambiguity on delay compensation limits", 52, 2),
                (2, "AeroAssist-Agentic-v1", 91.0, "PASS", "RESOLVED", None, 125, 4),
                (3, "AeroAssist-Agentic-v1", 28.5, "FAIL", "ESCALATED", "Unsupported request for direct financial wire transfer", 88, 0),
                (4, "AeroAssist-Agentic-v1", 84.0, "PASS", "RESOLVED", None, 140, 3),
                (5, "Deterministic-Policy-Engine", 68.0, "NEEDS_REVISION", "ESCALATED", "Review required by policy", 40, 2),
            ]
            for idx, (t_idx, model, conf, val, outcome, reason, lat, src_cnt) in enumerate(sample_evals):
                t = all_tickets[t_idx % len(all_tickets)]
                eval_time = datetime.now(timezone.utc) - timedelta(days=(idx % 14), hours=(idx * 2))
                ev = AIEvaluation(
                    ticket_id=t.id,
                    model_name=model,
                    confidence_score=conf,
                    validation_outcome=val,
                    validation_details={"verdict": val, "checks_passed": val == "PASS"},
                    final_outcome=outcome,
                    escalation_reason=reason,
                    latency_ms=lat,
                    retrieved_sources_count=src_cnt,
                    status="SUCCESS",
                    created_at=eval_time
                )
                db.add(ev)
                db.commit()
                db.refresh(ev)

                if idx in [0, 2, 3, 5, 8]:
                    fb = EvaluationFeedback(
                        evaluation_id=ev.id,
                        ticket_id=t.id,
                        accuracy_label="CORRECT" if conf >= 70 else "PARTIALLY_CORRECT",
                        source_grounding_rating=5 if conf >= 85 else 4,
                        notes="Verified against official airline operating manual.",
                        created_at=eval_time
                    )
                    db.add(fb)
                    db.commit()
                elif idx in [1, 4]:
                    fb = EvaluationFeedback(
                        evaluation_id=ev.id,
                        ticket_id=t.id,
                        accuracy_label="PARTIALLY_CORRECT",
                        source_grounding_rating=3,
                        notes="Properly identified flight delay but required human agent signoff.",
                        created_at=eval_time
                    )
                    db.add(fb)
                    db.commit()

        print("Seeding complete! Airline database is fully populated.")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(seed_everything())
