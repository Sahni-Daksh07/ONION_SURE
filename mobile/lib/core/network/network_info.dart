import 'dart:io';
import 'package:flutter/foundation.dart';

/// Governs network connectivity monitoring and airplane mode simulation for offline field testing.
class NetworkInfo extends ChangeNotifier {
  static final NetworkInfo _instance = NetworkInfo._internal();
  factory NetworkInfo() => _instance;
  NetworkInfo._internal();

  bool _isAirplaneMode = false;
  bool _isOnline = true;

  bool get isAirplaneMode => _isAirplaneMode;
  bool get isOnline => !_isAirplaneMode && _isOnline;

  void setAirplaneMode(bool enabled) {
    _isAirplaneMode = enabled;
    notifyListeners();
  }

  void toggleAirplaneMode() {
    _isAirplaneMode = !_isAirplaneMode;
    notifyListeners();
  }

  Future<bool> checkConnectivity({String host = '8.8.8.8'}) async {
    if (_isAirplaneMode) {
      _isOnline = false;
      notifyListeners();
      return false;
    }

    try {
      final result = await InternetAddress.lookup(host).timeout(const Duration(seconds: 3));
      _isOnline = result.isNotEmpty && result[0].rawAddress.isNotEmpty;
    } catch (_) {
      _isOnline = false;
    }
    notifyListeners();
    return _isOnline;
  }
}
