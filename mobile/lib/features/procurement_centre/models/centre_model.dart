class CentreModel {
  final String id;
  final String centreCode;
  final String name;
  final String district;
  final String state;
  final bool isActive;

  CentreModel({
    required this.id,
    required this.centreCode,
    required this.name,
    required this.district,
    required this.state,
    this.isActive = true,
  });

  factory CentreModel.fromJson(Map<String, dynamic> json) {
    return CentreModel(
      id: json['id'] as String,
      centreCode: json['centre_code'] as String,
      name: json['name'] as String,
      district: json['district'] as String,
      state: json['state'] as String,
      isActive: json['is_active'] as bool? ?? true,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'centre_code': centreCode,
        'name': name,
        'district': district,
        'state': state,
        'is_active': isActive,
      };
}
