"""Tests for admin dashboard API endpoints."""

from datetime import datetime, timedelta

import pytest

from models import Application, Document, Subscription, User, db
from models.subscription import SubscriptionPlan, SubscriptionStatus


@pytest.fixture
def admin_user(app):
    """Create an admin user."""
    with app.app_context():
        user = User(
            email="admin@example.com",
            full_name="Admin User",
            email_verified=True,
            is_admin=True,
        )
        user.set_password("AdminPass123")
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "email": user.email, "password": "AdminPass123"}


@pytest.fixture
def admin_token(client, admin_user):
    """Get JWT token for admin user."""
    response = client.post(
        "/api/auth/login",
        json={"email": admin_user["email"], "password": admin_user["password"]},
    )
    return response.get_json()["access_token"]


@pytest.fixture
def admin_headers(admin_token):
    """Return headers with admin JWT authorization."""
    return {"Authorization": f"Bearer {admin_token}"}


class TestAdminRequired:
    """Test admin_required decorator."""

    def test_unauthenticated_returns_401(self, client):
        response = client.get("/api/admin/stats")
        assert response.status_code == 401

    def test_non_admin_returns_403(self, client, auth_headers):
        response = client.get("/api/admin/stats", headers=auth_headers)
        assert response.status_code == 403
        data = response.get_json()
        assert data["error"] == "Admin-Rechte erforderlich"

    def test_admin_returns_200(self, client, admin_headers):
        response = client.get("/api/admin/stats", headers=admin_headers)
        assert response.status_code == 200

    def test_inactive_admin_returns_401(self, client, app):
        """An admin user who is inactive should get 401."""
        with app.app_context():
            user = User(
                email="inactive_admin@example.com",
                full_name="Inactive Admin",
                email_verified=True,
                is_admin=True,
                is_active=False,
            )
            user.set_password("Pass1234!")
            db.session.add(user)
            db.session.commit()

        # Login won't work for inactive user in most cases, but let's
        # test with a token if we could get one
        # Since login checks is_active, we test the decorator directly
        # by setting the user inactive after getting a token
        with app.app_context():
            active_admin = User(
                email="temp_admin@example.com",
                full_name="Temp Admin",
                email_verified=True,
                is_admin=True,
                is_active=True,
            )
            active_admin.set_password("Pass1234!")
            db.session.add(active_admin)
            db.session.commit()
            temp_id = active_admin.id

        # Get token while active
        response = client.post(
            "/api/auth/login",
            json={"email": "temp_admin@example.com", "password": "Pass1234!"},
        )
        token = response.get_json()["access_token"]

        # Deactivate user
        with app.app_context():
            user = User.query.get(temp_id)
            user.is_active = False
            db.session.commit()

        # Now request should fail
        response = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


class TestAdminStats:
    """Test GET /api/admin/stats."""

    def test_stats_empty_db(self, client, admin_headers, admin_user):
        """Stats with only the admin user in DB."""
        response = client.get("/api/admin/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["total_users"] == 1  # admin user
        assert data["total_applications"] == 0
        assert data["applications_this_month"] == 0
        assert data["subscriptions"]["free"] == 1
        assert data["subscriptions"]["basic"] == 0
        assert data["subscriptions"]["pro"] == 0
        assert data["revenue_estimate"] == 0.0
        assert data["email_verified_count"] == 1  # admin is verified

    def test_stats_with_users_and_subscriptions(self, client, admin_headers, app):
        """Stats with multiple users, subscriptions, and applications."""
        with app.app_context():
            # Create users
            user1 = User(email="user1@example.com", full_name="User One", email_verified=True)
            user1.set_password("Pass1234!")
            user1.applications_this_month = 5

            user2 = User(email="user2@example.com", full_name="User Two", email_verified=False)
            user2.set_password("Pass1234!")
            user2.applications_this_month = 3

            db.session.add_all([user1, user2])
            db.session.flush()

            # Create subscriptions
            sub1 = Subscription(
                user_id=user1.id,
                plan=SubscriptionPlan.basic,
                status=SubscriptionStatus.active,
            )
            sub2 = Subscription(
                user_id=user2.id,
                plan=SubscriptionPlan.pro,
                status=SubscriptionStatus.active,
            )
            db.session.add_all([sub1, sub2])

            # Create applications
            app1 = Application(user_id=user1.id, firma="Company A", datum=datetime.utcnow())
            app2 = Application(user_id=user2.id, firma="Company B", datum=datetime.utcnow())
            app3 = Application(
                user_id=user1.id,
                firma="Company C",
                datum=datetime.utcnow() - timedelta(days=60),
            )
            db.session.add_all([app1, app2, app3])
            db.session.commit()

        response = client.get("/api/admin/stats", headers=admin_headers)
        data = response.get_json()
        assert data["total_users"] == 3  # admin + 2 users
        assert data["total_applications"] == 3
        assert data["applications_this_month"] == 8  # 5 + 3 + 0 (admin)
        assert data["subscriptions"]["basic"] == 1
        assert data["subscriptions"]["pro"] == 1
        assert data["subscriptions"]["free"] == 1  # admin user
        assert data["revenue_estimate"] == round(9.99 + 19.99, 2)
        assert data["email_verified_count"] == 2  # admin + user1

    def test_stats_active_users_30d(self, client, admin_headers, app):
        """Active users counts users with recent activity."""
        with app.app_context():
            # Old user with no recent apps
            old_user = User(
                email="old@example.com",
                full_name="Old User",
                created_at=datetime.utcnow() - timedelta(days=90),
            )
            old_user.set_password("Pass1234!")
            db.session.add(old_user)
            db.session.flush()

            # Old user with recent app
            active_old = User(
                email="active_old@example.com",
                full_name="Active Old",
                created_at=datetime.utcnow() - timedelta(days=90),
            )
            active_old.set_password("Pass1234!")
            db.session.add(active_old)
            db.session.flush()

            app_recent = Application(
                user_id=active_old.id,
                firma="Recent Co",
                datum=datetime.utcnow() - timedelta(days=5),
            )
            db.session.add(app_recent)
            db.session.commit()

        response = client.get("/api/admin/stats", headers=admin_headers)
        data = response.get_json()
        # Admin user (recent created_at) + active_old (recent app) = 2
        # old_user has no recent activity
        assert data["active_users_30d"] == 2

    def test_stats_signups_last_7_days(self, client, admin_headers, app):
        """Signups count only users created in last 7 days."""
        with app.app_context():
            old_user = User(
                email="old_signup@example.com",
                full_name="Old Signup",
                created_at=datetime.utcnow() - timedelta(days=10),
            )
            old_user.set_password("Pass1234!")
            db.session.add(old_user)
            db.session.commit()

        response = client.get("/api/admin/stats", headers=admin_headers)
        data = response.get_json()
        # Only admin user was created recently
        assert data["signups_last_7_days"] == 1


class TestAdminUsers:
    """Test GET /api/admin/users."""

    def test_list_users_default(self, client, admin_headers):
        """Default listing returns paginated users."""
        response = client.get("/api/admin/users", headers=admin_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "pages" in data
        assert data["total"] == 1  # admin user
        assert data["page"] == 1
        assert data["per_page"] == 20

    def test_list_users_pagination(self, client, admin_headers, app):
        """Pagination works correctly."""
        with app.app_context():
            for i in range(5):
                user = User(email=f"user{i}@example.com", full_name=f"User {i}")
                user.set_password("Pass1234!")
                db.session.add(user)
            db.session.commit()

        response = client.get("/api/admin/users?page=1&per_page=3", headers=admin_headers)
        data = response.get_json()
        assert len(data["users"]) == 3
        assert data["total"] == 6  # admin + 5 users
        assert data["pages"] == 2

        response = client.get("/api/admin/users?page=2&per_page=3", headers=admin_headers)
        data = response.get_json()
        assert len(data["users"]) == 3

    def test_list_users_search_by_email(self, client, admin_headers, app):
        """Search filter by email."""
        with app.app_context():
            user = User(email="findme@special.com", full_name="Some User")
            user.set_password("Pass1234!")
            db.session.add(user)
            db.session.commit()

        response = client.get("/api/admin/users?search=findme", headers=admin_headers)
        data = response.get_json()
        assert data["total"] == 1
        assert data["users"][0]["email"] == "findme@special.com"

    def test_list_users_search_by_name(self, client, admin_headers, app):
        """Search filter by full_name."""
        with app.app_context():
            user = User(email="someone@example.com", full_name="Unique Name XYZ")
            user.set_password("Pass1234!")
            db.session.add(user)
            db.session.commit()

        response = client.get("/api/admin/users?search=Unique", headers=admin_headers)
        data = response.get_json()
        assert data["total"] == 1
        assert data["users"][0]["name"] == "Unique Name XYZ"

    def test_list_users_plan_filter_free(self, client, admin_headers, app):
        """Filter by free plan."""
        with app.app_context():
            user = User(email="free_user@example.com", full_name="Free User")
            user.set_password("Pass1234!")
            db.session.add(user)
            db.session.flush()

            paid_user = User(email="paid@example.com", full_name="Paid User")
            paid_user.set_password("Pass1234!")
            db.session.add(paid_user)
            db.session.flush()

            sub = Subscription(
                user_id=paid_user.id,
                plan=SubscriptionPlan.basic,
                status=SubscriptionStatus.active,
            )
            db.session.add(sub)
            db.session.commit()

        response = client.get("/api/admin/users?plan=free", headers=admin_headers)
        data = response.get_json()
        # admin + free_user = 2 (paid_user excluded)
        assert data["total"] == 2
        emails = [u["email"] for u in data["users"]]
        assert "paid@example.com" not in emails

    def test_list_users_plan_filter_basic(self, client, admin_headers, app):
        """Filter by basic plan."""
        with app.app_context():
            user = User(email="basic_user@example.com", full_name="Basic User")
            user.set_password("Pass1234!")
            db.session.add(user)
            db.session.flush()

            sub = Subscription(
                user_id=user.id,
                plan=SubscriptionPlan.basic,
                status=SubscriptionStatus.active,
            )
            db.session.add(sub)
            db.session.commit()

        response = client.get("/api/admin/users?plan=basic", headers=admin_headers)
        data = response.get_json()
        assert data["total"] == 1
        assert data["users"][0]["email"] == "basic_user@example.com"

    def test_list_users_plan_filter_pro(self, client, admin_headers, app):
        """Filter by pro plan."""
        with app.app_context():
            user = User(email="pro_user@example.com", full_name="Pro User")
            user.set_password("Pass1234!")
            db.session.add(user)
            db.session.flush()

            sub = Subscription(
                user_id=user.id,
                plan=SubscriptionPlan.pro,
                status=SubscriptionStatus.active,
            )
            db.session.add(sub)
            db.session.commit()

        response = client.get("/api/admin/users?plan=pro", headers=admin_headers)
        data = response.get_json()
        assert data["total"] == 1
        assert data["users"][0]["email"] == "pro_user@example.com"

    def test_list_users_sort_email_asc(self, client, admin_headers, app):
        """Sort by email ascending."""
        with app.app_context():
            user = User(email="aaa@example.com", full_name="AAA")
            user.set_password("Pass1234!")
            db.session.add(user)
            user2 = User(email="zzz@example.com", full_name="ZZZ")
            user2.set_password("Pass1234!")
            db.session.add(user2)
            db.session.commit()

        response = client.get("/api/admin/users?sort=email&order=asc", headers=admin_headers)
        data = response.get_json()
        emails = [u["email"] for u in data["users"]]
        assert emails == sorted(emails)

    def test_list_users_sort_created_at_desc(self, client, admin_headers, app):
        """Sort by created_at descending (default)."""
        with app.app_context():
            old_user = User(
                email="old@example.com",
                full_name="Old",
                created_at=datetime.utcnow() - timedelta(days=10),
            )
            old_user.set_password("Pass1234!")
            db.session.add(old_user)
            db.session.commit()

        response = client.get("/api/admin/users", headers=admin_headers)
        data = response.get_json()
        # Admin (newest) should be first
        assert data["users"][0]["email"] == "admin@example.com"

    def test_list_users_includes_application_info(self, client, admin_headers, app):
        """User entries include application_count and last_application_date."""
        with app.app_context():
            user = User(email="appuser@example.com", full_name="App User")
            user.set_password("Pass1234!")
            db.session.add(user)
            db.session.flush()

            app1 = Application(
                user_id=user.id,
                firma="Co A",
                datum=datetime(2025, 6, 1),
            )
            app2 = Application(
                user_id=user.id,
                firma="Co B",
                datum=datetime(2025, 8, 15),
            )
            db.session.add_all([app1, app2])
            db.session.commit()

        response = client.get("/api/admin/users?search=appuser", headers=admin_headers)
        data = response.get_json()
        user_data = data["users"][0]
        assert user_data["application_count"] == 2
        assert user_data["last_application_date"] == "2025-08-15T00:00:00"

    def test_list_users_shows_plan(self, client, admin_headers, app):
        """User entries show plan as string."""
        with app.app_context():
            user = User(email="planuser@example.com", full_name="Plan User")
            user.set_password("Pass1234!")
            db.session.add(user)
            db.session.flush()

            sub = Subscription(
                user_id=user.id,
                plan=SubscriptionPlan.pro,
                status=SubscriptionStatus.active,
            )
            db.session.add(sub)
            db.session.commit()

        response = client.get("/api/admin/users?search=planuser", headers=admin_headers)
        data = response.get_json()
        assert data["users"][0]["plan"] == "pro"
        assert data["users"][0]["status"] == "active"


class TestAdminUserDetail:
    """Test GET /api/admin/users/<id>."""

    def test_get_user_detail(self, client, admin_headers, app):
        """Returns detailed user info."""
        with app.app_context():
            user = User(email="detail@example.com", full_name="Detail User", email_verified=True)
            user.set_password("Pass1234!")
            db.session.add(user)
            db.session.flush()
            user_id = user.id

            doc = Document(user_id=user.id, original_filename="cv.pdf", file_path="/tmp/cv.pdf", doc_type="lebenslauf")
            app1 = Application(
                user_id=user.id, firma="Corp A", position="Dev", datum=datetime.utcnow(), status="erstellt"
            )
            app2 = Application(
                user_id=user.id, firma="Corp B", position="PM", datum=datetime.utcnow(), status="versendet"
            )
            db.session.add_all([doc, app1, app2])
            db.session.commit()

        response = client.get(f"/api/admin/users/{user_id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.get_json()
        user_data = data["user"]
        assert user_data["email"] == "detail@example.com"
        assert user_data["document_count"] == 1
        assert user_data["application_count"] == 2
        assert len(user_data["recent_applications"]) == 2
        assert user_data["recent_applications"][0]["firma"] in ("Corp A", "Corp B")

    def test_get_user_detail_not_found(self, client, admin_headers):
        """Returns 404 for non-existent user."""
        response = client.get("/api/admin/users/99999", headers=admin_headers)
        assert response.status_code == 404

    def test_get_user_detail_includes_admin_flag(self, client, admin_headers, admin_user):
        """User detail includes is_admin field."""
        response = client.get(f"/api/admin/users/{admin_user['id']}", headers=admin_headers)
        data = response.get_json()
        assert data["user"]["is_admin"] is True

    def test_get_user_detail_recent_apps_limited_to_10(self, client, admin_headers, app):
        """Recent applications limited to 10."""
        with app.app_context():
            user = User(email="many_apps@example.com", full_name="Many Apps")
            user.set_password("Pass1234!")
            db.session.add(user)
            db.session.flush()
            user_id = user.id

            for i in range(15):
                a = Application(
                    user_id=user.id,
                    firma=f"Company {i}",
                    datum=datetime.utcnow() - timedelta(days=i),
                )
                db.session.add(a)
            db.session.commit()

        response = client.get(f"/api/admin/users/{user_id}", headers=admin_headers)
        data = response.get_json()
        assert len(data["user"]["recent_applications"]) == 10


class TestAdminUserPatch:
    """Test PATCH /api/admin/users/<id>."""

    def test_toggle_is_active(self, client, admin_headers, app):
        """Can toggle is_active."""
        with app.app_context():
            user = User(email="toggle@example.com", full_name="Toggle User")
            user.set_password("Pass1234!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        response = client.patch(
            f"/api/admin/users/{user_id}",
            json={"is_active": False},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["user"]["is_active"] is False

    def test_toggle_is_admin(self, client, admin_headers, app):
        """Can toggle is_admin."""
        with app.app_context():
            user = User(email="promote@example.com", full_name="Promote User")
            user.set_password("Pass1234!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        response = client.patch(
            f"/api/admin/users/{user_id}",
            json={"is_admin": True},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["user"]["is_admin"] is True

    def test_toggle_email_verified(self, client, admin_headers, app):
        """Can toggle email_verified."""
        with app.app_context():
            user = User(email="verify@example.com", full_name="Verify User")
            user.set_password("Pass1234!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        response = client.patch(
            f"/api/admin/users/{user_id}",
            json={"email_verified": True},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["user"]["email_verified"] is True

    def test_reject_invalid_fields(self, client, admin_headers, app):
        """Rejects fields not in allowed list."""
        with app.app_context():
            user = User(email="reject@example.com", full_name="Reject User")
            user.set_password("Pass1234!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        response = client.patch(
            f"/api/admin/users/{user_id}",
            json={"email": "hacked@example.com"},
            headers=admin_headers,
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "Unzulässige Felder" in data["error"]

    def test_patch_not_found(self, client, admin_headers):
        """Returns 404 for non-existent user."""
        response = client.patch(
            "/api/admin/users/99999",
            json={"is_active": False},
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_patch_no_data(self, client, admin_headers, app):
        """Returns 400 when no JSON body."""
        with app.app_context():
            user = User(email="nodata@example.com", full_name="No Data")
            user.set_password("Pass1234!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        response = client.patch(
            f"/api/admin/users/{user_id}",
            headers=admin_headers,
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_patch_multiple_fields(self, client, admin_headers, app):
        """Can update multiple allowed fields at once."""
        with app.app_context():
            user = User(email="multi@example.com", full_name="Multi User")
            user.set_password("Pass1234!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        response = client.patch(
            f"/api/admin/users/{user_id}",
            json={"is_active": False, "is_admin": True, "email_verified": True},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["user"]["is_active"] is False
        assert data["user"]["is_admin"] is True
        assert data["user"]["email_verified"] is True

    def test_cannot_deactivate_self(self, client, admin_headers, admin_user):
        """Admin cannot deactivate their own account."""
        response = client.patch(
            f"/api/admin/users/{admin_user['id']}",
            json={"is_active": False},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "eigenes Konto" in response.get_json()["error"]

    def test_cannot_remove_own_admin(self, client, admin_headers, admin_user):
        """Admin cannot remove their own admin rights."""
        response = client.patch(
            f"/api/admin/users/{admin_user['id']}",
            json={"is_admin": False},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "Admin-Rechte" in response.get_json()["error"]

    def test_can_verify_own_email(self, client, admin_headers, admin_user):
        """Admin can still toggle email_verified on their own account."""
        response = client.patch(
            f"/api/admin/users/{admin_user['id']}",
            json={"email_verified": True},
            headers=admin_headers,
        )
        assert response.status_code == 200

    def test_non_admin_cannot_patch(self, client, auth_headers, test_user):
        """Non-admin user gets 403 on PATCH."""
        response = client.patch(
            f"/api/admin/users/{test_user['id']}",
            json={"is_admin": True},
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestAdminUserApplications:
    """Test GET /api/admin/users/<id>/applications."""

    def test_get_user_applications(self, client, admin_headers, app):
        """Returns full application data for a user."""
        with app.app_context():
            user = User(email="apps@example.com", full_name="Apps User")
            user.set_password("Pass1234!")
            db.session.add(user)
            db.session.flush()
            user_id = user.id

            app1 = Application(
                user_id=user.id,
                firma="Firma A",
                position="Developer",
                datum=datetime.utcnow(),
                status="erstellt",
                einleitung="Sehr geehrte Damen und Herren",
                betreff="Bewerbung als Developer",
                email_text="Hiermit bewerbe ich mich...",
                notizen="Telefonisch nachfragen",
                quelle="https://example.com/job",
                ansprechpartner="Herr Müller",
            )
            app2 = Application(
                user_id=user.id,
                firma="Firma B",
                position="PM",
                datum=datetime.utcnow() - timedelta(days=5),
                status="versendet",
            )
            db.session.add_all([app1, app2])
            db.session.commit()

        response = client.get(f"/api/admin/users/{user_id}/applications", headers=admin_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["applications"]) == 2
        # Newest first
        assert data["applications"][0]["firma"] == "Firma A"
        assert data["applications"][0]["einleitung"] == "Sehr geehrte Damen und Herren"
        assert data["applications"][0]["betreff"] == "Bewerbung als Developer"
        assert data["applications"][0]["email_text"] == "Hiermit bewerbe ich mich..."
        assert data["applications"][0]["notizen"] == "Telefonisch nachfragen"
        assert data["applications"][0]["quelle"] == "https://example.com/job"
        assert data["applications"][0]["ansprechpartner"] == "Herr Müller"
        assert data["applications"][1]["firma"] == "Firma B"

    def test_get_user_applications_empty(self, client, admin_headers, app):
        """Returns empty list when user has no applications."""
        with app.app_context():
            user = User(email="noapps@example.com", full_name="No Apps")
            user.set_password("Pass1234!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        response = client.get(f"/api/admin/users/{user_id}/applications", headers=admin_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["applications"] == []

    def test_get_user_applications_not_found(self, client, admin_headers):
        """Returns 404 for non-existent user."""
        response = client.get("/api/admin/users/99999/applications", headers=admin_headers)
        assert response.status_code == 404
