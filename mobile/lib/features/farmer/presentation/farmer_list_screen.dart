import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/state_views.dart';
import '../repository/farmer_repository.dart';
import '../models/farmer_model.dart';

class FarmerListScreen extends StatefulWidget {
  @override
  _FarmerListScreenState createState() => _FarmerListScreenState();
}

class _FarmerListScreenState extends State<FarmerListScreen> {
  final _searchController = TextEditingController();
  String _searchQuery = "";

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<FarmerRepository>().fetchFarmers();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _showAddFarmerDialog() {
    final codeController = TextEditingController(text: "FARM-${const Uuid().v4().substring(0, 6).toUpperCase()}");
    final nameController = TextEditingController();
    final phoneController = TextEditingController();
    final villageController = TextEditingController();
    final districtController = TextEditingController(text: "Nashik");
    final stateController = TextEditingController(text: "Maharashtra");
    final aadhaarController = TextEditingController(text: "XXXX-XXXX-1234");

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Register Farmer"),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: codeController,
                decoration: const InputDecoration(labelText: "Farmer Code"),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: nameController,
                decoration: const InputDecoration(labelText: "Full Name *"),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: phoneController,
                keyboardType: TextInputType.phone,
                decoration: const InputDecoration(labelText: "Phone Number"),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: villageController,
                decoration: const InputDecoration(labelText: "Village"),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: districtController,
                decoration: const InputDecoration(labelText: "District"),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: aadhaarController,
                decoration: const InputDecoration(labelText: "Masked Aadhaar"),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
          ElevatedButton(
            onPressed: () async {
              if (nameController.text.trim().isEmpty) return;
              Navigator.pop(ctx);
              final repo = context.read<FarmerRepository>();
              await repo.createFarmer(
                farmerCode: codeController.text.trim(),
                name: nameController.text.trim(),
                phone: phoneController.text.trim(),
                village: villageController.text.trim(),
                district: districtController.text.trim(),
                state: stateController.text.trim(),
                aadhaarMasked: aadhaarController.text.trim(),
              );
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text("Farmer registered successfully")),
              );
            },
            child: const Text("Register"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final repo = context.watch<FarmerRepository>();
    final allFarmers = repo.farmers;

    final filteredFarmers = allFarmers.where((f) {
      if (_searchQuery.isEmpty) return true;
      final q = _searchQuery.toLowerCase();
      return f.name.toLowerCase().contains(q) ||
          f.farmerCode.toLowerCase().contains(q) ||
          (f.phone?.contains(q) ?? false) ||
          (f.village?.toLowerCase().contains(q) ?? false);
    }).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text("Farmer Directory"),
        actions: [
          IconButton(
            icon: const Icon(Icons.person_add),
            tooltip: "Add Farmer",
            onPressed: _showAddFarmerDialog,
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(12.0),
              child: TextField(
                controller: _searchController,
                onChanged: (val) => setState(() => _searchQuery = val.trim()),
                decoration: InputDecoration(
                  hintText: "Search farmer by name, code, village...",
                  prefixIcon: const Icon(Icons.search),
                  suffixIcon: _searchQuery.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear),
                          onPressed: () {
                            _searchController.clear();
                            setState(() => _searchQuery = "");
                          },
                        )
                      : null,
                ),
              ),
            ),
            Expanded(
              child: repo.isLoading
                  ? const LoadingView(message: "Loading farmers...")
                  : repo.errorMessage != null && allFarmers.isEmpty
                      ? ErrorView(
                          message: repo.errorMessage!,
                          onRetry: () => repo.fetchFarmers(),
                        )
                      : filteredFarmers.isEmpty
                          ? EmptyView(
                              title: "No Farmers Found",
                              message: _searchQuery.isEmpty
                                  ? "No farmers registered in this mandi yet."
                                  : "No matches found for '$_searchQuery'.",
                              actionLabel: "Register Farmer",
                              onAction: _showAddFarmerDialog,
                            )
                          : ListView.separated(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                              itemCount: filteredFarmers.length,
                              separatorBuilder: (_, __) => const SizedBox(height: 8),
                              itemBuilder: (ctx, index) {
                                final farmer = filteredFarmers[index];
                                return Card(
                                  child: ListTile(
                                    leading: CircleAvatar(
                                      backgroundColor: AppColors.primaryGreen.withOpacity(0.12),
                                      child: Text(
                                        farmer.name.substring(0, 1).toUpperCase(),
                                        style: const TextStyle(
                                          fontWeight: FontWeight.bold,
                                          color: AppColors.primaryGreen,
                                        ),
                                      ),
                                    ),
                                    title: Text(
                                      farmer.name,
                                      style: const TextStyle(fontWeight: FontWeight.w700),
                                    ),
                                    subtitle: Text(
                                      "${farmer.farmerCode} • ${farmer.village ?? ''}, ${farmer.district ?? ''}",
                                      style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                                    ),
                                    trailing: farmer.phone != null
                                        ? Text(
                                            farmer.phone!,
                                            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                                          )
                                        : null,
                                  ),
                                );
                              },
                            ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showAddFarmerDialog,
        backgroundColor: AppColors.primaryGreen,
        icon: const Icon(Icons.add, color: Colors.white),
        label: const Text("Add Farmer", style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
      ),
    );
  }
}
