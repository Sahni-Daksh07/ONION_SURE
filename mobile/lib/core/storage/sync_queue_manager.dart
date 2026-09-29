import 'package:flutter/foundation.dart';
import 'package:uuid/uuid.dart';
import '../network/api_client.dart';
import '../constants/api_constants.dart';
import 'local_storage.dart';

enum SyncStatus { pending, syncing, synced, failed }

class SyncItem {
  final String id;
  final String syncKey;
  final String entityType;
  final Map<String, dynamic> payload;
  SyncStatus status;
  String? errorMessage;
  final DateTime createdAt;

  SyncItem({
    required this.id,
    required this.syncKey,
    required this.entityType,
    required this.payload,
    this.status = SyncStatus.pending,
    this.errorMessage,
    required this.createdAt,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'sync_key': syncKey,
        'entity_type': entityType,
        'payload': payload,
        'status': status.name,
        'error_message': errorMessage,
        'created_at': createdAt.toIso8601String(),
      };

  factory SyncItem.fromJson(Map<String, dynamic> json) => SyncItem(
        id: json['id'] as String,
        syncKey: json['sync_key'] as String,
        entityType: json['entity_type'] as String,
        payload: Map<String, dynamic>.from(json['payload'] as Map),
        status: SyncStatus.values.firstWhere(
          (s) => s.name == json['status'],
          orElse: () => SyncStatus.pending,
        ),
        errorMessage: json['error_message'] as String?,
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
  int get pendingCount => _queue.where((i) => i.status == SyncStatus.pending || i.status == SyncStatus.failed).length;
  bool get isSyncing => _isSyncing;

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
    required Map<String, dynamic> payload,
  }) async {
    final uuid = const Uuid();
    final item = SyncItem(
      id: uuid.v4(),
      syncKey: "sync_${uuid.v4()}",
      entityType: entityType,
      payload: payload,
      createdAt: DateTime.now().toUtc(),
    );
    _queue.add(item);
    await _persistQueue();
    notifyListeners();
    return item;
  }

  Future<bool> syncPendingBatch() async {
    if (_isSyncing) return false;
    final pendingItems = _queue.where((i) => i.status == SyncStatus.pending || i.status == SyncStatus.failed).toList();
    if (pendingItems.isEmpty) return true;

    _isSyncing = true;
    notifyListeners();

    try {
      final apiClient = ApiClient();
      final batchPayload = {
        'client_id': _clientId,
        'items': pendingItems.map((item) => {
              'sync_key': item.syncKey,
              'entity_type': item.entityType,
              'action': 'CREATE',
              'payload': item.payload,
            }).toList(),
      };

      for (var item in pendingItems) {
        item.status = SyncStatus.syncing;
      }
      notifyListeners();

      final response = await apiClient.post(ApiConstants.syncBatch, body: batchPayload);

      if (response is Map && response.containsKey('processed_count')) {
        for (var item in pendingItems) {
          item.status = SyncStatus.synced;
        }
      } else {
        for (var item in pendingItems) {
          item.status = SyncStatus.failed;
          item.errorMessage = "Invalid batch response";
        }
      }
    } catch (e) {
      for (var item in pendingItems) {
        item.status = SyncStatus.failed;
        item.errorMessage = e.toString();
      }
    } finally {
      _isSyncing = false;
      await _persistQueue();
      notifyListeners();
    }

    return pendingItems.every((i) => i.status == SyncStatus.synced);
  }

  Future<void> clearSynced() async {
    _queue.removeWhere((i) => i.status == SyncStatus.synced);
    await _persistQueue();
    notifyListeners();
  }
}
