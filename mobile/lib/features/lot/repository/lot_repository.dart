import 'package:flutter/foundation.dart';
import 'package:uuid/uuid.dart';
import '../../../core/network/api_client.dart';
import '../../../core/constants/api_constants.dart';
import '../../../core/storage/local_storage.dart';
import '../../../core/storage/sync_queue_manager.dart';
import '../../../core/network/api_exceptions.dart';
import '../models/lot_model.dart';

class LotRepository extends ChangeNotifier {
  final ApiClient _apiClient = ApiClient();
  final LocalStorage _localStorage = LocalStorage();
  final SyncQueueManager _syncManager = SyncQueueManager();

  List<LotModel> _lots = [];
  bool _isLoading = false;
  String? _errorMessage;

  List<LotModel> get lots => List.unmodifiable(_lots);
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  Future<void> fetchLots({String? centreId, String? status}) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final query = <String, dynamic>{'page': 1, 'page_size': 50};
      if (centreId != null) query['procurement_centre_id'] = centreId;
      if (status != null) query['status'] = status;

      final res = await _apiClient.get(ApiConstants.lots, queryParams: query);
      if (res is Map && res.containsKey('items')) {
        final items = (res['items'] as List)
            .map((item) => LotModel.fromJson(Map<String, dynamic>.from(item as Map)))
            .toList();
        _lots = items;
        await _localStorage.cacheLots(_lots.map((l) => l.toJson()).toList());
      }
    } on NetworkException {
      final cached = _localStorage.getCachedLots();
      if (cached.isNotEmpty) {
        _lots = cached.map((c) => LotModel.fromJson(c)).toList();
      } else {
        _errorMessage = "Offline mode: No cached lots available.";
      }
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<LotModel> createLot({
    required String lotNumber,
    required String farmerId,
    required String procurementCentreId,
    required String variety,
    required double quantityQuintals,
    required int bagCount,
  }) async {
    final payload = {
      'lot_number': lotNumber,
      'farmer_id': farmerId,
      'procurement_centre_id': procurementCentreId,
      'variety': variety,
      'quantity_quintals': quantityQuintals,
      'bag_count': bagCount,
    };

    try {
      final res = await _apiClient.post(ApiConstants.lots, body: payload);
      final newLot = LotModel.fromJson(Map<String, dynamic>.from(res as Map));
      _lots.insert(0, newLot);
      await _localStorage.cacheLots(_lots.map((l) => l.toJson()).toList());
      notifyListeners();
      return newLot;
    } on NetworkException {
      // Offline mode: create local model and enqueue sync
      final localId = const Uuid().v4();
      final offlinePayload = Map<String, dynamic>.from(payload)
        ..['id'] = localId
        ..['status'] = 'REGISTERED'
        ..['created_at'] = DateTime.now().toUtc().toIso8601String();
      final localLot = LotModel.fromJson(offlinePayload);
      _lots.insert(0, localLot);
      await _localStorage.cacheLots(_lots.map((l) => l.toJson()).toList());

      await _syncManager.enqueue(
        entityType: 'Lot',
        payload: payload,
      );

      notifyListeners();
      return localLot;
    }
  }
}
