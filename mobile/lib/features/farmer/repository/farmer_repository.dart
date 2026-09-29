import 'package:flutter/foundation.dart';
import 'package:uuid/uuid.dart';
import '../../../core/network/api_client.dart';
import '../../../core/constants/api_constants.dart';
import '../../../core/storage/local_storage.dart';
import '../../../core/storage/sync_queue_manager.dart';
import '../../../core/network/api_exceptions.dart';
import '../models/farmer_model.dart';

class FarmerRepository extends ChangeNotifier {
  final ApiClient _apiClient = ApiClient();
  final LocalStorage _localStorage = LocalStorage();
  final SyncQueueManager _syncManager = SyncQueueManager();

  List<FarmerModel> _farmers = [];
  bool _isLoading = false;
  String? _errorMessage;

  List<FarmerModel> get farmers => List.unmodifiable(_farmers);
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  Future<void> fetchFarmers({String? district}) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final query = <String, dynamic>{'page': 1, 'page_size': 100};
      if (district != null && district.isNotEmpty) {
        query['district'] = district;
      }

      final res = await _apiClient.get(ApiConstants.farmers, queryParams: query);
      if (res is Map && res.containsKey('items')) {
        final items = (res['items'] as List)
            .map((item) => FarmerModel.fromJson(Map<String, dynamic>.from(item as Map)))
            .toList();
        _farmers = items;
        await _localStorage.cacheFarmers(_farmers.map((f) => f.toJson()).toList());
      }
    } on NetworkException {
      // Fallback to offline cached farmers
      final cached = _localStorage.getCachedFarmers();
      if (cached.isNotEmpty) {
        _farmers = cached.map((c) => FarmerModel.fromJson(c)).toList();
      } else {
        _errorMessage = "Offline mode: No cached farmers available.";
      }
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<FarmerModel> createFarmer({
    required String farmerCode,
    required String name,
    String? phone,
    String? village,
    String? district,
    String? state,
    String? aadhaarMasked,
  }) async {
    final payload = {
      'farmer_code': farmerCode,
      'name': name,
      'phone': phone,
      'village': village,
      'district': district,
      'state': state,
      'aadhaar_masked': aadhaarMasked,
    };

    try {
      final res = await _apiClient.post(ApiConstants.farmers, body: payload);
      final newFarmer = FarmerModel.fromJson(Map<String, dynamic>.from(res as Map));
      _farmers.insert(0, newFarmer);
      await _localStorage.cacheFarmers(_farmers.map((f) => f.toJson()).toList());
      notifyListeners();
      return newFarmer;
    } on NetworkException {
      // Offline mode: generate local ID and queue for sync
      final localId = const Uuid().v4();
      final offlinePayload = Map<String, dynamic>.from(payload)..['id'] = localId;
      final localFarmer = FarmerModel.fromJson(offlinePayload);
      _farmers.insert(0, localFarmer);
      await _localStorage.cacheFarmers(_farmers.map((f) => f.toJson()).toList());

      await _syncManager.enqueue(
        entityType: 'Farmer',
        payload: payload,
      );

      notifyListeners();
      return localFarmer;
    }
  }
}
