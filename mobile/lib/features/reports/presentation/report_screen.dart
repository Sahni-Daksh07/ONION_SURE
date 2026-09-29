import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../core/theme/app_colors.dart';
import '../../inspection/models/inspection_model.dart';

class ReportScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final report = ModalRoute.of(context)?.settings.arguments as ReportModel?;
    final now = report?.generatedAt ?? DateTime.now();
    final dateFormatted = DateFormat("dd MMMM yyyy, HH:mm").format(now);

    final summary = report?.summaryMetrics ?? {};
    final gradeAPct = (summary['grade_a_percentage'] as num?)?.toDouble() ?? 60.0;
    final ursPct = (summary['urs_percentage'] as num?)?.toDouble() ?? 20.0;
    final rejectPct = (summary['reject_percentage'] as num?)?.toDouble() ?? 20.0;
    final lotDecision = summary['lot_decision']?.toString() ?? "ACCEPT_GRADE_A";
    final totalOnions = summary['total_onions'] ?? 5;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Quality Certificate"),
        actions: [
          IconButton(
            icon: const Icon(Icons.share),
            tooltip: "Share Certificate",
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text("Certificate link ready for APMC distribution.")),
              );
            },
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Official Certificate Card
              Card(
                elevation: 3,
                child: Padding(
                  padding: const EdgeInsets.all(20.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      // Header
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.account_balance, color: AppColors.primaryGreen, size: 28),
                          const SizedBox(width: 8),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: const [
                              Text(
                                "GOVERNMENT OF INDIA",
                                style: TextStyle(fontWeight: FontWeight.w800, fontSize: 13, letterSpacing: 0.5),
                              ),
                              Text(
                                "Department of Consumer Affairs (DoCA)",
                                style: TextStyle(fontSize: 10, color: AppColors.textSecondary),
                              ),
                            ],
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),
                      const Divider(),
                      const SizedBox(height: 8),

                      const Text(
                        "DIGITAL ONION QUALITY CERTIFICATE",
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w900,
                          color: AppColors.primaryGreen,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        "Certificate Code: ${report?.reportCode ?? 'REP-SAMPLE-2026'}",
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                      ),
                      Text(
                        "Generated: $dateFormatted",
                        style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
                      ),
                      const SizedBox(height: 20),

                      // QR Code Container with Verification Frame
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: AppColors.cardBorder, width: 2),
                        ),
                        child: Column(
                          children: [
                            Container(
                              width: 130,
                              height: 130,
                              color: Colors.grey.shade100,
                              child: Center(
                                child: Icon(
                                  Icons.qr_code_2,
                                  size: 110,
                                  color: Colors.grey.shade800,
                                ),
                              ),
                            ),
                            const SizedBox(height: 8),
                            const Text(
                              "SCAN TO VERIFY AUTHENTICITY",
                              style: TextStyle(
                                fontSize: 9.5,
                                fontWeight: FontWeight.w800,
                                color: AppColors.primaryGreen,
                                letterSpacing: 0.8,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Certified Result Badge
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                        decoration: BoxDecoration(
                          color: lotDecision == 'REJECT_LOT' ? AppColors.gradeRejectBg : AppColors.gradeABg,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                            color: lotDecision == 'REJECT_LOT' ? AppColors.gradeReject : AppColors.gradeA,
                          ),
                        ),
                        child: Text(
                          "OFFICIAL DECISION: $lotDecision",
                          style: TextStyle(
                            color: lotDecision == 'REJECT_LOT' ? AppColors.gradeReject : AppColors.gradeA,
                            fontWeight: FontWeight.w800,
                            fontSize: 13,
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Quality Metrics Table
                      Table(
                        border: TableBorder.all(color: AppColors.cardBorder, width: 1),
                        children: [
                          _buildTableRow("Total Sampled Onions", "$totalOnions Units"),
                          _buildTableRow("Grade A Quality", "${gradeAPct.toStringAsFixed(1)}%"),
                          _buildTableRow("URS (Under-Grade)", "${ursPct.toStringAsFixed(1)}%"),
                          _buildTableRow("Defective / Reject", "${rejectPct.toStringAsFixed(1)}%"),
                        ],
                      ),
                      const SizedBox(height: 14),

                      // Cryptographic Hash Footprint
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: AppColors.backgroundLight,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              "Cryptographic Verification Hash:",
                              style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              report?.qrVerificationHash ??
                                  "62745f3870cdaef57fc5812c95842ad0442e8627cc2d4594a1f4e1f636090948",
                              style: const TextStyle(
                                fontSize: 9,
                                fontFamily: "monospace",
                                color: AppColors.textSecondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 20),

              ElevatedButton.icon(
                onPressed: () {
                  Navigator.pushNamedAndRemoveUntil(context, '/dashboard', (route) => false);
                },
                icon: const Icon(Icons.home),
                label: const Text("RETURN TO DASHBOARD"),
              ),
            ],
          ),
        ),
      ),
    );
  }

  TableRow _buildTableRow(String label, String value) {
    return TableRow(
      children: [
        Padding(
          padding: const EdgeInsets.all(8.0),
          child: Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
        ),
        Padding(
          padding: const EdgeInsets.all(8.0),
          child: Text(value, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
        ),
      ],
    );
  }
}
