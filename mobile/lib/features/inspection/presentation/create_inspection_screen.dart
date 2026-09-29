import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../auth/repository/auth_repository.dart';
import '../../lot/repository/lot_repository.dart';
import '../../lot/models/lot_model.dart';
import '../repository/inspection_repository.dart';

class CreateInspectionScreen extends StatefulWidget {
  @override
  _CreateInspectionScreenState createState() => _CreateInspectionScreenState();
}

class _CreateInspectionScreenState extends State<CreateInspectionScreen> {
  String? _selectedLotId;
  int _sampleSize = 50;
  bool _isCreating = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final args = ModalRoute.of(context)?.settings.arguments;
    if (args is LotModel && _selectedLotId == null) {
      _selectedLotId = args.id;
    }
  }

  Future<void> _handleStartInspection() async {
    final user = context.read<AuthRepository>().currentUser;
    if (_selectedLotId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please select a lot to inspect.")),
      );
      return;
    }

    if (user == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Inspector profile not found.")),
      );
      return;
    }

    setState(() => _isCreating = true);

    try {
      final inspRepo = context.read<InspectionRepository>();
      final newInsp = await inspRepo.createInspection(
        lotId: _selectedLotId!,
        inspectorId: user.id,
        sampleSize: _sampleSize,
      );

      if (!mounted) return;
      // Navigate to Sampling protocol screen
      Navigator.pushReplacementNamed(context, '/sampling', arguments: newInsp);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Could not initiate inspection: $e")),
      );
    } finally {
      if (mounted) setState(() => _isCreating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final lots = context.watch<LotRepository>().lots;
    final user = context.watch<AuthRepository>().currentUser;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Initiate Inspection"),
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
                        "Inspection Configuration",
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        "Follow standard DoCA sampling protocol PS26031.",
                        style: TextStyle(fontSize: 12.5, color: AppColors.textSecondary),
                      ),
                      const SizedBox(height: 16),
                      DropdownButtonFormField<String>(
                        value: _selectedLotId,
                        decoration: const InputDecoration(
                          labelText: "Select Onion Lot *",
                          prefixIcon: Icon(Icons.inbox),
                        ),
                        items: lots.map((lot) {
                          return DropdownMenuItem(
                            value: lot.id,
                            child: Text("${lot.lotNumber} (${lot.quantityQuintals} Qtl)"),
                          );
                        }).toList(),
                        onChanged: (val) => setState(() => _selectedLotId = val),
                      ),
                      const SizedBox(height: 16),
                      const Text(
                        "Target Sample Size",
                        style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Expanded(
                            child: ChoiceChip(
                              label: const Center(child: Text("50 Onions (Standard)")),
                              selected: _sampleSize == 50,
                              onSelected: (val) => setState(() => _sampleSize = 50),
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: ChoiceChip(
                              label: const Center(child: Text("100 Onions (Large Lot)")),
                              selected: _sampleSize == 100,
                              onSelected: (val) => setState(() => _sampleSize = 100),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppColors.backgroundLight,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.security, size: 20, color: AppColors.primaryGreen),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                "Assigned Inspector: ${user?.fullName ?? 'N/A'}",
                                style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: _isCreating ? null : _handleStartInspection,
                icon: const Icon(Icons.arrow_forward),
                label: _isCreating
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                      )
                    : const Text("PROCEED TO SAMPLING PROTOCOL"),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
