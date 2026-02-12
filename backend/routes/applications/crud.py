from flask import jsonify, request

from middleware.jwt_required import jwt_required_custom
from routes.applications import applications_bp
from services import application_service


@applications_bp.route("", methods=["GET"])
@jwt_required_custom
def list_applications(current_user):
    """List user's applications"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    pagination = application_service.list_applications(current_user.id, page=page, per_page=per_page)

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

    applications = application_service.get_timeline_applications(current_user.id, days_filter)

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
    app = application_service.get_application(app_id, current_user.id)

    if not app:
        return jsonify({"error": "Application not found"}), 404

    return jsonify({"success": True, "application": app.to_dict()}), 200


@applications_bp.route("/<int:app_id>", methods=["PUT"])
@jwt_required_custom
def update_application(app_id, current_user):
    """Update application (status, notes)"""
    app = application_service.get_application(app_id, current_user.id)

    if not app:
        return jsonify({"error": "Application not found"}), 404

    data = request.json
    application_service.update_application(app, data)

    return jsonify({"success": True, "application": app.to_dict()}), 200


@applications_bp.route("/<int:app_id>", methods=["DELETE"])
@jwt_required_custom
def delete_application(app_id, current_user):
    """Delete application"""
    app = application_service.get_application(app_id, current_user.id)

    if not app:
        return jsonify({"error": "Application not found"}), 404

    application_service.delete_application(app)

    return jsonify({"success": True, "message": "Application deleted"}), 200
