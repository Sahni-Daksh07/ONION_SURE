import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../auth/repository/auth_repository.dart';
import '../../inspection/models/inspection_model.dart';
import '../../inspection/repository/inspection_repository.dart';

class ManualReviewScreen extends StatefulWidget {
  @override
  _ManualReviewScreenState createState() => _ManualReviewScreenState();
}

class _ManualReviewScreenState extends State<ManualReviewScreen> {
  String _reviewedGrade = "URS";
  String _selectedReason = "Surface mud mistakenly classified as rot";
  final _commentsController = TextEditingController();
  bool _isSubmitting = false;

  final List<String> _reasonOptions = [
    "Surface mud mistakenly classified as rot",
    "Minor peel blemish does not affect internal flesh",
    "Borderline diameter confirmed acceptable by manual caliper",
    "Skin discoloration within permissible DoCA allowance",
    "Physical tactile inspection confirms firmness",
  ];

  @override
  void dispose() {
    _commentsController.dispose();
    super.dispose();
  }

  Future<void> _handleSubmitReview(InspectionModel? inspection, GradeResultModel? result) async {
    if (inspection == null || result == null) return;
    final user = context.read<AuthRepository>().currentUser;

    setState(() => _isSubmitting = true);

    try {
      final inspRepo = context.read<InspectionRepository>();
      await inspRepo.submitManualReview(
        inspectionId: inspection.id,
        gradeResultId: result.id,
        reviewerId: user?.id ?? "reviewer",
        reviewedGrade: _reviewedGrade,
        reason: _selectedReason,
        comments: _commentsController.text.trim(),
      );

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Manual review override logged to audit trail.")),
      );
      Navigator.pop(context);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Review Error: $e")),
      );
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final args = ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>?;
    final inspection = args?['inspection'] as InspectionModel?;
    final gradeResult = args?['gradeResult'] as GradeResultModel?;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Supervisor Manual Review"),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // AI Detection Info Card
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "AI Automated Classification",
                        style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text("Original AI Grade:"),
                          Text(
                            gradeResult?.grade ?? "REJECT",
                            style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.gradeReject),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text("Defect Class:"),
                          Text(
                            gradeResult?.defectClass ?? "ROTTEN",
                            style: const TextStyle(fontWeight: FontWeight.w600),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text("Measured Diameter:"),
                          Text(
                            gradeResult?.diameterMm != null ? "${gradeResult!.diameterMm} mm" : "N/A",
                            style: const TextStyle(fontWeight: FontWeight.w600),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Override Form
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "Supervisor Override",
                        style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        value: _reviewedGrade,
                        decoration: const InputDecoration(labelText: "New Certified Grade *"),
                        items: const [
                          DropdownMenuItem(value: "GRADE_A", child: Text("GRADE A (Prime)")),
                          DropdownMenuItem(value: "URS", child: Text("URS (Under-Grade)")),
                          DropdownMenuItem(value: "REJECT", child: Text("REJECT (Confirmed Defect)")),
                        ],
                        onChanged: (val) => setState(() => _reviewedGrade = val ?? "URS"),
                      ),
                      const SizedBox(height: 14),
                      DropdownButtonFormField<String>(
                        value: _selectedReason,
                        decoration: const InputDecoration(labelText: "Mandatory Audit Reason *"),
                        isExpanded: true,
                        items: _reasonOptions.map((r) {
                          return DropdownMenuItem(value: r, child: Text(r, overflow: TextOverflow.ellipsis));
                        }).toList(),
                        onChanged: (val) => setState(() => _selectedReason = val ?? _reasonOptions.first),
                      ),
                      const SizedBox(height: 14),
                      TextField(
                        controller: _commentsController,
                        maxLines: 3,
                        decoration: const InputDecoration(
                          labelText: "Supervisor Comments (Optional)",
                          hintText: "Add specific notes regarding sample condition...",
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              ElevatedButton.icon(
                onPressed: _isSubmitting ? null : () => _handleSubmitReview(inspection, gradeResult),
                icon: const Icon(Icons.check_circle_outline),
                label: _isSubmitting
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text("SUBMIT AUDITABLE OVERRIDE"),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
