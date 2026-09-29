class LotModel {
  final String id;
  final String lotNumber;
  final String farmerId;
  final String procurementCentreId;
  final String variety;
  final double quantityQuintals;
  final int bagCount;
  final String status;
  final DateTime createdAt;

  LotModel({
    required this.id,
    required this.lotNumber,
    required this.farmerId,
    required this.procurementCentreId,
    required this.variety,
    required this.quantityQuintals,
    required this.bagCount,
    required this.status,
    required this.createdAt,
  });

  factory LotModel.fromJson(Map<String, dynamic> json) {
    return LotModel(
      id: json['id'] as String,
      lotNumber: json['lot_number'] as String,
      farmerId: json['farmer_id'] as String,
      procurementCentreId: json['procurement_centre_id'] as String,
      variety: json['variety'] as String? ?? 'Red',
      quantityQuintals: (json['quantity_quintals'] as num).toDouble(),
      bagCount: json['bag_count'] as int? ?? 1,
      status: json['status'] as String? ?? 'REGISTERED',
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'lot_number': lotNumber,
        'farmer_id': farmerId,
        'procurement_centre_id': procurementCentreId,
        'variety': variety,
        'quantity_quintals': quantityQuintals,
        'bag_count': bagCount,
        'status': status,
        'created_at': createdAt.toIso8601String(),
      };
}
