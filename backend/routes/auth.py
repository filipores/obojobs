from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from services.auth_service import AuthService
from services.password_validator import PasswordValidator

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user"""
    data = request.json

    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        user = AuthService.register_user(email, password, full_name)
        return jsonify({"message": "User registered successfully", "user": user.to_dict()}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login user"""
    data = request.json

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        result = AuthService.login_user(email, password)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 401


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    return jsonify({"access_token": access_token}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """Get current user info"""
    current_user_id = get_jwt_identity()
    user = AuthService.get_user_by_id(int(current_user_id))

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict()), 200


@auth_bp.route("/password-requirements", methods=["GET"])
def password_requirements():
    """Get password requirements for frontend display"""
    return jsonify({"requirements": PasswordValidator.get_requirements()}), 200


@auth_bp.route("/validate-password", methods=["POST"])
def validate_password():
    """Validate password strength"""
    data = request.json
    password = data.get("password", "")

    result = PasswordValidator.validate(password)
    return jsonify(result), 200
