class UserModel {
  final String id;
  final String email;
  final String fullName;
  final String? phone;
  final String? procurementCentreId;
  final List<String> roles;
  final bool isActive;

  UserModel({
    required this.id,
    required this.email,
    required this.fullName,
    this.phone,
    this.procurementCentreId,
    required this.roles,
    required this.isActive,
  });

  bool get isAdmin => roles.contains('ADMIN');
  bool get isInspector => roles.contains('INSPECTOR');
  bool get isOfficer => roles.contains('OFFICER');
  bool get isReviewer => roles.contains('REVIEWER');

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] as String,
      email: json['email'] as String,
      fullName: json['full_name'] as String,
      phone: json['phone'] as String?,
      procurementCentreId: json['procurement_centre_id'] as String?,
      roles: (json['roles'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      isActive: json['is_active'] as bool? ?? true,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'email': email,
        'full_name': fullName,
        'phone': phone,
        'procurement_centre_id': procurementCentreId,
        'roles': roles,
        'is_active': isActive,
      };
}
