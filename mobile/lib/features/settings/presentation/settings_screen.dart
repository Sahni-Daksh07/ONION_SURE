import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/network/api_client.dart';
import '../../../core/storage/sync_queue_manager.dart';
import '../../auth/repository/auth_repository.dart';
import '../../procurement_centre/repository/centre_repository.dart';

class SettingsScreen extends StatefulWidget {
  @override
  _SettingsScreenState createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _serverUrlController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _serverUrlController.text = ApiClient().baseUrl;
  }

  @override
  void dispose() {
    _serverUrlController.dispose();
    super.dispose();
  }

  Future<void> _saveServerUrl() async {
    final url = _serverUrlController.text.trim();
    if (url.isNotEmpty) {
      await ApiClient().setBaseUrl(url);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Backend server set to: $url")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final authRepo = context.watch<AuthRepository>();
    final centreRepo = context.watch<CentreRepository>();
    final syncManager = context.watch<SyncQueueManager>();

    final user = authRepo.currentUser;
    final activeCentre = centreRepo.activeCentre;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Terminal Settings"),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Inspector Identity Card
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const CircleAvatar(
                            radius: 24,
                            backgroundColor: AppColors.primaryGreen,
                            child: Icon(Icons.person, color: Colors.white, size: 28),
                          ),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  user?.fullName ?? "Authorized Inspector",
                                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  user?.email ?? "inspector@onionsure.gov.in",
                                  style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                                ),
                                const SizedBox(height: 4),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: AppColors.primaryGreen.withOpacity(0.12),
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: Text(
                                    user?.roles.join(" • ") ?? "INSPECTOR",
                                    style: const TextStyle(
                                      color: AppColors.primaryGreen,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 10.5,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),
                      const Divider(),
                      const SizedBox(height: 6),
                      Text(
                        "Assigned Mandi: ${activeCentre != null ? '${activeCentre.name} (${activeCentre.district})' : 'All Mandis'}",
                        style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Offline Sync Queue Management
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            "Offline Synchronization",
                            style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: syncManager.pendingCount > 0
                                  ? Colors.amber.shade100
                                  : AppColors.gradeABg,
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              syncManager.pendingCount > 0
                                  ? "${syncManager.pendingCount} PENDING"
                                  : "UP TO DATE",
                              style: TextStyle(
                                color: syncManager.pendingCount > 0 ? Colors.amber.shade900 : AppColors.gradeA,
                                fontWeight: FontWeight.w800,
                                fontSize: 10.5,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        "Queue Size: ${syncManager.queue.length} items (${syncManager.pendingCount} awaiting upload).",
                        style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                      ),
                      const SizedBox(height: 14),
                      Row(
                        children: [
                          Expanded(
                            child: ElevatedButton.icon(
                              onPressed: syncManager.isSyncing
                                  ? null
                                  : () => syncManager.syncPendingBatch(),
                              icon: const Icon(Icons.sync, size: 18),
                              label: syncManager.isSyncing
                                  ? const SizedBox(
                                      width: 16,
                                      height: 16,
                                      child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                                    )
                                  : const Text("SYNC NOW"),
                            ),
                          ),
                          const SizedBox(width: 10),
                          OutlinedButton(
                            onPressed: () => syncManager.clearSynced(),
                            child: const Text("Clear Synced"),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Network & Server Configuration
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "Backend Server Host",
                        style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        "Change host URL to point to a specific local or cloud API instance.",
                        style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _serverUrlController,
                        decoration: const InputDecoration(
                          labelText: "Base URL",
                          prefixIcon: Icon(Icons.dns),
                        ),
                      ),
                      const SizedBox(height: 12),
                      ElevatedButton(
                        onPressed: _saveServerUrl,
                        child: const Text("SAVE SERVER URL"),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Mandi Information & Compliance
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(14.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: const [
                      Text(
                        "Smart India Hackathon 2026 • PS26031",
                        style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
                      ),
                      SizedBox(height: 4),
                      Text(
                        "Ministry of Consumer Affairs, Food & Public Distribution\nDepartment of Consumer Affairs (DoCA)\nEngine: Deterministic Vision & Grading Matrix v1.0.0",
                        style: TextStyle(fontSize: 11.5, color: AppColors.textSecondary, height: 1.4),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              OutlinedButton.icon(
                onPressed: () async {
                  await authRepo.logout();
                  if (!mounted) return;
                  Navigator.pushNamedAndRemoveUntil(context, '/login', (route) => false);
                },
                icon: const Icon(Icons.logout, color: AppColors.gradeReject),
                label: const Text(
                  "LOGOUT FROM MANDI TERMINAL",
                  style: TextStyle(color: AppColors.gradeReject),
                ),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: AppColors.gradeReject),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
