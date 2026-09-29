import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/state_views.dart';
import '../../../core/storage/sync_queue_manager.dart';
import '../../auth/repository/auth_repository.dart';
import '../../procurement_centre/repository/centre_repository.dart';
import '../../lot/repository/lot_repository.dart';
import '../../inspection/repository/inspection_repository.dart';

class DashboardScreen extends StatefulWidget {
  @override
  _DashboardScreenState createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _currentTab = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadDashboardData();
    });
  }

  Future<void> _loadDashboardData() async {
    final centreRepo = context.read<CentreRepository>();
    final lotRepo = context.read<LotRepository>();
    final inspRepo = context.read<InspectionRepository>();

    await Future.wait([
      centreRepo.fetchCentres(),
      lotRepo.fetchLots(),
      inspRepo.fetchInspections(),
    ]);
  }

  @override
  Widget build(BuildContext context) {
    final authRepo = context.watch<AuthRepository>();
    final centreRepo = context.watch<CentreRepository>();
    final lotRepo = context.watch<LotRepository>();
    final inspRepo = context.watch<InspectionRepository>();
    final syncManager = context.watch<SyncQueueManager>();

    final user = authRepo.currentUser;
    final activeCentre = centreRepo.activeCentre;
    final inspections = inspRepo.inspections;

    final gradeACount = inspections.where((i) => i.lotDecision == 'ACCEPT_GRADE_A').length;
    final ursCount = inspections.where((i) => i.lotDecision == 'ACCEPT_URS').length;
    final rejectCount = inspections.where((i) => i.lotDecision == 'REJECT_LOT').length;

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text("Mandi Quality Terminal", style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
            Text(
              activeCentre != null
                  ? "${activeCentre.name} (${activeCentre.centreCode})"
                  : "National APMC Network",
              style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.85)),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: "Refresh Dashboard",
            onPressed: _loadDashboardData,
          ),
          IconButton(
            icon: const Icon(Icons.account_circle),
            tooltip: "Inspector Profile",
            onPressed: () => Navigator.pushNamed(context, '/settings'),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            if (authRepo.isOfflineMode || syncManager.pendingCount > 0)
              OfflineBanner(
                pendingCount: syncManager.pendingCount,
                onSyncTap: () => syncManager.syncPendingBatch(),
              ),
            Expanded(
              child: RefreshIndicator(
                onRefresh: _loadDashboardData,
                child: SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // Inspector Header Card
                      Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: AppColors.primaryGreen.withOpacity(0.08),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: AppColors.primaryGreen.withOpacity(0.2)),
                        ),
                        child: Row(
                          children: [
                            const CircleAvatar(
                              backgroundColor: AppColors.primaryGreen,
                              child: Icon(Icons.badge, color: Colors.white, size: 20),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    user?.fullName ?? "Authorized Inspector",
                                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
                                  ),
                                  Text(
                                    user?.roles.join(", ") ?? "INSPECTOR",
                                    style: const TextStyle(fontSize: 11.5, color: AppColors.textSecondary),
                                  ),
                                ],
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: AppColors.online.withOpacity(0.15),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: const Text(
                                "MANDI READY",
                                style: TextStyle(
                                  color: AppColors.online,
                                  fontWeight: FontWeight.w800,
                                  fontSize: 10,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Metrics Grid
                      Row(
                        children: [
                          Expanded(
                            child: _buildMetricCard(
                              title: "Grade A Lots",
                              value: "$gradeACount",
                              color: AppColors.gradeA,
                              bgColor: AppColors.gradeABg,
                              icon: Icons.check_circle_outline,
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: _buildMetricCard(
                              title: "URS Lots",
                              value: "$ursCount",
                              color: AppColors.gradeURS,
                              bgColor: AppColors.gradeURSBg,
                              icon: Icons.warning_amber_rounded,
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: _buildMetricCard(
                              title: "Rejected",
                              value: "$rejectCount",
                              color: AppColors.gradeReject,
                              bgColor: AppColors.gradeRejectBg,
                              icon: Icons.cancel_outlined,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),

                      // Rapid Actions Grid
                      const Text(
                        "Operations & Quality Inspection",
                        style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          Expanded(
                            child: _buildActionTile(
                              title: "New Lot Intake",
                              subtitle: "Register farmer arrival",
                              icon: Icons.add_box_outlined,
                              color: AppColors.primaryGreen,
                              onTap: () => Navigator.pushNamed(context, '/create_lot'),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: _buildActionTile(
                              title: "Start Inspection",
                              subtitle: "AI quality assessment",
                              icon: Icons.camera_alt_outlined,
                              color: AppColors.harvestAmber,
                              onTap: () => Navigator.pushNamed(context, '/create_inspection'),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: _buildActionTile(
                              title: "Farmer Directory",
                              subtitle: "Search & view history",
                              icon: Icons.people_outline,
                              color: const Color(0xFF0284C7),
                              onTap: () => Navigator.pushNamed(context, '/farmers'),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: _buildActionTile(
                              title: "Verify QR Code",
                              subtitle: "Public report scan",
                              icon: Icons.qr_code_scanner,
                              color: const Color(0xFF7C3AED),
                              onTap: () => Navigator.pushNamed(context, '/qr_verification'),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 22),

                      // Recent Inspections Section
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            "Recent Inspections",
                            style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                          ),
                          TextButton(
                            onPressed: () => Navigator.pushNamed(context, '/history'),
                            child: const Text("View All", style: TextStyle(fontSize: 13)),
                          ),
                        ],
                      ),
                      if (inspections.isEmpty)
                        const Padding(
                          padding: EdgeInsets.symmetric(vertical: 24.0),
                          child: EmptyView(
                            title: "No Inspections Today",
                            message: "Start a new inspection to grade farmer lots with AI.",
                            icon: Icons.inventory_2_outlined,
                          ),
                        )
                      else
                        ListView.separated(
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          itemCount: inspections.take(5).length,
                          separatorBuilder: (_, __) => const SizedBox(height: 8),
                          itemBuilder: (ctx, index) {
                            final insp = inspections[index];
                            return _buildInspectionListTile(insp);
                          },
                        ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentTab,
        selectedItemColor: AppColors.primaryGreen,
        unselectedItemColor: AppColors.textMuted,
        type: BottomNavigationBarType.fixed,
        onTap: (index) {
          setState(() => _currentTab = index);
          if (index == 1) Navigator.pushNamed(context, '/history');
          if (index == 2) Navigator.pushNamed(context, '/qr_verification');
          if (index == 3) Navigator.pushNamed(context, '/settings');
        },
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: "Dashboard"),
          BottomNavigationBarItem(icon: Icon(Icons.history), label: "History"),
          BottomNavigationBarItem(icon: Icon(Icons.qr_code_scanner), label: "Verify QR"),
          BottomNavigationBarItem(icon: Icon(Icons.settings), label: "Settings"),
        ],
      ),
    );
  }

  Widget _buildMetricCard({
    required String title,
    required String value,
    required Color color,
    required Color bgColor,
    required IconData icon,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 10),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 22),
          const SizedBox(height: 6),
          Text(
            value,
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w900,
              color: color,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            title,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: color.withOpacity(0.9),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionTile({
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(10),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppColors.cardBorder),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.02),
              blurRadius: 4,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              radius: 18,
              backgroundColor: color.withOpacity(0.12),
              child: Icon(icon, color: color, size: 20),
            ),
            const SizedBox(height: 12),
            Text(
              title,
              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 2),
            Text(
              subtitle,
              style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInspectionListTile(insp) {
    Color badgeColor = AppColors.textMuted;
    Color badgeBg = Colors.grey.shade100;
    String label = insp.status;

    if (insp.lotDecision == 'ACCEPT_GRADE_A') {
      badgeColor = AppColors.gradeA;
      badgeBg = AppColors.gradeABg;
      label = "GRADE A (${insp.gradeAPercentage.toStringAsFixed(1)}%)";
    } else if (insp.lotDecision == 'ACCEPT_URS') {
      badgeColor = AppColors.gradeURS;
      badgeBg = AppColors.gradeURSBg;
      label = "URS (${insp.ursPercentage.toStringAsFixed(1)}%)";
    } else if (insp.lotDecision == 'REJECT_LOT') {
      badgeColor = AppColors.gradeReject;
      badgeBg = AppColors.gradeRejectBg;
      label = "REJECT (${insp.rejectPercentage.toStringAsFixed(1)}%)";
    }

    return Card(
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: AppColors.primaryGreen.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: const Icon(Icons.assessment_outlined, color: AppColors.primaryGreen),
        ),
        title: Text(
          insp.inspectionCode,
          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13.5),
        ),
        subtitle: Text(
          "Evaluated: ${insp.totalOnionsEvaluated} onions",
          style: const TextStyle(fontSize: 11.5, color: AppColors.textSecondary),
        ),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: badgeBg,
            borderRadius: BorderRadius.circular(6),
          ),
          child: Text(
            label,
            style: TextStyle(
              color: badgeColor,
              fontWeight: FontWeight.w700,
              fontSize: 11,
            ),
          ),
        ),
        onTap: () {
          Navigator.pushNamed(context, '/history');
        },
      ),
    );
  }
}
