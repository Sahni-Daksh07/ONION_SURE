import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class LocalStorage {
  static final LocalStorage _instance = LocalStorage._internal();
  factory LocalStorage() => _instance;
  LocalStorage._internal();

  late SharedPreferences _prefs;

  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  // Key-value raw helpers
  Future<void> setString(String key, String value) => _prefs.setString(key, value);
  String? getString(String key) => _prefs.getString(key);

  Future<void> setJson(String key, dynamic data) => _prefs.setString(key, jsonEncode(data));
  dynamic getJson(String key) {
    final str = _prefs.getString(key);
    if (str == null || str.isEmpty) return null;
    try {
      return jsonDecode(str);
    } catch (_) {
      return null;
    }
  }

  Future<void> remove(String key) => _prefs.remove(key);

  // User session
  Future<void> saveUserSession(Map<String, dynamic> userMap) async {
    await setJson('user_session', userMap);
  }

  Map<String, dynamic>? getUserSession() {
    final data = getJson('user_session');
    if (data is Map<String, dynamic>) return data;
    return null;
  }

  Future<void> clearUserSession() async {
    await remove('user_session');
    await remove('access_token');
  }

  // Cached Master Data
  Future<void> cacheFarmers(List<Map<String, dynamic>> farmers) async {
    await setJson('cached_farmers', farmers);
  }

  List<Map<String, dynamic>> getCachedFarmers() {
    final list = getJson('cached_farmers');
    if (list is List) {
      return list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
    }
    return [];
  }

  Future<void> cacheLots(List<Map<String, dynamic>> lots) async {
    await setJson('cached_lots', lots);
  }

  List<Map<String, dynamic>> getCachedLots() {
    final list = getJson('cached_lots');
    if (list is List) {
      return list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
    }
    return [];
  }

  Future<void> cacheInspections(List<Map<String, dynamic>> inspections) async {
    await setJson('cached_inspections', inspections);
  }

  List<Map<String, dynamic>> getCachedInspections() {
    final list = getJson('cached_inspections');
    if (list is List) {
      return list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
    }
    return [];
  }
}
