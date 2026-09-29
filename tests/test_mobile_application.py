"""
Mobile Application Architecture and Screen Completeness Test Suite
Smart India Hackathon 2026 - Problem Statement PS26031
"""

import os
from pathlib import Path
import pytest

MOBILE_ROOT = Path("mobile")
LIB_DIR = MOBILE_ROOT / "lib"
FEATURES_DIR = LIB_DIR / "features"


def test_mobile_directory_structure():
    """Verify clean architecture folder layout for the Flutter app."""
    assert MOBILE_ROOT.exists(), "Mobile directory does not exist."
    assert (MOBILE_ROOT / "pubspec.yaml").exists(), "pubspec.yaml missing."
    assert (MOBILE_ROOT / "analysis_options.yaml").exists(), "analysis_options.yaml missing."
    assert (LIB_DIR / "main.dart").exists(), "main.dart entrypoint missing."
    assert (LIB_DIR / "app.dart").exists(), "app.dart missing."

    core_dirs = ["constants", "network", "storage", "theme", "widgets"]
    for cd in core_dirs:
        assert (LIB_DIR / "core" / cd).is_dir(), f"Core sub-package {cd} missing."


def test_required_18_screens_exist():
    """
    Verify all 18 required screens exist with valid dart files:
    1. Splash
    2. Login
    3. Dashboard
    4. Farmer list/profile
    5. Procurement centre
    6. Create lot
    7. Create inspection
    8. Sampling
    9. Camera
    10. Image quality feedback
    11. AI processing
    12. Onion-level results
    13. Lot-level results
    14. Manual review
    15. Inspection history
    16. Report
    17. QR verification
    18. Settings
    """
    expected_screens = {
        "1. Splash": FEATURES_DIR / "splash" / "presentation" / "splash_screen.dart",
        "2. Login": FEATURES_DIR / "auth" / "presentation" / "login_screen.dart",
        "3. Dashboard": FEATURES_DIR / "dashboard" / "presentation" / "dashboard_screen.dart",
        "4. Farmer list": FEATURES_DIR / "farmer" / "presentation" / "farmer_list_screen.dart",
        "5. Procurement centre": FEATURES_DIR / "procurement_centre" / "presentation" / "procurement_centre_screen.dart",
        "6. Create lot": FEATURES_DIR / "lot" / "presentation" / "create_lot_screen.dart",
        "7. Create inspection": FEATURES_DIR / "inspection" / "presentation" / "create_inspection_screen.dart",
        "8. Sampling": FEATURES_DIR / "inspection" / "presentation" / "sampling_guidance_screen.dart",
        "9. Camera": FEATURES_DIR / "inspection" / "presentation" / "camera_capture_screen.dart",
        "10. Image quality feedback": FEATURES_DIR / "inspection" / "presentation" / "image_quality_screen.dart",
        "11. AI processing": FEATURES_DIR / "inspection" / "presentation" / "ai_processing_screen.dart",
        "12. Onion-level results": FEATURES_DIR / "inspection" / "presentation" / "onion_results_screen.dart",
        "13. Lot-level results": FEATURES_DIR / "inspection" / "presentation" / "lot_results_screen.dart",
        "14. Manual review": FEATURES_DIR / "manual_review" / "presentation" / "manual_review_screen.dart",
        "15. Inspection history": FEATURES_DIR / "history" / "presentation" / "inspection_history_screen.dart",
        "16. Report": FEATURES_DIR / "reports" / "presentation" / "report_screen.dart",
        "17. QR verification": FEATURES_DIR / "qr_verification" / "presentation" / "qr_verification_screen.dart",
        "18. Settings": FEATURES_DIR / "settings" / "presentation" / "settings_screen.dart",
    }

    for screen_name, file_path in expected_screens.items():
        assert file_path.exists(), f"Screen '{screen_name}' file missing at {file_path}"
        content = file_path.read_text(encoding="utf-8")
        assert len(content) > 100, f"Screen '{screen_name}' file is unexpectedly empty."


def test_app_router_covers_all_screens():
    """Verify that lib/app.dart declares all routes corresponding to the required screens."""
    app_dart = (LIB_DIR / "app.dart").read_text(encoding="utf-8")
    expected_routes = [
        "'/'",
        "'/login'",
        "'/dashboard'",
        "'/farmers'",
        "'/procurement_centres'",
        "'/create_lot'",
        "'/create_inspection'",
        "'/sampling'",
        "'/camera'",
        "'/image_quality'",
        "'/ai_processing'",
        "'/onion_results'",
        "'/lot_results'",
        "'/manual_review'",
        "'/history'",
        "'/report'",
        "'/qr_verification'",
        "'/settings'",
    ]

    for route in expected_routes:
        assert route in app_dart, f"Route {route} not registered in lib/app.dart"


def test_api_constants_match_backend_contract():
    """Verify that ApiConstants in Flutter aligns with FastAPI backend endpoints."""
    constants_file = LIB_DIR / "core" / "constants" / "api_constants.dart"
    assert constants_file.exists(), "api_constants.dart does not exist."
    content = constants_file.read_text(encoding="utf-8")

    assert 'apiVersion = "/api/v1"' in content
    assert '/auth/login' in content
    assert '/farmers' in content
    assert '/procurement-centres' in content
    assert '/lots' in content
    assert '/inspections' in content
    assert '/reports' in content
    assert '/sync/batch' in content


def test_offline_sync_queue_manager_implementation():
    """Verify offline sync queue implementation satisfies idempotency and state machine requirements."""
    sync_file = LIB_DIR / "core" / "storage" / "sync_queue_manager.dart"
    assert sync_file.exists(), "sync_queue_manager.dart missing."
    content = sync_file.read_text(encoding="utf-8")

    assert "enum SyncStatus" in content
    assert "syncKey" in content or "sync_key" in content
    assert "syncPendingBatch" in content
    assert "enqueue" in content


def test_android_manifest_permissions():
    """Verify AndroidManifest.xml includes required permissions for mandi field operations."""
    manifest_file = MOBILE_ROOT / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
    assert manifest_file.exists(), "AndroidManifest.xml missing."
    content = manifest_file.read_text(encoding="utf-8")

    assert "android.permission.CAMERA" in content
    assert "android.permission.INTERNET" in content
    assert "android.permission.ACCESS_NETWORK_STATE" in content
