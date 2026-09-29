import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/state_views.dart';
import '../../../core/widgets/sync_status_badge.dart';
import '../../../core/storage/sync_queue_manager.dart';
import '../../inspection/repository/inspection_repository.dart';
import '../../inspection/models/inspection_model.dart';

class InspectionHistoryScreen extends StatefulWidget {
  @override
  _InspectionHistoryScreenState createState() => _InspectionHistoryScreenState();
}

class _InspectionHistoryScreenState extends State<InspectionHistoryScreen> {
  final _searchController = TextEditingController();
  String _filter = "ALL";
  String _query = "";

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<InspectionRepository>().fetchInspections();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final inspRepo = context.watch<InspectionRepository>();
    final allInspections = inspRepo.inspections;

    final filtered = allInspections.where((i) {
      if (_filter == "COMPLETED" && i.status != "COMPLETED") return false;
      if (_filter == "REVIEW" && i.status != "REVIEW_REQUIRED") return false;
      if (_query.isNotEmpty) {
        final q = _query.toLowerCase();
        return i.inspectionCode.toLowerCase().contains(q) ||
            i.lotId.toLowerCase().contains(q);
      }
      return true;
    }).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text("Inspection History & Records"),
      ),
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(12.0),
              child: TextField(
                controller: _searchController,
                onChanged: (val) => setState(() => _query = val.trim()),
                decoration: InputDecoration(
                  hintText: "Search by inspection code or lot ID...",
                  prefixIcon: const Icon(Icons.search),
                  suffixIcon: _query.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear),
                          onPressed: () {
                            _searchController.clear();
                            setState(() => _query = "");
                          },
                        )
                      : null,
                ),
              ),
            ),

            // Filter Chips
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12.0),
              child: Row(
                children: [
                  ChoiceChip(
                    label: const Text("All Records"),
                    selected: _filter == "ALL",
                    onSelected: (_) => setState(() => _filter = "ALL"),
                  ),
                  const SizedBox(width: 8),
                  ChoiceChip(
                    label: const Text("Completed"),
                    selected: _filter == "COMPLETED",
                    onSelected: (_) => setState(() => _filter = "COMPLETED"),
                  ),
                  const SizedBox(width: 8),
                  ChoiceChip(
                    label: const Text("Review Required"),
                    selected: _filter == "REVIEW",
                    onSelected: (_) => setState(() => _filter = "REVIEW"),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 8),

            Expanded(
              child: inspRepo.isLoading
                  ? const LoadingView(message: "Loading inspection archive...")
                  : inspRepo.errorMessage != null && allInspections.isEmpty
                      ? ErrorView(
                          message: inspRepo.errorMessage!,
                          onRetry: () => inspRepo.fetchInspections(),
                        )
                      : filtered.isEmpty
                          ? const EmptyView(
                              title: "No Inspections Found",
                              message: "No matching inspection records found in history.",
                              icon: Icons.history,
                            )
                          : ListView.separated(
                              padding: const EdgeInsets.all(12),
                              itemCount: filtered.length,
                              separatorBuilder: (_, __) => const SizedBox(height: 8),
                              itemBuilder: (ctx, index) {
                                final insp = filtered[index];
                                return _buildHistoryCard(insp);
                              },
                            ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHistoryCard(InspectionModel insp) {
    Color badgeColor = AppColors.textMuted;
    Color badgeBg = Colors.grey.shade100;
    String decisionLabel = insp.status;

    if (insp.lotDecision == 'ACCEPT_GRADE_A') {
      badgeColor = AppColors.gradeA;
      badgeBg = AppColors.gradeABg;
      decisionLabel = "GRADE A (${insp.gradeAPercentage.toStringAsFixed(0)}%)";
    } else if (insp.lotDecision == 'ACCEPT_URS') {
      badgeColor = AppColors.gradeURS;
      badgeBg = AppColors.gradeURSBg;
      decisionLabel = "URS (${insp.ursPercentage.toStringAsFixed(0)}%)";
    } else if (insp.lotDecision == 'REJECT_LOT') {
      badgeColor = AppColors.gradeReject;
      badgeBg = AppColors.gradeRejectBg;
      decisionLabel = "REJECT";
    }

    final dateFormatted = DateFormat("dd MMM yyyy, HH:mm").format(insp.createdAt);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    insp.inspectionCode,
                    style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 14),
                  ),
                ),
                _buildSyncBadgeForInspection(insp),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: badgeBg,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    decisionLabel,
                    style: TextStyle(
                      color: badgeColor,
                      fontWeight: FontWeight.w700,
                      fontSize: 11,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              "Date: $dateFormatted • Sample: ${insp.totalOnionsEvaluated} / ${insp.sampleSize} onions",
              style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
            ),
            if (insp.decisionReason != null) ...[
              const SizedBox(height: 6),
              Text(
                insp.decisionReason!,
                style: const TextStyle(fontSize: 12, color: AppColors.textPrimary, fontStyle: FontStyle.italic),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildSyncBadgeForInspection(InspectionModel insp) {
    final syncManager = context.watch<SyncQueueManager>();
    final match = syncManager.queue.where((i) => i.entityId == insp.id).toList();

    SyncStatus status = SyncStatus.synced;
    if (match.isNotEmpty) {
      status = match.last.status;
    }

    return SyncStatusBadge(
      status: status,
      onRetry: () => syncManager.syncPendingBatch(),
      onAction: () {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Inspection ${insp.inspectionCode} requires supervisor review before sync.")),
        );
      },
    );
  }
}
