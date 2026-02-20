"""
Phase 3 API endpoints:
  #7 – Notifications  (GET / PATCH mark-read / mark-all-read / DELETE)
  #8 – Leaderboard   (GET per paper)
  #9 – PDF Report    (GET per submission – student or teacher)
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from io import BytesIO
from datetime import datetime

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.notification import Notification
from app.models.submission import AnswerSubmission
from app.models.evaluation import Evaluation
from app.models.question_paper import QuestionPaper
from app.models.question import Question
from app.crud import question_paper as crud_paper

router = APIRouter(prefix="/v2", tags=["phase3"])


def _me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


# ═══════════════════════════════════════════════════════════════
# FEATURE #7 – Notifications
# ═══════════════════════════════════════════════════════════════

@router.get("/notifications")
def get_my_notifications(
    limit: int = 30,
    db: Session = Depends(get_db),
    me: User = Depends(_me),
):
    rows = (
        db.query(Notification)
        .filter(Notification.user_id == me.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )
    unread = db.query(func.count(Notification.id)).filter(
        Notification.user_id == me.id, Notification.is_read == False
    ).scalar()

    return {
        "unread_count": unread,
        "notifications": [
            {
                "id": str(n.id),
                "type": n.type,
                "title": n.title,
                "body": n.body,
                "link": n.link,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in rows
        ],
    }


@router.patch("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    me: User = Depends(_me),
):
    n = db.query(Notification).filter(
        Notification.id == notification_id, Notification.user_id == me.id
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Not found")
    n.is_read = True
    db.commit()
    return {"ok": True}


@router.patch("/notifications/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    me: User = Depends(_me),
):
    db.query(Notification).filter(
        Notification.user_id == me.id, Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"ok": True}


@router.delete("/notifications/clear")
def clear_all_notifications(
    db: Session = Depends(get_db),
    me: User = Depends(_me),
):
    db.query(Notification).filter(Notification.user_id == me.id).delete()
    db.commit()
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════
# FEATURE #8 – Leaderboard
# ═══════════════════════════════════════════════════════════════

@router.get("/papers/{paper_id}/leaderboard")
def get_leaderboard(
    paper_id: str,
    db: Session = Depends(get_db),
    me: User = Depends(_me),
):
    """
    Returns ranked list of students for a paper.
    Teachers see names; students see anonymised (only their own name shown).
    """
    paper = crud_paper.get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Aggregate marks per submission
    subquery = (
        db.query(
            AnswerSubmission.id.label("sub_id"),
            AnswerSubmission.student_id.label("student_id"),
            func.sum(Evaluation.marks_obtained).label("total"),
            func.sum(Evaluation.max_marks).label("max_m"),
        )
        .join(Evaluation, Evaluation.submission_id == AnswerSubmission.id)
        .filter(
            AnswerSubmission.paper_id == paper.id,
            AnswerSubmission.status == "evaluated",
        )
        .group_by(AnswerSubmission.id, AnswerSubmission.student_id)
        .all()
    )

    if not subquery:
        return {
            "paper_title": paper.title, 
            "total_marks": paper.total_marks, 
            "total_participants": 0,
            "entries": []
        }

    # Sort by total marks desc
    ranked = sorted(subquery, key=lambda r: (r.total or 0), reverse=True)
    max_m = float(ranked[0].max_m or paper.total_marks or 1)
    if max_m == 0: max_m = 1.0 # Safety

    is_teacher = me.role == UserRole.TEACHER

    entries = []
    for rank, row in enumerate(ranked, 1):
        student = db.query(User).filter(User.id == row.student_id).first()
        total = float(row.total or 0)
        pct = round(total / float(max_m) * 100, 1)

        # Everyone sees all names
        name = student.full_name if student else "Unknown"

        is_me = str(row.student_id) == str(me.id)

        entries.append({
            "rank": rank,
            "name": name,
            "score": total,
            "max_marks": float(max_m),
            "percentage": pct,
            "is_me": is_me,
            "grade": _grade(pct),
            "submission_id": str(row.sub_id) if is_me else None,
        })

    return {
        "paper_title": paper.title,
        "total_marks": paper.total_marks,
        "total_participants": len(entries),
        "entries": entries,
    }


def _grade(pct: float) -> str:
    if pct >= 90: return "A+"
    if pct >= 80: return "A"
    if pct >= 70: return "B"
    if pct >= 60: return "C"
    if pct >= 50: return "D"
    return "F"


# ═══════════════════════════════════════════════════════════════
# FEATURE #9 – PDF Report Card
# ═══════════════════════════════════════════════════════════════

@router.get("/submissions/{submission_id}/report")
def download_report(
    submission_id: str,
    db: Session = Depends(get_db),
    me: User = Depends(_me),
):
    """
    Generate and stream a PDF report card for the given submission.
    Student can only download their own; teacher can download any paper they own.
    """
    sub = db.query(AnswerSubmission).filter(AnswerSubmission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Authorization check
    if me.role == UserRole.STUDENT and str(sub.student_id) != str(me.id):
        raise HTTPException(status_code=403, detail="Not authorised")
    if me.role == UserRole.TEACHER:
        paper_obj = crud_paper.get_paper(db, str(sub.paper_id))
        if not paper_obj or str(paper_obj.teacher_id) != str(me.id):
            raise HTTPException(status_code=403, detail="Not authorised")

    student = db.query(User).filter(User.id == sub.student_id).first()
    paper = crud_paper.get_paper(db, str(sub.paper_id))
    evals = db.query(Evaluation, Question).join(
        Question, Evaluation.question_id == Question.id
    ).filter(Evaluation.submission_id == sub.id).order_by(Question.question_number).all()

    total = float(db.query(func.sum(Evaluation.marks_obtained)).filter(
        Evaluation.submission_id == sub.id
    ).scalar() or 0)
    max_m = float(db.query(func.sum(Evaluation.max_marks)).filter(
        Evaluation.submission_id == sub.id
    ).scalar() or 1)
    pct = round(total / max_m * 100, 1) if max_m else 0

    pdf_bytes = _build_pdf(student, paper, sub, evals, total, max_m, pct)

    filename = f"Report_{student.full_name.replace(' ','_')}_{paper.title[:20].replace(' ','_')}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _build_pdf(student, paper, sub, evals, total, max_m, pct):
    """Build a clean PDF using reportlab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=20, spaceAfter=4)
    sub_style   = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=10, textColor=colors.grey)
    heading2    = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceBefore=14, spaceAfter=4)
    body_style  = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9, leading=13)
    q_style     = ParagraphStyle("Q", parent=styles["Normal"], fontSize=9, leading=13, leftIndent=6)
    small_grey  = ParagraphStyle("SG", parent=styles["Normal"], fontSize=8, textColor=colors.grey)

    grade_color = (
        colors.HexColor("#16a34a") if pct >= 70 else
        colors.HexColor("#d97706") if pct >= 40 else
        colors.HexColor("#dc2626")
    )

    # ── IST time ────────────────────────────────────────────────
    submitted_ist = sub.submitted_at.strftime("%d %b %Y, %I:%M %p") if sub.submitted_at else "—"

    story = []

    # Header
    story.append(Paragraph("K12 Answer Evaluator", title_style))
    story.append(Paragraph("Result Report Card", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey, spaceAfter=12))

    # Student info table
    info_data = [
        ["Student", student.full_name if student else "—", "Submitted", submitted_ist],
        ["Paper", paper.title if paper else "—", "Subject", str(paper.subject.value if hasattr(paper.subject,'value') else paper.subject).capitalize() if paper else "—"],
        ["Class", str(paper.class_level) if paper else "—", "Duration", f"{paper.duration_minutes} min" if paper else "—"],
    ]
    info_table = Table(info_data, colWidths=[3*cm, 7*cm, 3*cm, 4*cm])
    info_table.setStyle(TableStyle([
        ("FONTSIZE",     (0,0), (-1,-1), 9),
        ("TEXTCOLOR",    (0,0), (0,-1), colors.grey),
        ("TEXTCOLOR",    (2,0), (2,-1), colors.grey),
        ("FONTNAME",     (0,0), (-1,-1), "Helvetica"),
        ("FONTNAME",     (1,0), (1,-1), "Helvetica-Bold"),
        ("FONTNAME",     (3,0), (3,-1), "Helvetica-Bold"),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 12))

    # Score summary box
    grade_str = _grade(pct)
    summary_data = [
        ["Total Marks", "Percentage", "Grade"],
        [f"{total:.0f} / {max_m:.0f}", f"{pct}%", grade_str],
    ]
    summary_tbl = Table(summary_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    summary_tbl.setStyle(TableStyle([
        ("FONTSIZE",        (0,0), (-1,-1), 11),
        ("FONTNAME",        (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME",        (0,1), (-1,-1), "Helvetica-Bold"),
        ("ALIGN",           (0,0), (-1,-1), "CENTER"),
        ("BACKGROUND",      (0,0), (-1,0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR",       (0,0), (-1,0), colors.white),
        ("BACKGROUND",      (0,1), (-1,-1), colors.HexColor("#f8fafc")),
        ("TEXTCOLOR",       (0,1), (0,1),  colors.HexColor("#0f172a")),
        ("TEXTCOLOR",       (1,1), (1,1),  grade_color),
        ("TEXTCOLOR",       (2,1), (2,1),  grade_color),
        ("FONTSIZE",        (0,1), (-1,1), 18),
        ("TOPPADDING",      (0,1), (-1,1), 10),
        ("BOTTOMPADDING",   (0,1), (-1,1), 10),
        ("ROWBACKGROUNDS",  (0,0), (-1,-1), [None]),
        ("BOX",             (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("INNERGRID",       (0,0), (-1,-1), 0.5, colors.lightgrey),
    ]))
    story.append(summary_tbl)
    story.append(Spacer(1, 16))

    # Per-question table
    story.append(Paragraph("Question-wise Breakdown", heading2))

    q_header = ["Q#", "Question", "Answer", "Marks", "Feedback"]
    q_rows = [q_header]
    for ev, q in evals:
        effective_marks = ev.override_marks if ev.teacher_override and ev.override_marks is not None else ev.marks_obtained
        feedback_raw = ev.override_feedback or ""
        if not feedback_raw and ev.feedback:
            import json as _json
            try:
                fb = _json.loads(ev.feedback)
                feedback_raw = fb.get("feedback", "")
            except Exception:
                feedback_raw = str(ev.feedback)[:120]

        q_rows.append([
            str(q.question_number),
            Paragraph(q.question_text[:120] + ("…" if len(q.question_text) > 120 else ""), q_style),
            Paragraph((ev.student_answer or "—")[:200], body_style),
            f"{effective_marks or 0:.0f}/{q.marks}",
            Paragraph(feedback_raw[:200] if feedback_raw else "—", small_grey),
        ])

    q_table = Table(q_rows, colWidths=[1*cm, 4.5*cm, 4.5*cm, 1.8*cm, 4.7*cm], repeatRows=1)
    q_table.setStyle(TableStyle([
        ("FONTSIZE",     (0,0), (-1,-1), 8),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND",   (0,0), (-1,0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
        ("ALIGN",        (0,0), (0,-1), "CENTER"),
        ("ALIGN",        (3,0), (3,-1), "CENTER"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ("BOX",          (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("INNERGRID",    (0,0), (-1,-1), 0.3, colors.lightgrey),
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
    ]))
    story.append(q_table)

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph(
        f"Generated by K12 Answer Evaluator · {datetime.utcnow().strftime('%d %b %Y %H:%M')} UTC",
        small_grey
    ))

    doc.build(story)
    return buf.getvalue()
