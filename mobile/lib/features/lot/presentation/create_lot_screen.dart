import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';
import '../../../core/theme/app_colors.dart';
import '../../farmer/repository/farmer_repository.dart';
import '../../procurement_centre/repository/centre_repository.dart';
import '../repository/lot_repository.dart';

class CreateLotScreen extends StatefulWidget {
  @override
  _CreateLotScreenState createState() => _CreateLotScreenState();
}

class _CreateLotScreenState extends State<CreateLotScreen> {
  final _lotNumberController = TextEditingController(
    text: "LOT-MANDI-${const Uuid().v4().substring(0, 6).toUpperCase()}",
  );
  final _quantityController = TextEditingController(text: "25.0");
  final _bagCountController = TextEditingController(text: "50");

  String? _selectedFarmerId;
  String _selectedVariety = "Red";
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final farmerRepo = context.read<FarmerRepository>();
      if (farmerRepo.farmers.isEmpty) {
        farmerRepo.fetchFarmers();
      }
    });
  }

  @override
  void dispose() {
    _lotNumberController.dispose();
    _quantityController.dispose();
    _bagCountController.dispose();
    super.dispose();
  }

  Future<void> _handleSubmit() async {
    final lotNum = _lotNumberController.text.trim();
    final qty = double.tryParse(_quantityController.text.trim());
    final bags = int.tryParse(_bagCountController.text.trim());
    final centre = context.read<CentreRepository>().activeCentre;

    if (_selectedFarmerId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please select a registered farmer.")),
      );
      return;
    }

    if (centre == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please select an active procurement centre.")),
      );
      return;
    }

    if (qty == null || qty <= 0 || bags == null || bags <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please enter valid positive quantity and bag count.")),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final lotRepo = context.read<LotRepository>();
      final newLot = await lotRepo.createLot(
        lotNumber: lotNum,
        farmerId: _selectedFarmerId!,
        procurementCentreId: centre.id,
        variety: _selectedVariety,
        quantityQuintals: qty,
        bagCount: bags,
      );

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Lot ${newLot.lotNumber} registered successfully!")),
      );

      // Offer immediate inspection flow
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (ctx) => AlertDialog(
          title: const Text("Lot Registered"),
          content: Text("Lot ${newLot.lotNumber} is now registered. Would you like to proceed directly to sampling & quality inspection?"),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(ctx);
                Navigator.pop(context);
              },
              child: const Text("Return to Dashboard"),
            ),
            ElevatedButton(
              onPressed: () {
                Navigator.pop(ctx);
                Navigator.pushReplacementNamed(context, '/create_inspection', arguments: newLot);
              },
              child: const Text("Start Inspection"),
            ),
          ],
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Registration Error: $e")),
      );
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final farmers = context.watch<FarmerRepository>().farmers;
    final centre = context.watch<CentreRepository>().activeCentre;

    return Scaffold(
      appBar: AppBar(
        title: const Text("New Lot Intake"),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "Procurement Intake Details",
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: AppColors.backgroundLight,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.storefront, color: AppColors.primaryGreen, size: 20),
                            const SizedBox(width: 8),
                            Text(
                              centre != null ? "${centre.name} (${centre.centreCode})" : "Select Active Centre",
                              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        controller: _lotNumberController,
                        decoration: const InputDecoration(
                          labelText: "Lot Tracking Code *",
                          prefixIcon: Icon(Icons.tag),
                        ),
                      ),
                      const SizedBox(height: 14),
                      DropdownButtonFormField<String>(
                        value: _selectedFarmerId,
                        decoration: const InputDecoration(
                          labelText: "Select Farmer *",
                          prefixIcon: Icon(Icons.person),
                        ),
                        items: farmers.map((f) {
                          return DropdownMenuItem(
                            value: f.id,
                            child: Text("${f.name} (${f.farmerCode})"),
                          );
                        }).toList(),
                        onChanged: (val) => setState(() => _selectedFarmerId = val),
                      ),
                      const SizedBox(height: 14),
                      DropdownButtonFormField<String>(
                        value: _selectedVariety,
                        decoration: const InputDecoration(
                          labelText: "Onion Variety *",
                          prefixIcon: Icon(Icons.category),
                        ),
                        items: const [
                          DropdownMenuItem(value: "Red", child: Text("Red Onion (Nashik/Pimpalgaon)")),
                          DropdownMenuItem(value: "White", child: Text("White Onion (Bhavnagar/Mahua)")),
                          DropdownMenuItem(value: "Garwa", child: Text("Garwa / Late Kharif")),
                        ],
                        onChanged: (val) => setState(() => _selectedVariety = val ?? "Red"),
                      ),
                      const SizedBox(height: 14),
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _quantityController,
                              keyboardType: const TextInputType.numberWithOptions(decimal: true),
                              decoration: const InputDecoration(
                                labelText: "Quantity (Quintals) *",
                                prefixIcon: Icon(Icons.scale),
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: TextField(
                              controller: _bagCountController,
                              keyboardType: TextInputType.number,
                              decoration: const InputDecoration(
                                labelText: "Bag Count *",
                                prefixIcon: Icon(Icons.inventory),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _isSubmitting ? null : _handleSubmit,
                child: _isSubmitting
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text("REGISTER ONION LOT"),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
