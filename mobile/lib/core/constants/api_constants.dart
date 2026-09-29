class ApiConstants {
  // Default development URL (use 10.0.2.2 for Android Emulator, or 127.0.0.1 for local desktop/web)
  static const String defaultBaseUrl = "http://10.0.2.2:8000";
  static const String apiVersion = "/api/v1";

  // Auth Endpoints
  static const String login = "$apiVersion/auth/login";
  static const String register = "$apiVersion/auth/register";
  static const String refresh = "$apiVersion/auth/refresh";
  static const String me = "$apiVersion/auth/me";

  // Core Master Data
  static const String farmers = "$apiVersion/farmers";
  static const String procurementCentres = "$apiVersion/procurement-centres";
  static const String lots = "$apiVersion/lots";

  // Inspection & Vision Pipeline
  static const String inspections = "$apiVersion/inspections";
  static String uploadImage(String inspectionId) => "$inspections/$inspectionId/upload-image";
  static String gradeInspection(String inspectionId) => "$inspections/$inspectionId/grade";
  static String finalizeInspection(String inspectionId) => "$inspections/$inspectionId/finalize";
  static String manualReview(String inspectionId) => "$inspections/$inspectionId/manual-review";
  static String inspectionImages(String inspectionId) => "$inspections/$inspectionId/images";
  static String inspectionDetections(String inspectionId) => "$inspections/$inspectionId/detections";

  // Reports & Verification
  static const String reports = "$apiVersion/reports";
  static String verifyReport(String qrHash) => "$apiVersion/reports/verify/$qrHash";

  // Offline Synchronization
  static const String syncBatch = "$apiVersion/sync/batch";
  static String syncStatus(String clientId) => "$apiVersion/sync/status/$clientId";
}
