"""Tests for Seele API routes - all 7 endpoints, auth, validation."""

from unittest.mock import patch

MOCK_ONBOARDING_FRAGEN = [
    {
        "key": "motivation.aktuelle_situation",
        "frage": "Was beschreibt deine aktuelle Situation am besten?",
        "typ": "chips",
        "optionen": ["Aktiv auf Jobsuche", "Offen für Neues", "Karrierewechsel"],
        "mehrfach": False,
    },
    {
        "key": "arbeitsstil.arbeitsmodell",
        "frage": "Welches Arbeitsmodell passt zu dir?",
        "typ": "chips",
        "optionen": ["Remote", "Hybrid", "Vor Ort"],
        "mehrfach": True,
    },
    {
        "key": "motivation.wichtig_im_job",
        "frage": "Was ist dir im nächsten Job wichtig?",
        "typ": "chips_freitext",
        "optionen": ["Work-Life-Balance", "Gehalt", "Teamkultur"],
        "mehrfach": True,
        "max_auswahl": 5,
    },
    {
        "key": "motivation.wechsel_tempo",
        "frage": "Wie schnell möchtest du wechseln?",
        "typ": "chips",
        "optionen": ["Sofort verfügbar", "In 1-3 Monaten", "Schaue mich nur um"],
        "mehrfach": False,
    },
]


class TestSeeleProfilRoutes:
    """Tests for GET/PUT /api/seele/profil."""

    def test_get_profil_unauthenticated(self, client):
        """GET /profil returns 401 without auth."""
        response = client.get("/api/seele/profil")
        assert response.status_code in (401, 422)

    def test_get_profil_creates_if_missing(self, client, auth_headers):
        """GET /profil creates profile if none exists."""
        response = client.get("/api/seele/profil", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "profil" in data

    def test_get_profil_returns_existing(self, client, auth_headers):
        """GET /profil returns consistent data across calls."""
        r1 = client.get("/api/seele/profil", headers=auth_headers)
        r2 = client.get("/api/seele/profil", headers=auth_headers)
        assert r1.get_json()["profil"]["id"] == r2.get_json()["profil"]["id"]

    def test_update_profil(self, client, auth_headers):
        """PUT /profil updates profile fields."""
        # Create profile first
        client.get("/api/seele/profil", headers=auth_headers)

        response = client.put(
            "/api/seele/profil",
            headers=auth_headers,
            json={"motivation": {"aktuelle_situation": "Karrierewechsel"}},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["profil"]["profil"]["motivation"]["aktuelle_situation"] == "Karrierewechsel"

    def test_update_profil_no_data(self, client, auth_headers):
        """PUT /profil with empty body returns 400."""
        response = client.put(
            "/api/seele/profil",
            headers=auth_headers,
            content_type="application/json",
            data="",
        )
        assert response.status_code == 400

    def test_update_profil_unauthenticated(self, client):
        """PUT /profil returns 401 without auth."""
        response = client.put("/api/seele/profil", json={"test": "data"})
        assert response.status_code in (401, 422)


class TestSeeleSessionRoutes:
    """Tests for POST /sessions and GET /sessions/aktuell."""

    @patch("services.seele_service.generiere_micro_frage", return_value=None)
    @patch("services.seele_service.generiere_fragen", return_value=MOCK_ONBOARDING_FRAGEN)
    def test_starte_session(self, mock_gen, mock_micro, client, auth_headers):
        """POST /sessions starts onboarding session."""
        response = client.post(
            "/api/seele/sessions",
            headers=auth_headers,
            json={"session_typ": "onboarding"},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert data["session"]["session_typ"] == "onboarding"
        assert len(data["fragen"]) > 0

    def test_starte_session_invalid_type(self, client, auth_headers):
        """POST /sessions with invalid type returns 400."""
        response = client.post(
            "/api/seele/sessions",
            headers=auth_headers,
            json={"session_typ": "invalid"},
        )
        assert response.status_code == 400

    @patch("services.seele_service.generiere_micro_frage", return_value=None)
    @patch("services.seele_service.generiere_fragen", return_value=MOCK_ONBOARDING_FRAGEN)
    def test_starte_session_duplicate(self, mock_gen, mock_micro, client, auth_headers):
        """POST /sessions twice returns 400 (active session exists)."""
        client.post(
            "/api/seele/sessions",
            headers=auth_headers,
            json={"session_typ": "onboarding"},
        )
        response = client.post(
            "/api/seele/sessions",
            headers=auth_headers,
            json={"session_typ": "onboarding"},
        )
        assert response.status_code == 400
        assert "aktive Session" in response.get_json()["error"]

    def test_starte_session_unauthenticated(self, client):
        """POST /sessions returns 401 without auth."""
        response = client.post("/api/seele/sessions", json={"session_typ": "onboarding"})
        assert response.status_code in (401, 422)

    @patch("services.seele_service.generiere_micro_frage", return_value=None)
    @patch("services.seele_service.generiere_fragen", return_value=MOCK_ONBOARDING_FRAGEN)
    def test_aktuelle_session(self, mock_gen, mock_micro, client, auth_headers):
        """GET /sessions/aktuell returns active session."""
        # Start session first
        client.post(
            "/api/seele/sessions",
            headers=auth_headers,
            json={"session_typ": "onboarding"},
        )
        response = client.get("/api/seele/sessions/aktuell", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["session"] is not None

    def test_aktuelle_session_none(self, client, auth_headers):
        """GET /sessions/aktuell returns null when no active session."""
        response = client.get("/api/seele/sessions/aktuell", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["session"] is None


class TestSeeleAntwortRoutes:
    """Tests for POST /antworten and POST /antworten/ueberspringen."""

    @patch("services.seele_service.generiere_micro_frage", return_value=None)
    @patch("services.seele_service.generiere_fragen", return_value=MOCK_ONBOARDING_FRAGEN)
    def test_antwort_einreichen(self, mock_gen, mock_micro, client, auth_headers):
        """POST /antworten saves answer and returns next questions."""
        # Start session
        start = client.post(
            "/api/seele/sessions",
            headers=auth_headers,
            json={"session_typ": "onboarding"},
        )
        session_id = start.get_json()["session"]["id"]
        frage_key = start.get_json()["fragen"][0]["key"]

        # Submit answer
        response = client.post(
            "/api/seele/antworten",
            headers=auth_headers,
            json={
                "session_id": session_id,
                "frage_key": frage_key,
                "antwort": "Aktiv auf Jobsuche",
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "naechste_fragen" in data
        assert data["session"]["fragen_beantwortet"] == 1

    def test_antwort_no_data(self, client, auth_headers):
        """POST /antworten with empty body returns 400."""
        response = client.post(
            "/api/seele/antworten",
            headers=auth_headers,
            content_type="application/json",
            data="",
        )
        assert response.status_code == 400

    def test_antwort_missing_fields(self, client, auth_headers):
        """POST /antworten without required fields returns 400."""
        response = client.post(
            "/api/seele/antworten",
            headers=auth_headers,
            json={"antwort": "test"},
        )
        assert response.status_code == 400
        assert "erforderlich" in response.get_json()["error"]

    def test_antwort_invalid_session(self, client, auth_headers):
        """POST /antworten with non-existent session returns 400."""
        response = client.post(
            "/api/seele/antworten",
            headers=auth_headers,
            json={
                "session_id": 9999,
                "frage_key": "test.key",
                "antwort": "test",
            },
        )
        assert response.status_code == 400

    @patch("services.seele_service.generiere_micro_frage", return_value=None)
    @patch("services.seele_service.generiere_fragen", return_value=MOCK_ONBOARDING_FRAGEN)
    def test_frage_ueberspringen(self, mock_gen, mock_micro, client, auth_headers):
        """POST /antworten/ueberspringen skips question."""
        # Start session
        start = client.post(
            "/api/seele/sessions",
            headers=auth_headers,
            json={"session_typ": "onboarding"},
        )
        session_id = start.get_json()["session"]["id"]
        frage_key = start.get_json()["fragen"][0]["key"]

        # Skip
        response = client.post(
            "/api/seele/antworten/ueberspringen",
            headers=auth_headers,
            json={
                "session_id": session_id,
                "frage_key": frage_key,
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["session"]["fragen_uebersprungen"] == 1

    def test_ueberspringen_no_data(self, client, auth_headers):
        """POST /antworten/ueberspringen with empty body returns 400."""
        response = client.post(
            "/api/seele/antworten/ueberspringen",
            headers=auth_headers,
            content_type="application/json",
            data="",
        )
        assert response.status_code == 400

    def test_ueberspringen_missing_fields(self, client, auth_headers):
        """POST /antworten/ueberspringen without required fields returns 400."""
        response = client.post(
            "/api/seele/antworten/ueberspringen",
            headers=auth_headers,
            json={"session_id": 1},
        )
        assert response.status_code == 400


class TestSeeleCheckRoute:
    """Tests for GET /check."""

    def test_check_no_profile(self, client, auth_headers):
        """GET /check recommends session when no profile."""
        response = client.get("/api/seele/check?trigger=dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["soll_starten"] is True
        assert data["session_typ"] == "onboarding"

    def test_check_default_trigger(self, client, auth_headers):
        """GET /check defaults to dashboard trigger."""
        response = client.get("/api/seele/check", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_check_unauthenticated(self, client):
        """GET /check returns 401 without auth."""
        response = client.get("/api/seele/check")
        assert response.status_code in (401, 422)
