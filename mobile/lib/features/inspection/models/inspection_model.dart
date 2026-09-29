class InspectionModel {
  final String id;
  final String inspectionCode;
  final String lotId;
  final String inspectorId;
  final int sampleSize;
  final String status;
  final int totalOnionsEvaluated;
  final int gradeACount;
  final double gradeAPercentage;
  final int ursCount;
  final double ursPercentage;
  final int rejectCount;
  final double rejectPercentage;
  final int manualReviewCount;
  final String? lotDecision;
  final String? decisionReason;
  final DateTime? finalizedAt;
  final DateTime createdAt;

  InspectionModel({
    required this.id,
    required this.inspectionCode,
    required this.lotId,
    required this.inspectorId,
    required this.sampleSize,
    required this.status,
    this.totalOnionsEvaluated = 0,
    this.gradeACount = 0,
    this.gradeAPercentage = 0.0,
    this.ursCount = 0,
    this.ursPercentage = 0.0,
    this.rejectCount = 0,
    this.rejectPercentage = 0.0,
    this.manualReviewCount = 0,
    this.lotDecision,
    this.decisionReason,
    this.finalizedAt,
    required this.createdAt,
  });

  factory InspectionModel.fromJson(Map<String, dynamic> json) {
    return InspectionModel(
      id: json['id'] as String,
      inspectionCode: json['inspection_code'] as String,
      lotId: json['lot_id'] as String,
      inspectorId: json['inspector_id'] as String,
      sampleSize: json['sample_size'] as int? ?? 50,
      status: json['status'] as String? ?? 'CAPTURING',
      totalOnionsEvaluated: json['total_onions_evaluated'] as int? ?? 0,
      gradeACount: json['grade_a_count'] as int? ?? 0,
      gradeAPercentage: (json['grade_a_percentage'] as num?)?.toDouble() ?? 0.0,
      ursCount: json['urs_count'] as int? ?? 0,
      ursPercentage: (json['urs_percentage'] as num?)?.toDouble() ?? 0.0,
      rejectCount: json['reject_count'] as int? ?? 0,
      rejectPercentage: (json['reject_percentage'] as num?)?.toDouble() ?? 0.0,
      manualReviewCount: json['manual_review_count'] as int? ?? 0,
      lotDecision: json['lot_decision'] as String?,
      decisionReason: json['decision_reason'] as String?,
      finalizedAt: json['finalized_at'] != null ? DateTime.parse(json['finalized_at'] as String) : null,
      createdAt: json['created_at'] != null ? DateTime.parse(json['created_at'] as String) : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'inspection_code': inspectionCode,
        'lot_id': lotId,
        'inspector_id': inspectorId,
        'sample_size': sampleSize,
        'status': status,
        'total_onions_evaluated': totalOnionsEvaluated,
        'grade_a_count': gradeACount,
        'grade_a_percentage': gradeAPercentage,
        'urs_count': ursCount,
        'urs_percentage': ursPercentage,
        'reject_count': rejectCount,
        'reject_percentage': rejectPercentage,
        'manual_review_count': manualReviewCount,
        'lot_decision': lotDecision,
        'decision_reason': decisionReason,
        'finalized_at': finalizedAt?.toIso8601String(),
        'created_at': createdAt.toIso8601String(),
      };
}

class InspectionImageModel {
  final String id;
  final String inspectionId;
  final String storageKey;
  final String filename;
  final String qualityStatus;
  final double? blurVariance;
  final double? meanBrightness;
  final bool calibrationDetected;
  final double? pixelsPerMm;

  InspectionImageModel({
    required this.id,
    required this.inspectionId,
    required this.storageKey,
    required this.filename,
    required this.qualityStatus,
    this.blurVariance,
    this.meanBrightness,
    required this.calibrationDetected,
    this.pixelsPerMm,
  });

  factory InspectionImageModel.fromJson(Map<String, dynamic> json) => InspectionImageModel(
        id: json['id'] as String,
        inspectionId: json['inspection_id'] as String,
        storageKey: json['storage_key'] as String,
        filename: json['filename'] as String? ?? "capture.jpg",
        qualityStatus: json['quality_status'] as String? ?? "PASSED",
        blurVariance: (json['blur_variance'] as num?)?.toDouble(),
        meanBrightness: (json['mean_brightness'] as num?)?.toDouble(),
        calibrationDetected: json['calibration_detected'] as bool? ?? false,
        pixelsPerMm: (json['pixels_per_mm'] as num?)?.toDouble(),
      );
}

class GradeResultModel {
  final String id;
  final String inspectionId;
  final String? detectionId;
  final String grade;
  final List<String> reasonCodes;
  final double confidence;
  final bool requiresReview;
  final String? defectClass;
  final double? diameterMm;

  GradeResultModel({
    required this.id,
    required this.inspectionId,
    this.detectionId,
    required this.grade,
    required this.reasonCodes,
    required this.confidence,
    this.requiresReview = false,
    this.defectClass,
    this.diameterMm,
  });

  factory GradeResultModel.fromJson(Map<String, dynamic> json) => GradeResultModel(
        id: json['id'] as String,
        inspectionId: json['inspection_id'] as String,
        detectionId: json['detection_id'] as String?,
        grade: json['grade'] as String,
        reasonCodes: (json['reason_codes'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
        confidence: (json['confidence'] as num).toDouble(),
        requiresReview: json['requires_review'] as bool? ?? false,
        defectClass: json['defect_class'] as String?,
        diameterMm: (json['diameter_mm'] as num?)?.toDouble(),
      );
}

class ReportModel {
  final String id;
  final String reportCode;
  final String inspectionId;
  final String qrVerificationHash;
  final Map<String, dynamic> summaryMetrics;
  final bool isFinalized;
  final DateTime generatedAt;

  ReportModel({
    required this.id,
    required this.reportCode,
    required this.inspectionId,
    required this.qrVerificationHash,
    required this.summaryMetrics,
    required this.isFinalized,
    required this.generatedAt,
  });

  factory ReportModel.fromJson(Map<String, dynamic> json) => ReportModel(
        id: json['id'] as String,
        reportCode: json['report_code'] as String,
        inspectionId: json['inspection_id'] as String,
        qrVerificationHash: json['qr_verification_hash'] as String,
        summaryMetrics: Map<String, dynamic>.from(json['summary_metrics'] as Map? ?? {}),
        isFinalized: json['is_finalized'] as bool? ?? true,
        generatedAt: DateTime.parse(json['generated_at'] as String),
      );
}
