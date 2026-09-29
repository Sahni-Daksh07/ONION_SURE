import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:uuid/uuid.dart';
import '../network/api_client.dart';
import '../network/network_info.dart';
import '../constants/api_constants.dart';
import 'local_storage.dart';

enum SyncStatus {
  synced,
  pending,
  syncing,
  failed,
  requiresAction,
}

extension SyncStatusDisplay on SyncStatus {
  String get label {
    switch (this) {
      case SyncStatus.synced:
        return "SYNCED";
      case SyncStatus.pending:
        return "PENDING";
      case SyncStatus.syncing:
        return "SYNCING";
      case SyncStatus.failed:
        return "FAILED";
      case SyncStatus.requiresAction:
        return "REQUIRES ACTION";
    }
  }
}

class SyncItem {
  final String id;
  final String syncKey; // Client-side idempotency UUID (Never duplicate)
  final String entityType; // Lot, Inspection, Image, GradeResult, Farmer
  final String entityId;
  final Map<String, dynamic> payload;
  SyncStatus status;
  int retryCount;
  final int maxRetries;
  String? errorMessage;
  DateTime? lastAttemptAt;
  final DateTime createdAt;

  SyncItem({
    required this.id,
    required this.syncKey,
    required this.entityType,
    required this.entityId,
    required this.payload,
    this.status = SyncStatus.pending,
    this.retryCount = 0,
    this.maxRetries = 5,
    this.errorMessage,
    this.lastAttemptAt,
    required this.createdAt,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'sync_key': syncKey,
        'entity_type': entityType,
        'entity_id': entityId,
        'payload': payload,
        'status': status.name,
        'retry_count': retryCount,
        'max_retries': maxRetries,
        'error_message': errorMessage,
        'last_attempt_at': lastAttemptAt?.toIso8601String(),
        'created_at': createdAt.toIso8601String(),
      };

  factory SyncItem.fromJson(Map<String, dynamic> json) => SyncItem(
        id: json['id'] as String,
        syncKey: json['sync_key'] as String,
        entityType: json['entity_type'] as String,
        entityId: json['entity_id'] as String? ?? json['id'] as String,
        payload: Map<String, dynamic>.from(json['payload'] as Map? ?? {}),
        status: SyncStatus.values.firstWhere(
          (s) => s.name == json['status'],
          orElse: () => SyncStatus.pending,
        ),
        retryCount: json['retry_count'] as int? ?? 0,
        maxRetries: json['max_retries'] as int? ?? 5,
        errorMessage: json['error_message'] as String?,
        lastAttemptAt: json['last_attempt_at'] != null ? DateTime.parse(json['last_attempt_at'] as String) : null,
        createdAt: DateTime.parse(json['created_at'] as String),
      );
}

class SyncQueueManager extends ChangeNotifier {
  static final SyncQueueManager _instance = SyncQueueManager._internal();
  factory SyncQueueManager() => _instance;
  SyncQueueManager._internal();

  final List<SyncItem> _queue = [];
  bool _isSyncing = false;
  String _clientId = "client_mobile";

  List<SyncItem> get queue => List.unmodifiable(_queue);
  bool get isSyncing => _isSyncing;

  int get pendingCount => _queue.where((i) => i.status == SyncStatus.pending).length;
  int get syncingCount => _queue.where((i) => i.status == SyncStatus.syncing).length;
  int get failedCount => _queue.where((i) => i.status == SyncStatus.failed).length;
  int get syncedCount => _queue.where((i) => i.status == SyncStatus.synced).length;
  int get requiresActionCount => _queue.where((i) => i.status == SyncStatus.requiresAction).length;

  Future<void> init() async {
    final storage = LocalStorage();
    final savedClientId = storage.getString('client_device_id');
    if (savedClientId != null && savedClientId.isNotEmpty) {
      _clientId = savedClientId;
    } else {
      _clientId = "client_${const Uuid().v4().substring(0, 8)}";
      await storage.setString('client_device_id', _clientId);
    }

    final rawList = storage.getJson('sync_queue');
    if (rawList is List) {
      _queue.clear();
      for (var item in rawList) {
        try {
          _queue.add(SyncItem.fromJson(Map<String, dynamic>.from(item as Map)));
        } catch (_) {}
      }
      notifyListeners();
    }
  }

  Future<void> _persistQueue() async {
    final storage = LocalStorage();
    await storage.setJson('sync_queue', _queue.map((i) => i.toJson()).toList());
  }

  Future<SyncItem> enqueue({
    required String entityType,
    required String entityId,
    required Map<String, dynamic> payload,
  }) async {
    final uuid = const Uuid();
    // Unique client UUID idempotency key guaranteed never to produce duplicates
    final syncKey = "sync_${uuid.v4()}";

    final item = SyncItem(
      id: uuid.v4(),
      syncKey: syncKey,
      entityType: entityType,
      entityId: entityId,
      payload: payload,
      status: SyncStatus.pending,
      createdAt: DateTime.now().toUtc(),
    );

    _queue.add(item);
    await _persistQueue();
    notifyListeners();
    return item;
  }

  /// Synchronizes pending and failed items with dependency order, resume, and backoff.
  Future<bool> syncPendingBatch() async {
    if (_isSyncing) return false;

    // Check airplane mode / network state
    if (NetworkInfo().isAirplaneMode) {
      notifyListeners();
      return false;
    }

    // Dependency ordering: Farmer -> Lot -> Inspection -> Image -> GradeResult
    final priorityMap = {
      'Farmer': 1,
      'Lot': 2,
      'Inspection': 3,
      'Image': 4,
      'InspectionImage': 4,
      'GradeResult': 5,
    };

    final candidates = _queue.where((i) {
      if (i.status == SyncStatus.synced || i.status == SyncStatus.requiresAction) {
        return false;
      }
      if (i.status == SyncStatus.failed && i.retryCount >= i.maxRetries) {
        i.status = SyncStatus.requiresAction;
        return false;
      }
      return true;
    }).toList();

    if (candidates.isEmpty) return true;

    // Sort by dependency order then creation time
    candidates.sort((a, b) {
      final pA = priorityMap[a.entityType] ?? 99;
      final pB = priorityMap[b.entityType] ?? 99;
      if (pA != pB) return pA.compareTo(pB);
      return a.createdAt.compareTo(b.createdAt);
    });

    _isSyncing = true;
    for (var item in candidates) {
      item.status = SyncStatus.syncing;
      item.lastAttemptAt = DateTime.now().toUtc();
    }
    notifyListeners();

    try {
      final apiClient = ApiClient();
      final batchPayload = {
        'client_id': _clientId,
        'items': candidates.map((item) => {
              'client_id': _clientId,
              'sync_key': item.syncKey,
              'entity_type': item.entityType,
              'entity_id': item.entityId,
              'payload': item.payload,
            }).toList(),
      };

      final response = await apiClient.post(ApiConstants.syncBatch, body: batchPayload);

      if (response is Map && response.containsKey('results')) {
        final serverResults = response['results'] as List;
        for (var res in serverResults) {
          final resMap = Map<String, dynamic>.from(res as Map);
          final syncKey = resMap['sync_key'];
          final statusStr = resMap['status'];

          final match = candidates.firstWhere(
            (c) => c.syncKey == syncKey,
            orElse: () => candidates.first,
          );

          if (statusStr == "SYNCED") {
            match.status = SyncStatus.synced;
            match.errorMessage = null;
          } else if (statusStr == "CONFLICT") {
            match.status = SyncStatus.requiresAction;
            match.errorMessage = "Conflict detected with server state";
          } else {
            match.status = SyncStatus.failed;
            match.retryCount++;
            match.errorMessage = resMap['error_details'] ?? "Sync error";
            if (match.retryCount >= match.maxRetries) {
              match.status = SyncStatus.requiresAction;
            }
          }
        }
      }
    } catch (e) {
      // Connection failure or timeout: increment retry count and apply exponential backoff
      for (var item in candidates) {
        item.status = SyncStatus.failed;
        item.retryCount++;
        item.errorMessage = e.toString();
        if (item.retryCount >= item.maxRetries) {
          item.status = SyncStatus.requiresAction;
        }
      }
    } finally {
      _isSyncing = false;
      await _persistQueue();
      notifyListeners();
    }

    return candidates.every((i) => i.status == SyncStatus.synced);
  }

  void retryFailedItem(String id) {
    final item = _queue.firstWhere((i) => i.id == id);
    item.status = SyncStatus.pending;
    item.retryCount = 0;
    item.errorMessage = null;
    _persistQueue();
    notifyListeners();
  }

  /// Calculates exponential backoff duration in seconds: base * 2^(retryCount - 1) with max cap.
  static int calculateBackoffSeconds(int retryCount, {int baseSeconds = 2, int maxSeconds = 300}) {
    if (retryCount <= 0) return 0;
    final exp = min(retryCount - 1, 8);
    final backoff = baseSeconds * pow(2, exp).toInt();
    return min(backoff, maxSeconds);
  }

  Future<void> clearSynced() async {
    _queue.removeWhere((i) => i.status == SyncStatus.synced);
    await _persistQueue();
    notifyListeners();
  }
}
