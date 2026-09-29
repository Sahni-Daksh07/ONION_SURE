import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../inspection/repository/inspection_repository.dart';

class QrVerificationScreen extends StatefulWidget {
  @override
  _QrVerificationScreenState createState() => _QrVerificationScreenState();
}

class _QrVerificationScreenState extends State<QrVerificationScreen> {
  final _hashController = TextEditingController();
  bool _isVerifying = false;
  Map<String, dynamic>? _verificationResult;
  String? _error;

  @override
  void dispose() {
    _hashController.dispose();
    super.dispose();
  }

  Future<void> _verifyHash(String hash) async {
    final cleanHash = hash.trim();
    if (cleanHash.isEmpty) {
      setState(() => _error = "Please enter or scan a valid report verification hash.");
      return;
    }

    setState(() {
      _isVerifying = true;
      _error = null;
      _verificationResult = null;
    });

    try {
      final inspRepo = context.read<InspectionRepository>();
      final result = await inspRepo.verifyReportQr(cleanHash);
      if (!mounted) return;
      setState(() => _verificationResult = result);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = "Verification Failed: Certificate not found or hash is invalid.");
    } finally {
      if (mounted) setState(() => _isVerifying = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Public QR Verification"),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Scanner Visual Guidance
              Container(
                height: 180,
                decoration: BoxDecoration(
                  color: const Color(0xFF0F172A),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.primaryGreen, width: 2),
                ),
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.qr_code_scanner, size: 54, color: Colors.white.withOpacity(0.8)),
                      const SizedBox(height: 10),
                      const Text(
                        "POINT CAMERA AT CERTIFICATE QR CODE",
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 0.8,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        "Instant anti-counterfeit verification via DoCA registry",
                        style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 11),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Manual Hash Entry Card
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const Text(
                        "Manual Verification Hash",
                        style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(height: 10),
                      TextField(
                        controller: _hashController,
                        decoration: const InputDecoration(
                          hintText: "Enter 64-character SHA-256 hash...",
                          prefixIcon: Icon(Icons.tag),
                        ),
                      ),
                      const SizedBox(height: 12),
                      ElevatedButton(
                        onPressed: _isVerifying
                            ? null
                            : () => _verifyHash(_hashController.text),
                        child: _isVerifying
                            ? const CircularProgressIndicator(color: Colors.white)
                            : const Text("VERIFY AUTHENTICITY"),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Error State
              if (_error != null)
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppColors.gradeRejectBg,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppColors.gradeReject.withOpacity(0.3)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline, color: AppColors.gradeReject, size: 24),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          _error!,
                          style: const TextStyle(color: AppColors.gradeReject, fontSize: 13, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                ),

              // Verified Certificate Card
              if (_verificationResult != null) ...[
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.gradeABg,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppColors.gradeA, width: 2),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: const [
                          Icon(Icons.verified, color: AppColors.gradeA, size: 28),
                          SizedBox(width: 8),
                          Text(
                            "CERTIFIED AUTHENTIC REPORT",
                            style: TextStyle(
                              color: AppColors.gradeA,
                              fontWeight: FontWeight.w900,
                              fontSize: 14.5,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Text(
                        "Report Code: ${_verificationResult!['report_code'] ?? 'N/A'}",
                        style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        "Status: ${_verificationResult!['is_valid'] == true ? 'Valid & Cryptographically Verified' : 'Invalid'}",
                        style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        "Inspection Reference: ${_verificationResult!['inspection_code'] ?? 'N/A'}",
                        style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
