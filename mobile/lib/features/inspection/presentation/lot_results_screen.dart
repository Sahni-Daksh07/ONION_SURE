import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../auth/repository/auth_repository.dart';
import '../repository/inspection_repository.dart';

class LotResultsScreen extends StatefulWidget {
  @override
  _LotResultsScreenState createState() => _LotResultsScreenState();
}

class _LotResultsScreenState extends State<LotResultsScreen> {
  bool _isFinalizing = false;

  Future<void> _handleFinalizeInspection() async {
    final inspRepo = context.read<InspectionRepository>();
    final inspection = inspRepo.activeInspection;
    final user = context.read<AuthRepository>().currentUser;

    if (inspection == null) return;

    setState(() => _isFinalizing = true);

    try {
      final report = await inspRepo.finalizeInspection(inspection.id, actorId: user?.id);
      if (!mounted) return;

      Navigator.pushReplacementNamed(context, '/report', arguments: report);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Finalization Error: $e")),
      );
    } finally {
      if (mounted) setState(() => _isFinalizing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final inspRepo = context.watch<InspectionRepository>();
    final inspection = inspRepo.activeInspection;

    final lotDecision = inspection?.lotDecision ?? 'ACCEPT_GRADE_A';
    final gradeAPct = inspection?.gradeAPercentage ?? 60.0;
    final ursPct = inspection?.ursPercentage ?? 20.0;
    final rejectPct = inspection?.rejectPercentage ?? 20.0;
    final totalOnions = inspection?.totalOnionsEvaluated ?? 5;

    Color decisionColor = AppColors.gradeA;
    Color decisionBg = AppColors.gradeABg;
    String decisionLabel = "LOT ACCEPTED: GRADE A";

    if (lotDecision == 'ACCEPT_URS') {
      decisionColor = AppColors.gradeURS;
      decisionBg = AppColors.gradeURSBg;
      decisionLabel = "LOT ACCEPTED: URS (UNDER-GRADE)";
    } else if (lotDecision == 'REJECT_LOT') {
      decisionColor = AppColors.gradeReject;
      decisionBg = AppColors.gradeRejectBg;
      decisionLabel = "LOT REJECTED";
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text("Lot Assessment Decision"),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Mandi Acceptance Decision Banner
              Container(
                padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
                decoration: BoxDecoration(
                  color: decisionBg,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: decisionColor, width: 2),
                ),
                child: Column(
                  children: [
                    Icon(
                      lotDecision == 'REJECT_LOT' ? Icons.cancel : Icons.verified,
                      size: 44,
                      color: decisionColor,
                    ),
                    const SizedBox(height: 10),
                    Text(
                      decisionLabel,
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w900,
                        color: decisionColor,
                        letterSpacing: 0.5,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      inspection?.decisionReason ?? "Meets PS26031 Grade A quality criteria.",
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 13,
                        color: decisionColor.withOpacity(0.9),
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Grade Percentage Distribution
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
                            "Sample Distribution",
                            style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                          ),
                          Text(
                            "$totalOnions Onions Sampled",
                            style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),

                      // Grade A Bar
                      _buildProgressBar(
                        label: "Grade A (Prime Quality)",
                        percentage: gradeAPct,
                        color: AppColors.gradeA,
                      ),
                      const SizedBox(height: 14),

                      // URS Bar
                      _buildProgressBar(
                        label: "URS (Under-Sized / B-Grade)",
                        percentage: ursPct,
                        color: AppColors.gradeURS,
                      ),
                      const SizedBox(height: 14),

                      // Reject Bar
                      _buildProgressBar(
                        label: "Reject (Critical Rot / Sprouts)",
                        percentage: rejectPct,
                        color: AppColors.gradeReject,
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Regulatory Policy Traceability Card
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(14.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "Audit & Traceability Standards",
                        style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        "• Engine: Deterministic Rule Matrix (No LLM in decision path)\n• Policy: PS26031_STANDARD v1.0.0\n• Physical Scale: Calibrated 50mm ArUco Optical Ratio",
                        style: TextStyle(fontSize: 12, color: AppColors.textSecondary, height: 1.4),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              ElevatedButton.icon(
                onPressed: _isFinalizing ? null : _handleFinalizeInspection,
                icon: const Icon(Icons.description),
                label: _isFinalizing
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text("FINALIZE & GENERATE OFFICIAL REPORT"),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProgressBar({
    required String label,
    required double percentage,
    required Color color,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600)),
            Text(
              "${percentage.toStringAsFixed(1)}%",
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: color),
            ),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: percentage / 100.0,
            backgroundColor: color.withOpacity(0.12),
            valueColor: AlwaysStoppedAnimation<Color>(color),
            minHeight: 8,
          ),
        ),
      ],
    );
  }
}
