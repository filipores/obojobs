from datetime import datetime
from typing import Any

from flask import Response, jsonify, request

from middleware.jwt_required import jwt_required_custom
from routes.applications import applications_bp
from services import application_service
from services.interview_evaluator import InterviewEvaluator
from services.interview_generator import InterviewGenerator
from services.star_analyzer import STARAnalyzer
from services.web_scraper import WebScraper

VALID_INTERVIEW_RESULTS = ["scheduled", "completed", "passed", "rejected", "offer_received"]


@applications_bp.route("/<int:app_id>/generate-questions", methods=["POST"])
@jwt_required_custom
def generate_interview_questions(app_id: int, current_user: Any) -> tuple[Response, int]:
    """Generate interview questions for an application based on the job posting.

    Uses Claude API to generate personalized interview questions considering:
    - The job posting and requirements
    - The user's skills and experience
    - German interview culture

    Request body (optional):
        - question_count: Number of questions to generate (10-15, default 12)

    Returns:
        - questions: List of generated interview questions with sample answers
    """
    app = application_service.get_application(app_id, current_user.id)

    if not app:
        return jsonify({"success": False, "error": "Application not found"}), 404

    data = request.json or {}
    question_count = data.get("question_count", 12)

    # Get job text from various sources
    job_text = ""

    # First try notizen
    if app.notizen:
        job_text = app.notizen.replace("[Draft - Job-Fit Analyse]", "").strip()

    # Then try to scrape from quelle URL
    if not job_text and app.quelle and app.quelle.startswith(("http://", "https://")):
        try:
            scraper = WebScraper()
            job_data = scraper.fetch_job_posting(app.quelle)
            job_text = job_data.get("text", "")
        except Exception:
            pass

    if not job_text:
        return jsonify(
            {
                "success": False,
                "error": "Keine Stellenbeschreibung vorhanden. Bitte stelle sicher, dass die Bewerbung eine Stellenanzeige-URL oder Beschreibung hat.",
            }
        ), 400

    # Get user skills for personalized questions
    user_skills = application_service.get_user_skills(current_user.id)
    skills_list = [{"skill_name": s.skill_name, "category": s.skill_category} for s in user_skills]

    try:
        generator = InterviewGenerator()
        questions = generator.generate_questions(
            job_text=job_text,
            firma=app.firma or "Unbekannt",
            position=app.position or "Unbekannt",
            user_skills=skills_list,
            question_count=question_count,
        )

        if not questions:
            return jsonify(
                {"success": False, "error": "Keine Interview-Fragen generiert. Bitte versuche es erneut."}
            ), 500

        # Delete existing and save generated questions
        saved_questions = application_service.save_interview_questions(app_id, questions)

        return jsonify(
            {
                "success": True,
                "data": {
                    "application_id": app_id,
                    "questions": [q.to_dict() for q in saved_questions],
                    "total": len(saved_questions),
                },
                "message": f"{len(saved_questions)} Interview-Fragen generiert",
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": f"Fehler bei der Fragen-Generierung: {str(e)}"}), 500


@applications_bp.route("/<int:app_id>/interview-questions", methods=["GET"])
@jwt_required_custom
def get_interview_questions(app_id: int, current_user: Any) -> tuple[Response, int]:
    """Get all interview questions for an application.

    Returns questions grouped by type (behavioral, technical, situational,
    company_specific, salary_negotiation).

    Query params:
        - type: Filter by question type (optional)
    """
    app = application_service.get_application(app_id, current_user.id)

    if not app:
        return jsonify({"success": False, "error": "Application not found"}), 404

    question_type = request.args.get("type")
    questions = application_service.get_interview_questions(app_id, question_type=question_type)

    # Group by type
    grouped = {
        "behavioral": [],
        "technical": [],
        "situational": [],
        "company_specific": [],
        "salary_negotiation": [],
    }

    for q in questions:
        if q.question_type in grouped:
            grouped[q.question_type].append(q.to_dict())

    return jsonify(
        {
            "success": True,
            "data": {
                "application_id": app_id,
                "questions": grouped,
                "all_questions": [q.to_dict() for q in questions],
                "total": len(questions),
            },
        }
    ), 200


@applications_bp.route("/interview/evaluate-answer", methods=["POST"])
@jwt_required_custom
def evaluate_interview_answer(current_user: Any) -> tuple[Response, int]:
    """Evaluate an interview answer and provide AI feedback.

    Request body:
        - question_id: ID of the interview question being answered
        - answer_text: The user's answer to evaluate
        - application_id: Optional, for context (position, company)

    Returns:
        - evaluation: Structured feedback with score, strengths, improvements
        - star_analysis: STAR method analysis (for behavioral questions only)
    """
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "Request body required"}), 400

    question_id = data.get("question_id")
    answer_text = data.get("answer_text", "").strip()

    if not question_id:
        return jsonify({"success": False, "error": "question_id ist erforderlich"}), 400

    if not answer_text:
        return jsonify({"success": False, "error": "answer_text ist erforderlich"}), 400

    if len(answer_text) < 10:
        return jsonify(
            {"success": False, "error": "Die Antwort ist zu kurz. Bitte gib eine ausführlichere Antwort."}
        ), 400

    # Get the question
    question = application_service.get_interview_question(question_id)
    if not question:
        return jsonify({"success": False, "error": "Frage nicht gefunden"}), 404

    # Verify user has access to this question's application
    app = application_service.get_application(question.application_id, current_user.id)

    if not app:
        return jsonify({"success": False, "error": "Keine Berechtigung"}), 403

    try:
        evaluator = InterviewEvaluator()
        evaluation = evaluator.evaluate_answer(
            question_text=question.question_text,
            question_type=question.question_type,
            answer_text=answer_text,
            position=app.position,
            firma=app.firma,
        )

        return jsonify(
            {
                "success": True,
                "data": {
                    "question_id": question_id,
                    "question_type": question.question_type,
                    "evaluation": evaluation,
                },
                "message": "Antwort erfolgreich bewertet",
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": f"Fehler bei der Bewertung: {str(e)}"}), 500


@applications_bp.route("/interview/summary", methods=["POST"])
@jwt_required_custom
def get_interview_summary(current_user: Any) -> tuple[Response, int]:
    """Generate a summary of all interview answers for a mock interview session.

    Request body:
        - application_id: The application ID
        - answers: List of answer evaluations with scores and feedback

    Returns:
        - summary: Overall assessment with category scores and recommendations
    """
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "Request body required"}), 400

    application_id = data.get("application_id")
    answers = data.get("answers", [])

    if not application_id:
        return jsonify({"success": False, "error": "application_id ist erforderlich"}), 400

    # Verify user has access to this application
    app = application_service.get_application(application_id, current_user.id)

    if not app:
        return jsonify({"success": False, "error": "Bewerbung nicht gefunden"}), 404

    try:
        evaluator = InterviewEvaluator()
        summary = evaluator.generate_interview_summary(
            answers=answers,
            position=app.position,
            firma=app.firma,
        )

        return jsonify(
            {
                "success": True,
                "data": {
                    "application_id": application_id,
                    "summary": summary,
                },
                "message": "Zusammenfassung erstellt",
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": f"Fehler bei der Zusammenfassung: {str(e)}"}), 500


@applications_bp.route("/interview/analyze-star", methods=["POST"])
@jwt_required_custom
def analyze_star_method(current_user: Any) -> tuple[Response, int]:
    """Perform detailed STAR method analysis on a behavioral interview answer.

    Provides specialized feedback for behavioral questions with detailed analysis
    of each STAR component (Situation, Task, Action, Result) and improvement suggestions.

    Request body:
        - question_id: (optional) ID of the interview question
        - question_text: (required if no question_id) The question text
        - answer_text: The user's answer to analyze
        - application_id: Optional, for context (position, company)

    Returns:
        - star_analysis: Detailed analysis with:
          - overall_star_score: 0-100 compliance score
          - components: Analysis for each STAR component
          - improvement_suggestions: Specific improvement tips
          - improved_answer_example: Example of improved answer
    """
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "Request body required"}), 400

    question_id = data.get("question_id")
    question_text = data.get("question_text", "").strip()
    answer_text = data.get("answer_text", "").strip()
    application_id = data.get("application_id")

    # Get question text from question_id if not provided
    if not question_text and question_id:
        question = application_service.get_interview_question(question_id)
        if question:
            question_text = question.question_text
            if not application_id:
                application_id = question.application_id

    if not question_text:
        return jsonify({"success": False, "error": "question_text oder question_id ist erforderlich"}), 400

    if not answer_text:
        return jsonify({"success": False, "error": "answer_text ist erforderlich"}), 400

    if len(answer_text) < 20:
        return jsonify(
            {
                "success": False,
                "error": "Die Antwort ist zu kurz für eine STAR-Analyse. Bitte gib eine ausführlichere Antwort.",
            }
        ), 400

    # Get context from application if available
    position = None
    firma = None
    if application_id:
        app = application_service.get_application(application_id, current_user.id)
        if app:
            position = app.position
            firma = app.firma

    try:
        analyzer = STARAnalyzer()
        analysis = analyzer.analyze_star(
            question_text=question_text,
            answer_text=answer_text,
            position=position,
            firma=firma,
        )

        return jsonify(
            {
                "success": True,
                "data": {
                    "question_id": question_id,
                    "question_text": question_text,
                    "star_analysis": analysis,
                },
                "message": "STAR-Analyse erfolgreich",
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": f"Fehler bei der STAR-Analyse: {str(e)}"}), 500


@applications_bp.route("/interview/star-components", methods=["GET"])
@jwt_required_custom
def get_star_components(current_user: Any) -> tuple[Response, int]:
    """Get descriptions of STAR method components.

    Returns detailed information about each STAR component for help/reference.
    """
    analyzer = STARAnalyzer()
    return jsonify(
        {
            "success": True,
            "data": {
                "components": analyzer.get_component_descriptions(),
            },
        }
    ), 200


# ==================== Interview Result Tracking ====================


@applications_bp.route("/<int:app_id>/interview-result", methods=["PUT"])
@jwt_required_custom
def update_interview_result(app_id: int, current_user: Any) -> tuple[Response, int]:
    """Update interview result and feedback for an application.

    Request body:
        - interview_date: (optional) ISO date string for scheduled interview
        - interview_result: (optional) One of: scheduled, completed, passed, rejected, offer_received
        - interview_feedback: (optional) Free text for personal notes after interview

    Returns:
        - application: Updated application with interview fields
    """
    app = application_service.get_application(app_id, current_user.id)

    if not app:
        return jsonify({"success": False, "error": "Application not found"}), 404

    data = request.json or {}

    # Update interview_date
    if "interview_date" in data:
        date_value = data["interview_date"]
        if date_value:
            try:
                # Parse ISO format date
                if isinstance(date_value, str):
                    # Handle both datetime and date-only formats
                    if "T" in date_value:
                        app.interview_date = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
                    else:
                        app.interview_date = datetime.fromisoformat(date_value)
                else:
                    app.interview_date = None
            except ValueError:
                return jsonify(
                    {
                        "success": False,
                        "error": "Ungültiges Datumsformat. Bitte ISO-Format verwenden (YYYY-MM-DD oder YYYY-MM-DDTHH:MM:SS)",
                    }
                ), 400
        else:
            app.interview_date = None

    # Update interview_result
    if "interview_result" in data:
        result_value = data["interview_result"]
        if result_value:
            if result_value not in VALID_INTERVIEW_RESULTS:
                return jsonify(
                    {"success": False, "error": f"Ungültiges Ergebnis. Erlaubt: {', '.join(VALID_INTERVIEW_RESULTS)}"}
                ), 400
            app.interview_result = result_value
        else:
            app.interview_result = None

    # Update interview_feedback
    if "interview_feedback" in data:
        app.interview_feedback = data["interview_feedback"]

    application_service.commit()

    return jsonify({"success": True, "application": app.to_dict(), "message": "Interview-Ergebnis aktualisiert"}), 200


@applications_bp.route("/interview-stats", methods=["GET"])
@jwt_required_custom
def get_interview_statistics(current_user: Any) -> tuple[Response, int]:
    """Get interview statistics for the current user.

    Returns aggregated interview data:
        - total_interviews: Total applications with interview scheduled/completed
        - success_rate: Percentage of passed interviews out of completed
        - result_breakdown: Count per interview_result status
        - upcoming_interviews: List of scheduled interviews
        - recent_results: List of recent interview outcomes
    """
    stats = application_service.get_interview_statistics(current_user.id)

    result_breakdown = dict.fromkeys(VALID_INTERVIEW_RESULTS, 0)
    for result, count in stats["result_counts"]:
        if result in result_breakdown:
            result_breakdown[result] = count

    # Calculate success rate (passed + offer_received out of all completed outcomes)
    completed_outcomes = (
        result_breakdown.get("passed", 0)
        + result_breakdown.get("rejected", 0)
        + result_breakdown.get("offer_received", 0)
    )
    successful_outcomes = result_breakdown.get("passed", 0) + result_breakdown.get("offer_received", 0)
    success_rate = round((successful_outcomes / completed_outcomes * 100) if completed_outcomes > 0 else 0, 1)

    return jsonify(
        {
            "success": True,
            "data": {
                "total_interviews": stats["total_with_results"],
                "success_rate": success_rate,
                "result_breakdown": result_breakdown,
                "upcoming_interviews": [
                    {
                        "id": app.id,
                        "firma": app.firma,
                        "position": app.position,
                        "interview_date": app.interview_date.isoformat() if app.interview_date else None,
                    }
                    for app in stats["upcoming"]
                ],
                "recent_results": [
                    {
                        "id": app.id,
                        "firma": app.firma,
                        "position": app.position,
                        "interview_date": app.interview_date.isoformat() if app.interview_date else None,
                        "interview_result": app.interview_result,
                        "interview_feedback": app.interview_feedback,
                    }
                    for app in stats["recent_results"]
                ],
            },
        }
    ), 200
