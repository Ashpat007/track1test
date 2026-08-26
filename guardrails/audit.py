"""
Durable Audit Logger for Agentic Commerce.
Captures every decision, reasoning step, guardrail check, user gating prompt, and payment execution into PostgreSQL/SQLite.
"""

import os
import datetime
import json
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, Boolean, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agentic_commerce.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AuditLogRecord(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(64), index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    step_type = Column(String(32), index=True)  # CATALOG_SEARCH, LLM_REASONING, GUARDRAIL_EVALUATION, USER_GATING, PAYMENT_EXECUTION, FAILURE_HANDLED
    agent_goal = Column(Text, nullable=True)
    proposed_action = Column(Text, nullable=True)
    llm_reasoning = Column(Text, nullable=True)
    reasoning_source = Column(String(32), default="GEMINI_2.5_FLASH")  # GEMINI_2.5_FLASH vs RULE_FALLBACK
    spending_cap_inr = Column(Float, nullable=True)
    proposed_amount_inr = Column(Float, nullable=True)
    guardrail_passed = Column(Boolean, default=False)
    guardrail_message = Column(Text, nullable=True)
    gate_status = Column(String(32), default="PENDING")
    razorpay_order_id = Column(String(64), nullable=True)
    razorpay_payment_id = Column(String(64), nullable=True)
    outcome_status = Column(String(32), default="IN_PROGRESS")
    details_json = Column(Text, nullable=True)


Base.metadata.create_all(bind=engine)


class AuditLogger:
    def __init__(self, session_id: str):
        self.session_id = session_id

    def log_step(
        self,
        step_type: str,
        agent_goal: Optional[str] = None,
        proposed_action: Optional[str] = None,
        llm_reasoning: Optional[str] = None,
        reasoning_source: str = "GEMINI_2.5_FLASH",
        spending_cap_inr: Optional[float] = None,
        proposed_amount_inr: Optional[float] = None,
        guardrail_passed: bool = False,
        guardrail_message: Optional[str] = None,
        gate_status: str = "N/A",
        razorpay_order_id: Optional[str] = None,
        razorpay_payment_id: Optional[str] = None,
        outcome_status: str = "IN_PROGRESS",
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLogRecord:
        db = SessionLocal()
        try:
            record = AuditLogRecord(
                session_id=self.session_id,
                timestamp=datetime.datetime.utcnow(),
                step_type=step_type,
                agent_goal=agent_goal,
                proposed_action=proposed_action,
                llm_reasoning=llm_reasoning,
                reasoning_source=reasoning_source,
                spending_cap_inr=spending_cap_inr,
                proposed_amount_inr=proposed_amount_inr,
                guardrail_passed=guardrail_passed,
                guardrail_message=guardrail_message,
                gate_status=gate_status,
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                outcome_status=outcome_status,
                details_json=json.dumps(details) if details else None
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return record
        finally:
            db.close()

    def get_session_history(self) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            records = db.query(AuditLogRecord).filter(AuditLogRecord.session_id == self.session_id).order_by(AuditLogRecord.id.asc()).all()
            history = []
            for r in records:
                history.append({
                    "id": r.id,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "step_type": r.step_type,
                    "proposed_action": r.proposed_action,
                    "llm_reasoning": r.llm_reasoning,
                    "reasoning_source": getattr(r, "reasoning_source", "GEMINI_2.5_FLASH"),
                    "proposed_amount_inr": r.proposed_amount_inr,
                    "guardrail_passed": r.guardrail_passed,
                    "guardrail_message": r.guardrail_message,
                    "gate_status": r.gate_status,
                    "razorpay_order_id": r.razorpay_order_id,
                    "outcome_status": r.outcome_status,
                    "details": json.loads(r.details_json) if r.details_json else None
                })
            return history
        finally:
            db.close()
