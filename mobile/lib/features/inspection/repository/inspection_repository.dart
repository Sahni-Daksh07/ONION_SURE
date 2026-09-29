import 'package:flutter/foundation.dart';
import 'package:uuid/uuid.dart';
import '../../../core/network/api_client.dart';
import '../../../core/constants/api_constants.dart';
import '../../../core/storage/local_storage.dart';
import '../../../core/storage/sync_queue_manager.dart';
import '../../../core/network/api_exceptions.dart';
import '../models/inspection_model.dart';

class InspectionRepository extends ChangeNotifier {
  final ApiClient _apiClient = ApiClient();
  final LocalStorage _localStorage = LocalStorage();
  final SyncQueueManager _syncManager = SyncQueueManager();

  List<InspectionModel> _inspections = [];
  InspectionModel? _activeInspection;
  List<InspectionImageModel> _activeImages = [];
  List<GradeResultModel> _activeGradeResults = [];
  ReportModel? _latestReport;
  bool _isLoading = false;
  String? _errorMessage;

  List<InspectionModel> get inspections => List.unmodifiable(_inspections);
  InspectionModel? get activeInspection => _activeInspection;
  List<InspectionImageModel> get activeImages => List.unmodifiable(_activeImages);
  List<GradeResultModel> get activeGradeResults => List.unmodifiable(_activeGradeResults);
  ReportModel? get latestReport => _latestReport;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  Future<void> fetchInspections({String? lotId, String? status}) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final query = <String, dynamic>{'page': 1, 'page_size': 50};
      if (lotId != null) query['lot_id'] = lotId;
      if (status != null) query['status'] = status;

      final res = await _apiClient.get(ApiConstants.inspections, queryParams: query);
      if (res is Map && res.containsKey('items')) {
        final items = (res['items'] as List)
            .map((item) => InspectionModel.fromJson(Map<String, dynamic>.from(item as Map)))
            .toList();
        _inspections = items;
        await _localStorage.cacheInspections(_inspections.map((i) => i.toJson()).toList());
      }
    } on NetworkException {
      final cached = _localStorage.getCachedInspections();
      if (cached.isNotEmpty) {
        _inspections = cached.map((c) => InspectionModel.fromJson(c)).toList();
      } else {
        _errorMessage = "Offline mode: No cached inspections available.";
      }
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<InspectionModel> createInspection({
    required String lotId,
    required String inspectorId,
    required int sampleSize,
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    final payload = {
      'lot_id': lotId,
      'inspector_id': inspectorId,
      'sample_size': sampleSize,
    };

    try {
      final res = await _apiClient.post(ApiConstants.inspections, body: payload);
      final newInsp = InspectionModel.fromJson(Map<String, dynamic>.from(res as Map));
      _activeInspection = newInsp;
      _inspections.insert(0, newInsp);
      _activeImages = [];
      _activeGradeResults = [];
      _latestReport = null;
      await _localStorage.cacheInspections(_inspections.map((i) => i.toJson()).toList());
      return newInsp;
    } on NetworkException {
      final localId = const Uuid().v4();
      final offlinePayload = Map<String, dynamic>.from(payload)
        ..['id'] = localId
        ..['inspection_code'] = "INSP-OFFLINE-${localId.substring(0, 8).toUpperCase()}"
        ..['status'] = 'CAPTURING'
        ..['created_at'] = DateTime.now().toUtc().toIso8601String();
      final localInsp = InspectionModel.fromJson(offlinePayload);
      _activeInspection = localInsp;
      _inspections.insert(0, localInsp);
      _activeImages = [];
      _activeGradeResults = [];
      _latestReport = null;
      await _localStorage.cacheInspections(_inspections.map((i) => i.toJson()).toList());

      await _syncManager.enqueue(
        entityType: 'Inspection',
        payload: payload,
      );
      return localInsp;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<InspectionImageModel> uploadCapturedImage({
    required String inspectionId,
    required List<int> imageBytes,
    required String filename,
    required bool calibrationDetected,
    required double pixelsPerMm,
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final res = await _apiClient.uploadMultipart(
        ApiConstants.uploadImage(inspectionId),
        fileBytes: imageBytes,
        filename: filename,
        fields: {
          'calibration_detected': calibrationDetected.toString(),
          'pixels_per_mm': pixelsPerMm.toString(),
          'calibration_method': 'ARUCO_4X4_50',
        },
      );

      final imageModel = InspectionImageModel.fromJson(Map<String, dynamic>.from(res as Map));
      _activeImages.add(imageModel);
      return imageModel;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<List<GradeResultModel>> gradeInspectionObservations({
    required String inspectionId,
    required List<Map<String, dynamic>> observations,
    String policyVersion = "1.0.0",
    String modelVersion = "classifier-v1.0.0",
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    final payload = {
      'inspection_id': inspectionId,
      'policy_version': policyVersion,
      'model_version': modelVersion,
      'observations': observations,
    };

    try {
      final res = await _apiClient.post(
        ApiConstants.gradeInspection(inspectionId),
        body: payload,
      );

      if (res is List) {
        _activeGradeResults = res
            .map((item) => GradeResultModel.fromJson(Map<String, dynamic>.from(item as Map)))
            .toList();
      }

      // Refresh inspection state
      final updatedInspRes = await _apiClient.get("${ApiConstants.inspections}/$inspectionId");
      if (updatedInspRes is Map<String, dynamic>) {
        _activeInspection = InspectionModel.fromJson(updatedInspRes);
        final index = _inspections.indexWhere((i) => i.id == inspectionId);
        if (index != -1) {
          _inspections[index] = _activeInspection!;
          await _localStorage.cacheInspections(_inspections.map((i) => i.toJson()).toList());
        }
      }

      return _activeGradeResults;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> submitManualReview({
    required String inspectionId,
    required String gradeResultId,
    required String reviewerId,
    required String reviewedGrade,
    required String reason,
    String? comments,
  }) async {
    final payload = {
      'grade_result_id': gradeResultId,
      'reviewer_id': reviewerId,
      'reviewed_grade': reviewedGrade,
      'reason': reason,
      'comments': comments,
    };

    await _apiClient.post(
      ApiConstants.manualReview(inspectionId),
      body: payload,
    );

    // Refresh inspection results
    final updatedInspRes = await _apiClient.get("${ApiConstants.inspections}/$inspectionId");
    if (updatedInspRes is Map<String, dynamic>) {
      _activeInspection = InspectionModel.fromJson(updatedInspRes);
    }
    notifyListeners();
  }

  Future<ReportModel> finalizeInspection(String inspectionId, {String? actorId}) async {
    _isLoading = true;
    notifyListeners();

    try {
      final res = await _apiClient.post(
        ApiConstants.finalizeInspection(inspectionId),
        queryParams: actorId != null ? {'actor_id': actorId} : null,
      );

      final report = ReportModel.fromJson(Map<String, dynamic>.from(res as Map));
      _latestReport = report;

      // Refresh active inspection
      final updatedInspRes = await _apiClient.get("${ApiConstants.inspections}/$inspectionId");
      if (updatedInspRes is Map<String, dynamic>) {
        _activeInspection = InspectionModel.fromJson(updatedInspRes);
        final index = _inspections.indexWhere((i) => i.id == inspectionId);
        if (index != -1) {
          _inspections[index] = _activeInspection!;
          await _localStorage.cacheInspections(_inspections.map((i) => i.toJson()).toList());
        }
      }

      return report;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<Map<String, dynamic>> verifyReportQr(String qrHash) async {
    final res = await _apiClient.get(ApiConstants.verifyReport(qrHash));
    return Map<String, dynamic>.from(res as Map);
  }
}
