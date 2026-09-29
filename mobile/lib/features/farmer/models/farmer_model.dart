class FarmerModel {
  final String id;
  final String farmerCode;
  final String name;
  final String? phone;
  final String? village;
  final String? district;
  final String? state;
  final String? aadhaarMasked;

  FarmerModel({
    required this.id,
    required this.farmerCode,
    required this.name,
    this.phone,
    this.village,
    this.district,
    this.state,
    this.aadhaarMasked,
  });

  factory FarmerModel.fromJson(Map<String, dynamic> json) {
    return FarmerModel(
      id: json['id'] as String,
      farmerCode: json['farmer_code'] as String,
      name: json['name'] as String,
      phone: json['phone'] as String?,
      village: json['village'] as String?,
      district: json['district'] as String?,
      state: json['state'] as String?,
      aadhaarMasked: json['aadhaar_masked'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'farmer_code': farmerCode,
        'name': name,
        'phone': phone,
        'village': village,
        'district': district,
        'state': state,
        'aadhaar_masked': aadhaarMasked,
      };
}
