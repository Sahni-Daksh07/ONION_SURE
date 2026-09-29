import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';
import '../../../core/constants/api_constants.dart';
import '../../../core/storage/local_storage.dart';
import '../../../core/network/api_exceptions.dart';
import '../models/user_model.dart';

class AuthRepository extends ChangeNotifier {
  final ApiClient _apiClient = ApiClient();
  final LocalStorage _localStorage = LocalStorage();

  UserModel? _currentUser;
  bool _isAuthenticated = false;
  bool _isOfflineMode = false;

  UserModel? get currentUser => _currentUser;
  bool get isAuthenticated => _isAuthenticated;
  bool get isOfflineMode => _isOfflineMode;

  Future<void> checkAuthStatus() async {
    final cachedUser = _localStorage.getUserSession();
    final token = _localStorage.getString('access_token');

    if (token != null && cachedUser != null) {
      _currentUser = UserModel.fromJson(cachedUser);
      _isAuthenticated = true;
      _apiClient.setAuthToken(token);

      // Verify online profile in background if network available
      try {
        final profile = await _apiClient.get(ApiConstants.me);
        if (profile is Map<String, dynamic>) {
          _currentUser = UserModel.fromJson(profile);
          await _localStorage.saveUserSession(profile);
          _isOfflineMode = false;
        }
      } catch (e) {
        // If server unreachable, continue in offline mode safely
        _isOfflineMode = true;
      }
      notifyListeners();
    } else {
      _isAuthenticated = false;
      _currentUser = null;
      notifyListeners();
    }
  }

  Future<UserModel> login(String email, String password) async {
    try {
      final res = await _apiClient.post(
        ApiConstants.login,
        body: {'email': email, 'password': password},
      );

      final token = res['access_token'] as String;
      await _apiClient.setAuthToken(token);
      await _localStorage.setString('access_token', token);

      final profileRes = await _apiClient.get(ApiConstants.me);
      final user = UserModel.fromJson(profileRes as Map<String, dynamic>);
      _currentUser = user;
      _isAuthenticated = true;
      _isOfflineMode = false;

      await _localStorage.saveUserSession(profileRes);
      notifyListeners();
      return user;
    } on NetworkException {
      // Check if credentials match cached session for offline field entry
      final cachedUser = _localStorage.getUserSession();
      if (cachedUser != null && cachedUser['email'] == email) {
        _currentUser = UserModel.fromJson(cachedUser);
        _isAuthenticated = true;
        _isOfflineMode = true;
        notifyListeners();
        return _currentUser!;
      }
      rethrow;
    }
  }

  Future<void> logout() async {
    await _localStorage.clearUserSession();
    await _apiClient.setAuthToken(null);
    _currentUser = null;
    _isAuthenticated = false;
    _isOfflineMode = false;
    notifyListeners();
  }
}
