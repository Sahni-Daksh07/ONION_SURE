import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_colors.dart';
import '../models/inspection_model.dart';
import '../repository/inspection_repository.dart';

class OnionResultsScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final inspRepo = context.watch<InspectionRepository>();
    final inspection = inspRepo.activeInspection;
    final gradeResults = inspRepo.activeGradeResults;

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text("Onion-Level Evaluation", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            Text(
              "Session: ${inspection?.inspectionCode ?? ''}",
              style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.85)),
            ),
          ],
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              color: Colors.white,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    "Total Detected: ${gradeResults.length} onions",
                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
                  ),
                  Text(
                    "Policy: PS26031 Standard",
                    style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: ListView.separated(
                padding: const EdgeInsets.all(12),
                itemCount: gradeResults.length,
                separatorBuilder: (_, __) => const SizedBox(height: 8),
                itemBuilder: (ctx, index) {
                  final result = gradeResults[index];
                  return _buildOnionCard(context, result, index + 1, inspection);
                },
              ),
            ),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.05),
                    blurRadius: 6,
                    offset: const Offset(0, -2),
                  ),
                ],
              ),
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pushNamed(context, '/lot_results');
                },
                icon: const Icon(Icons.analytics_outlined),
                label: const Text("VIEW AGGREGATED LOT RESULTS"),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOnionCard(
    BuildContext context,
    GradeResultModel result,
    int index,
    InspectionModel? inspection,
  ) {
    Color badgeColor = AppColors.textMuted;
    Color badgeBg = Colors.grey.shade100;

    switch (result.grade) {
      case 'GRADE_A':
        badgeColor = AppColors.gradeA;
        badgeBg = AppColors.gradeABg;
        break;
      case 'URS':
        badgeColor = AppColors.gradeURS;
        badgeBg = AppColors.gradeURSBg;
        break;
      case 'REJECT':
        badgeColor = AppColors.gradeReject;
        badgeBg = AppColors.gradeRejectBg;
        break;
      default:
        badgeColor = AppColors.gradeReview;
        badgeBg = AppColors.gradeReviewBg;
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: AppColors.primaryGreen.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Center(
                child: Text(
                  "#$index",
                  style: const TextStyle(
                    fontWeight: FontWeight.w800,
                    color: AppColors.primaryGreen,
                    fontSize: 14,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        result.defectClass ?? "EVALUATED",
                        style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: badgeBg,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          result.grade,
                          style: TextStyle(
                            color: badgeColor,
                            fontWeight: FontWeight.w800,
                            fontSize: 11,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Text(
                        "Diameter: ${result.diameterMm != null ? '${result.diameterMm!.toStringAsFixed(1)} mm' : 'N/A'}",
                        style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                      ),
                      const SizedBox(width: 10),
                      Text(
                        "Conf: ${(result.confidence * 100).toStringAsFixed(0)}%",
                        style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                      ),
                    ],
                  ),
                  if (result.reasonCodes.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(
                      "Reason: ${result.reasonCodes.join(', ')}",
                      style: const TextStyle(fontSize: 11, color: AppColors.textMuted, fontStyle: FontStyle.italic),
                    ),
                  ],
                ],
              ),
            ),
            if (result.grade == 'REJECT' || result.requiresReview)
              IconButton(
                icon: const Icon(Icons.rate_review_outlined, color: AppColors.harvestAmber, size: 20),
                tooltip: "Supervisor Manual Review",
                onPressed: () {
                  Navigator.pushNamed(
                    context,
                    '/manual_review',
                    arguments: {
                      'inspection': inspection,
                      'gradeResult': result,
                    },
                  );
                },
              ),
          ],
        ),
      ),
    );
  }
}
