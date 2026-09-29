class ApiException implements Exception {
  final String message;
  final int? statusCode;
  final dynamic details;

  ApiException(this.message, {this.statusCode, this.details});

  @override
  String toString() => message;
}

class NetworkException extends ApiException {
  NetworkException([String message = "No network connection or server unreachable."])
      : super(message, statusCode: 0);
}

class UnauthorizedException extends ApiException {
  UnauthorizedException([String message = "Authentication failed or token expired."])
      : super(message, statusCode: 401);
}

class ForbiddenException extends ApiException {
  ForbiddenException([String message = "You do not have permission to perform this action."])
      : super(message, statusCode: 403);
}

class NotFoundException extends ApiException {
  NotFoundException([String message = "The requested resource was not found."])
      : super(message, statusCode: 404);
}

class ValidationException extends ApiException {
  ValidationException(String message, {dynamic details})
      : super(message, statusCode: 422, details: details);
}
