"""
Architectural constraint tests for obojobs backend.

These tests use the Python `ast` module to parse imports and enforce
layering rules. They run without importing application code, so they
are fast and have zero side-effects.

Layer rules (top = may depend on layers below):
    routes  ->  services  ->  models
    routes  -X->  models   (must go through services)
    models  -X->  services, routes
    services -X-> routes

Additional rules:
    - Anthropic API usage only in services/
    - No single Python file > 500 lines (keeps modules reviewable)
"""

import ast
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parent.parent
ROUTES_DIR = BACKEND_DIR / "routes"
MODELS_DIR = BACKEND_DIR / "models"
SERVICES_DIR = BACKEND_DIR / "services"


def _python_files(directory: Path) -> list[Path]:
    """Return all .py files under *directory*, excluding __pycache__."""
    return sorted(p for p in directory.rglob("*.py") if "__pycache__" not in str(p))


def _get_imports(filepath: Path) -> list[dict]:
    """Parse *filepath* and return a list of import records.

    Each record is a dict with keys:
        - "module": the module string (e.g. "models", "models.user")
        - "names": list of imported names
        - "lineno": line number in the source file
        - "type": "from" or "import"
    """
    source = filepath.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError:
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(
                {
                    "module": node.module,
                    "names": [alias.name for alias in node.names],
                    "lineno": node.lineno,
                    "type": "from",
                }
            )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(
                    {
                        "module": alias.name,
                        "names": [alias.name],
                        "lineno": node.lineno,
                        "type": "import",
                    }
                )
    return imports


def _imports_package(imports: list[dict], package: str) -> list[dict]:
    """Filter imports that reference *package* (top-level module name)."""
    return [imp for imp in imports if imp["module"] == package or imp["module"].startswith(f"{package}.")]


def _relative_path(filepath: Path) -> str:
    """Return path relative to BACKEND_DIR for readable messages."""
    return str(filepath.relative_to(BACKEND_DIR))


# ---------------------------------------------------------------------------
# Known violations (existing tech debt — each entry should have a TODO ticket)
# Remove entries as the code is refactored to comply.
# ---------------------------------------------------------------------------

# Task 8: Routes that currently import models directly.
# TODO: Refactor these routes to access data through service layer instead.
_ROUTES_IMPORTING_MODELS_ALLOWLIST: set[str] = set()

# Task 10: Files outside services/ that currently use the Anthropic API.
# TODO: Move Anthropic usage in routes/applications/ats.py into a service.
_ANTHROPIC_OUTSIDE_SERVICES_ALLOWLIST: set[str] = {
    "routes/applications/ats.py",
}

# Task 10: Files that currently exceed the line limit.
# TODO: Split these files into smaller, focused modules.
_FILE_SIZE_ALLOWLIST: set[str] = {
    "services/web_scraper.py",
    "services/qwen_client.py",
    "services/salary_coach.py",
    "services/company_researcher.py",
    "services/job_fit_calculator.py",
    "routes/email.py",
    "routes/auth.py",
    "routes/applications/generation.py",
    "tests/test_auth.py",
    "tests/test_applications.py",
    "tests/test_ats_routes.py",
    "tests/test_admin.py",
    "tests/test_generic_scraper.py",
    "tests/test_ats_service.py",
    "tests/test_password_reset.py",
    "tests/test_documents.py",
    "tests/test_generator_service.py",
}


# ---------------------------------------------------------------------------
# Test: Routes must NOT import models directly (Task 8)
# ---------------------------------------------------------------------------


class TestRoutesDoNotImportModels:
    """Routes should access data through the service layer, never by
    importing model classes directly.

    WHY: Keeping routes thin and free of ORM details makes them easier
    to test, easier to refactor, and prevents business logic from leaking
    into the HTTP layer.

    HOW TO FIX a violation:
        1. Move the data-access logic into an existing or new service in
           services/.
        2. Have the route call the service function instead.
        3. Remove the model import from the route file.
        4. Remove the file from _ROUTES_IMPORTING_MODELS_ALLOWLIST in
           this test.
    """

    def _violating_routes(self) -> list[tuple[str, list[dict]]]:
        """Return route files that import from models, excluding allowlisted."""
        violations = []
        for filepath in _python_files(ROUTES_DIR):
            rel = _relative_path(filepath)
            if rel in _ROUTES_IMPORTING_MODELS_ALLOWLIST:
                continue
            imports = _get_imports(filepath)
            model_imports = _imports_package(imports, "models")
            if model_imports:
                violations.append((rel, model_imports))
        return violations

    def test_no_new_model_imports_in_routes(self):
        """No route file (outside the allowlist) may import from models.

        If this test fails, a NEW route file is importing models directly.
        See the class docstring for how to fix it.
        """
        violations = self._violating_routes()
        if violations:
            msg_parts = [
                "Route files must not import models directly. " "Use the service layer instead.\n" "Violations found:"
            ]
            for rel, imps in violations:
                for imp in imps:
                    msg_parts.append(
                        f"  - {rel}:{imp['lineno']}  " f"'from {imp['module']} import {', '.join(imp['names'])}'"
                    )
            msg_parts.append(
                "\nFIX: Move data access into services/ and call the "
                "service from the route. Then remove the model import."
            )
            pytest.fail("\n".join(msg_parts))

    def test_all_existing_violations_are_tracked(self):
        """Ensure no route files import models directly.

        All routes have been refactored to use the service layer.
        """
        all_violations = []
        for filepath in _python_files(ROUTES_DIR):
            rel = _relative_path(filepath)
            imports = _get_imports(filepath)
            model_imports = _imports_package(imports, "models")
            if model_imports:
                all_violations.append(rel)

        assert not all_violations, "Route files must not import models directly. " "Use the service layer instead."

    def test_allowlist_has_no_stale_entries(self):
        """Allowlist entries must correspond to actual violations.

        If a route was refactored and no longer imports models, its
        entry should be removed from _ROUTES_IMPORTING_MODELS_ALLOWLIST.
        """
        actual_violators = set()
        for filepath in _python_files(ROUTES_DIR):
            rel = _relative_path(filepath)
            imports = _get_imports(filepath)
            model_imports = _imports_package(imports, "models")
            if model_imports:
                actual_violators.add(rel)

        stale = _ROUTES_IMPORTING_MODELS_ALLOWLIST - actual_violators
        if stale:
            pytest.fail(
                "These files are in the allowlist but no longer import "
                "models. Remove them from _ROUTES_IMPORTING_MODELS_ALLOWLIST "
                f"in test_architecture.py:\n  {', '.join(sorted(stale))}"
            )


# ---------------------------------------------------------------------------
# Test: Models must NOT import services or routes (Task 9)
# ---------------------------------------------------------------------------


class TestModelsDoNotImportUpward:
    """Model files must not depend on services or routes.

    WHY: Models are the bottom of the dependency graph. Importing
    services or routes would create circular dependencies and couple
    the data layer to application logic.

    HOW TO FIX a violation:
        1. If a model needs behaviour from a service, that logic belongs
           in the service, not the model.
        2. If a model needs a constant or type from routes, extract it
           into a shared module (e.g. config.py or a dedicated constants
           file).
    """

    def test_models_do_not_import_services(self):
        violations = []
        for filepath in _python_files(MODELS_DIR):
            rel = _relative_path(filepath)
            imports = _get_imports(filepath)
            service_imports = _imports_package(imports, "services")
            if service_imports:
                for imp in service_imports:
                    violations.append(
                        f"  - {rel}:{imp['lineno']}  " f"'from {imp['module']} import {', '.join(imp['names'])}'"
                    )
        if violations:
            msg = (
                "Models must not import from services/. "
                "Move the logic into the service layer instead.\n"
                "Violations found:\n" + "\n".join(violations)
            )
            pytest.fail(msg)

    def test_models_do_not_import_routes(self):
        violations = []
        for filepath in _python_files(MODELS_DIR):
            rel = _relative_path(filepath)
            imports = _get_imports(filepath)
            route_imports = _imports_package(imports, "routes")
            if route_imports:
                for imp in route_imports:
                    violations.append(
                        f"  - {rel}:{imp['lineno']}  " f"'from {imp['module']} import {', '.join(imp['names'])}'"
                    )
        if violations:
            msg = (
                "Models must not import from routes/. "
                "This would create a circular dependency.\n"
                "Violations found:\n" + "\n".join(violations)
            )
            pytest.fail(msg)


# ---------------------------------------------------------------------------
# Test: Services must NOT import routes (Task 9)
# ---------------------------------------------------------------------------


class TestServicesDoNotImportRoutes:
    """Service files must not depend on routes.

    WHY: Services sit below routes in the architecture. Importing routes
    would create a circular dependency and couple business logic to HTTP
    concerns.

    HOW TO FIX a violation:
        1. Extract the shared logic into a helper or utility module.
        2. If a service needs something currently in a route, move it
           to the service layer.
    """

    def test_services_do_not_import_routes(self):
        violations = []
        for filepath in _python_files(SERVICES_DIR):
            rel = _relative_path(filepath)
            imports = _get_imports(filepath)
            route_imports = _imports_package(imports, "routes")
            if route_imports:
                for imp in route_imports:
                    violations.append(
                        f"  - {rel}:{imp['lineno']}  " f"'from {imp['module']} import {', '.join(imp['names'])}'"
                    )
        if violations:
            msg = (
                "Services must not import from routes/. "
                "Extract shared logic into a utility module.\n"
                "Violations found:\n" + "\n".join(violations)
            )
            pytest.fail(msg)


# ---------------------------------------------------------------------------
# Test: No Anthropic API calls outside services/ (Task 10)
# ---------------------------------------------------------------------------


class TestAnthropicApiConfinedToServices:
    """The Anthropic SDK must only be imported inside services/.

    WHY: Centralising AI calls in the service layer makes them easier to
    mock in tests, swap providers, and manage API keys. Routes and models
    should never talk to external APIs directly.

    HOW TO FIX a violation:
        1. Create a new service (or extend an existing one) in services/.
        2. Move the Anthropic call there.
        3. Have the route/model call the service instead.
        4. Remove the file from _ANTHROPIC_OUTSIDE_SERVICES_ALLOWLIST.
    """

    def _find_anthropic_imports(self, directory: Path, exclude_dirs: set[str] | None = None) -> list[tuple[str, dict]]:
        """Find all files importing from 'anthropic' in the given directory."""
        violations = []
        exclude_dirs = exclude_dirs or set()
        for filepath in _python_files(directory):
            rel = _relative_path(filepath)
            # Skip excluded dirs (e.g. tests/, venv/)
            if any(rel.startswith(d) for d in exclude_dirs):
                continue
            # Skip services/ -- that's where Anthropic is allowed
            if rel.startswith("services/"):
                continue
            imports = _get_imports(filepath)
            anthropic_imports = _imports_package(imports, "anthropic")
            if anthropic_imports:
                violations.append((rel, anthropic_imports))
        return violations

    def _violating_files(self) -> list[tuple[str, list[dict]]]:
        """Return non-allowlisted files outside services/ that import anthropic."""
        all_violations = self._find_anthropic_imports(
            BACKEND_DIR,
            exclude_dirs={"tests/", "venv/", "evals/", "migrations/"},
        )
        return [(rel, imps) for rel, imps in all_violations if rel not in _ANTHROPIC_OUTSIDE_SERVICES_ALLOWLIST]

    def test_no_new_anthropic_imports_outside_services(self):
        """No file outside services/ (and outside the allowlist) may
        import the Anthropic SDK.

        If this test fails, a NEW file is importing Anthropic outside
        of services/. See the class docstring for how to fix it.
        """
        violations = self._violating_files()
        if violations:
            msg_parts = ["Anthropic API must only be used in services/. " "Violations found:"]
            for rel, imps in violations:
                for imp in imps:
                    msg_parts.append(
                        f"  - {rel}:{imp['lineno']}  " f"'from {imp['module']} import {', '.join(imp['names'])}'"
                    )
            msg_parts.append(
                "\nFIX: Move the Anthropic API call into a service in "
                "services/ and call it from the route/module instead."
            )
            pytest.fail("\n".join(msg_parts))

    @pytest.mark.xfail(
        reason="Known tech debt: routes/applications/ats.py uses Anthropic " "directly. TODO: move to a service.",
        strict=True,
    )
    def test_all_anthropic_violations_are_tracked(self):
        """Ensure allowlist covers all current violations."""
        all_violations = self._find_anthropic_imports(
            BACKEND_DIR,
            exclude_dirs={"tests/", "venv/", "evals/", "migrations/"},
        )
        assert not all_violations, (
            "All Anthropic-outside-services violations should have been "
            "resolved. Remove this xfail marker and the allowlist."
        )

    def test_anthropic_allowlist_has_no_stale_entries(self):
        """Allowlist entries must correspond to actual violations."""
        all_violations_rels = {
            rel
            for rel, _ in self._find_anthropic_imports(
                BACKEND_DIR,
                exclude_dirs={"tests/", "venv/", "evals/", "migrations/"},
            )
        }
        stale = _ANTHROPIC_OUTSIDE_SERVICES_ALLOWLIST - all_violations_rels
        if stale:
            pytest.fail(
                "These files are in the Anthropic allowlist but no longer "
                "import anthropic. Remove them from "
                "_ANTHROPIC_OUTSIDE_SERVICES_ALLOWLIST in test_architecture.py:\n"
                f"  {', '.join(sorted(stale))}"
            )


# ---------------------------------------------------------------------------
# Test: File size limits (Task 10)
# ---------------------------------------------------------------------------

MAX_LINES = 500


class TestFileSizeLimits:
    """No single Python file should exceed MAX_LINES lines.

    WHY: Large files are hard to review, hard to test, and tend to
    accumulate mixed concerns. Keeping files short encourages proper
    separation of concerns.

    HOW TO FIX a violation:
        1. Identify distinct responsibilities in the large file.
        2. Extract them into separate modules.
        3. Import and compose the pieces where needed.
        4. Remove the file from _FILE_SIZE_ALLOWLIST in this test.
    """

    def _oversized_files(self) -> list[tuple[str, int]]:
        """Return (rel_path, line_count) for files exceeding MAX_LINES."""
        results = []
        for filepath in _python_files(BACKEND_DIR):
            rel = _relative_path(filepath)
            if rel.startswith(("venv/", "migrations/", "migrations_legacy/")) or rel == "tests/test_architecture.py":
                continue
            try:
                line_count = len(filepath.read_text(encoding="utf-8").splitlines())
            except (OSError, UnicodeDecodeError):
                continue
            if line_count > MAX_LINES:
                results.append((rel, line_count))
        return results

    def test_no_new_file_exceeds_line_limit(self):
        """No file (outside the allowlist) may exceed the line limit.

        If this test fails, a NEW file has grown beyond the limit.
        See the class docstring for how to fix it.
        """
        violations = [(rel, count) for rel, count in self._oversized_files() if rel not in _FILE_SIZE_ALLOWLIST]

        if violations:
            violations.sort(key=lambda x: -x[1])
            msg_parts = [f"Python files must not exceed {MAX_LINES} lines. " "Violations found:"]
            for rel, count in violations:
                msg_parts.append(f"  - {rel}: {count} lines")
            msg_parts.append(
                "\nFIX: Split large files into smaller, focused modules. "
                "Extract distinct responsibilities into separate files."
            )
            pytest.fail("\n".join(msg_parts))

    @pytest.mark.xfail(
        reason="Known tech debt: several files exceed the line limit. " "TODO: split into smaller modules.",
        strict=True,
    )
    def test_all_oversized_files_are_tracked(self):
        """Ensure the allowlist covers all current oversized files."""
        all_oversized = self._oversized_files()
        assert not all_oversized, (
            "All oversized file violations should have been resolved. " "Remove this xfail marker and the allowlist."
        )

    def test_file_size_allowlist_has_no_stale_entries(self):
        """Allowlist entries must correspond to actual violations."""
        actual_oversized = {rel for rel, _ in self._oversized_files()}
        stale = _FILE_SIZE_ALLOWLIST - actual_oversized
        if stale:
            pytest.fail(
                "These files are in the file-size allowlist but no longer "
                "exceed the limit. Remove them from _FILE_SIZE_ALLOWLIST "
                f"in test_architecture.py:\n  {', '.join(sorted(stale))}"
            )
