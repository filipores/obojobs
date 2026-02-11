import os
from datetime import datetime, timedelta

from flask import jsonify, request

from middleware.jwt_required import jwt_required_custom
from models import Application, db
from routes.applications import applications_bp


@applications_bp.route("", methods=["GET"])
@jwt_required_custom
def list_applications(current_user):
    """List user's applications"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    pagination = (
        Application.query.filter_by(user_id=current_user.id)
        .order_by(Application.datum.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify(
        {
            "success": True,
            "applications": [app.to_dict() for app in pagination.items],
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
            "pages": pagination.pages,
        }
    ), 200


@applications_bp.route("/timeline", methods=["GET"])
@jwt_required_custom
def get_timeline(current_user):
    """Get all applications with status history for timeline view.
    Supports filtering by time period: 7, 30, 90 days or all."""
    days_filter = request.args.get("days", "all")

    query = Application.query.filter_by(user_id=current_user.id)

    # Apply time filter
    if days_filter != "all":
        try:
            days = int(days_filter)
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Application.datum >= cutoff_date)
        except ValueError:
            pass  # Invalid filter, show all

    # Order by date descending
    applications = query.order_by(Application.datum.desc()).all()

    # Build timeline data
    timeline_data = []
    for app in applications:
        app_dict = app.to_dict()
        # Ensure status_history is included (it's in to_dict now)
        # Add a timeline-specific format if no history exists
        if not app_dict.get("status_history"):
            # Create initial history from datum if none exists
            app_dict["status_history"] = [{"status": "erstellt", "timestamp": app_dict["datum"]}]
        timeline_data.append(app_dict)

    return jsonify(
        {
            "success": True,
            "data": {
                "applications": timeline_data,
                "total": len(timeline_data),
                "filter": days_filter,
            },
        }
    ), 200


@applications_bp.route("/<int:app_id>", methods=["GET"])
@jwt_required_custom
def get_application(app_id, current_user):
    """Get application details"""
    app = Application.query.filter_by(id=app_id, user_id=current_user.id).first()

    if not app:
        return jsonify({"error": "Application not found"}), 404

    return jsonify({"success": True, "application": app.to_dict()}), 200


@applications_bp.route("/<int:app_id>", methods=["PUT"])
@jwt_required_custom
def update_application(app_id, current_user):
    """Update application (status, notes)"""
    app = Application.query.filter_by(id=app_id, user_id=current_user.id).first()

    if not app:
        return jsonify({"error": "Application not found"}), 404

    data = request.json

    if "status" in data:
        new_status = data["status"]
        # Only add to history if status actually changed
        if new_status != app.status:
            app.add_status_change(new_status)
        app.status = new_status
    if "notizen" in data:
        app.notizen = data["notizen"]

    db.session.commit()

    return jsonify({"success": True, "application": app.to_dict()}), 200


@applications_bp.route("/<int:app_id>", methods=["DELETE"])
@jwt_required_custom
def delete_application(app_id, current_user):
    """Delete application"""
    app = Application.query.filter_by(id=app_id, user_id=current_user.id).first()

    if not app:
        return jsonify({"error": "Application not found"}), 404

    # Delete PDF file
    if app.pdf_path and os.path.exists(app.pdf_path):
        os.remove(app.pdf_path)

    db.session.delete(app)
    db.session.commit()

    return jsonify({"success": True, "message": "Application deleted"}), 200
