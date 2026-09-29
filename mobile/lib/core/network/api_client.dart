import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../constants/api_constants.dart';
import 'api_exceptions.dart';

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;
  ApiClient._internal();

  String _baseUrl = ApiConstants.defaultBaseUrl;
  String? _accessToken;

  String get baseUrl => _baseUrl;
  String? get accessToken => _accessToken;

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _baseUrl = prefs.getString('api_base_url') ?? ApiConstants.defaultBaseUrl;
    _accessToken = prefs.getString('access_token');
  }

  Future<void> setBaseUrl(String url) async {
    _baseUrl = url.endsWith('/') ? url.substring(0, url.length - 1) : url;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('api_base_url', _baseUrl);
  }

  Future<void> setAuthToken(String? token) async {
    _accessToken = token;
    final prefs = await SharedPreferences.getInstance();
    if (token != null) {
      await prefs.setString('access_token', token);
    } else {
      await prefs.remove('access_token');
    }
  }

  Map<String, String> _buildHeaders({Map<String, String>? extraHeaders}) {
    final headers = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (_accessToken != null && _accessToken!.isNotEmpty) {
      headers['Authorization'] = 'Bearer $_accessToken';
    }
    if (extraHeaders != null) {
      headers.addAll(extraHeaders);
    }
    return headers;
  }

  Uri _buildUri(String path, [Map<String, dynamic>? queryParams]) {
    final fullUrl = path.startsWith('http') ? path : '$_baseUrl$path';
    final uri = Uri.parse(fullUrl);
    if (queryParams != null && queryParams.isNotEmpty) {
      final stringParams = queryParams.map((k, v) => MapEntry(k, v.toString()));
      return uri.replace(queryParameters: stringParams);
    }
    return uri;
  }

  Future<dynamic> get(String path, {Map<String, dynamic>? queryParams}) async {
    try {
      final uri = _buildUri(path, queryParams);
      final response = await http
          .get(uri, headers: _buildHeaders())
          .timeout(const Duration(seconds: 15));
      return _processResponse(response);
    } on SocketException {
      throw NetworkException("Cannot reach server at $_baseUrl. Check network/WiFi.");
    } on http.ClientException {
      throw NetworkException("Connection error. Server may be offline.");
    }
  }

  Future<dynamic> post(String path, {dynamic body, Map<String, dynamic>? queryParams}) async {
    try {
      final uri = _buildUri(path, queryParams);
      final response = await http
          .post(
            uri,
            headers: _buildHeaders(),
            body: body != null ? jsonEncode(body) : null,
          )
          .timeout(const Duration(seconds: 25));
      return _processResponse(response);
    } on SocketException {
      throw NetworkException("Cannot reach server at $_baseUrl. Check network/WiFi.");
    } on http.ClientException {
      throw NetworkException("Connection error. Server may be offline.");
    }
  }

  Future<dynamic> put(String path, {dynamic body}) async {
    try {
      final uri = _buildUri(path);
      final response = await http
          .put(
            uri,
            headers: _buildHeaders(),
            body: body != null ? jsonEncode(body) : null,
          )
          .timeout(const Duration(seconds: 20));
      return _processResponse(response);
    } on SocketException {
      throw NetworkException("Cannot reach server at $_baseUrl. Check network/WiFi.");
    }
  }

  Future<dynamic> uploadMultipart(
    String path, {
    required List<int> fileBytes,
    required String filename,
    Map<String, String>? fields,
  }) async {
    try {
      final uri = _buildUri(path);
      final request = http.MultipartRequest('POST', uri);
      
      if (_accessToken != null && _accessToken!.isNotEmpty) {
        request.headers['Authorization'] = 'Bearer $_accessToken';
      }

      if (fields != null) {
        request.fields.addAll(fields);
      }

      final multipartFile = http.MultipartFile.fromBytes(
        'file',
        fileBytes,
        filename: filename,
      );
      request.files.add(multipartFile);

      final streamedResponse = await request.send().timeout(const Duration(seconds: 60));
      final response = await http.Response.fromStream(streamedResponse);
      return _processResponse(response);
    } on SocketException {
      throw NetworkException("Upload failed. Server unreachable.");
    }
  }

  dynamic _processResponse(http.Response response) {
    dynamic body;
    try {
      if (response.body.isNotEmpty) {
        body = jsonDecode(response.body);
      }
    } catch (_) {
      body = response.body;
    }

    switch (response.statusCode) {
      case 200:
      case 201:
      case 204:
        return body;
      case 400:
        final msg = body is Map && body.containsKey('detail') ? body['detail'] : "Bad Request";
        throw ApiException(msg.toString(), statusCode: 400);
      case 401:
        throw UnauthorizedException();
      case 403:
        throw ForbiddenException();
      case 404:
        final msg = body is Map && body.containsKey('detail') ? body['detail'] : "Not Found";
        throw NotFoundException(msg.toString());
      case 422:
        final msg = body is Map && body.containsKey('detail') ? jsonEncode(body['detail']) : "Validation Error";
        throw ValidationException(msg, details: body);
      default:
        final msg = body is Map && body.containsKey('detail') ? body['detail'] : "Server Error (${response.statusCode})";
        throw ApiException(msg.toString(), statusCode: response.statusCode);
    }
  }
}
