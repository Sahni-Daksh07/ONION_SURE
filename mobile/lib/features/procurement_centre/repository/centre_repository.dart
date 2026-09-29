import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';
import '../../../core/constants/api_constants.dart';
import '../../../core/storage/local_storage.dart';
import '../../../core/network/api_exceptions.dart';
import '../models/centre_model.dart';

class CentreRepository extends ChangeNotifier {
  final ApiClient _apiClient = ApiClient();
  final LocalStorage _localStorage = LocalStorage();

  List<CentreModel> _centres = [];
  CentreModel? _activeCentre;
  bool _isLoading = false;
  String? _errorMessage;

  List<CentreModel> get centres => List.unmodifiable(_centres);
  CentreModel? get activeCentre => _activeCentre;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  Future<void> fetchCentres() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final res = await _apiClient.get(ApiConstants.procurementCentres, queryParams: {'page': 1, 'page_size': 50});
      if (res is Map && res.containsKey('items')) {
        final items = (res['items'] as List)
            .map((item) => CentreModel.fromJson(Map<String, dynamic>.from(item as Map)))
            .toList();
        _centres = items;
        if (_centres.isNotEmpty && _activeCentre == null) {
          _activeCentre = _centres.first;
        }
        await _localStorage.setJson('cached_centres', _centres.map((c) => c.toJson()).toList());
      }
    } on NetworkException {
      final cached = _localStorage.getJson('cached_centres');
      if (cached is List && cached.isNotEmpty) {
        _centres = cached.map((c) => CentreModel.fromJson(Map<String, dynamic>.from(c as Map))).toList();
        if (_centres.isNotEmpty && _activeCentre == null) {
          _activeCentre = _centres.first;
        }
      } else {
        _errorMessage = "Offline mode: No cached centres found.";
      }
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void setActiveCentre(CentreModel centre) {
    _activeCentre = centre;
    _localStorage.setJson('active_centre', centre.toJson());
    notifyListeners();
  }
}
