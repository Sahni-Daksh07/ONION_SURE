import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';
import '../models/inspection_model.dart';

class ImageQualityScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final args = ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>?;

    final inspection = args?['inspection'] as InspectionModel?;
    final imageBytes = args?['imageBytes'] as Uint8List?;
    final calibrationDetected = args?['calibrationDetected'] as bool? ?? true;
    final pixelsPerMm = args?['pixelsPerMm'] as double? ?? 5.2;
    final blurVariance = args?['blurVariance'] as double? ?? 185.4;
    final meanBrightness = args?['meanBrightness'] as double? ?? 142.0;

    final isBlurPassed = blurVariance >= 100.0;
    final isBrightnessPassed = meanBrightness >= 40.0 && meanBrightness <= 220.0;
    final allPassed = isBlurPassed && isBrightnessPassed && calibrationDetected;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Optical Quality Verification"),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Preview Frame
              Container(
                height: 190,
                decoration: BoxDecoration(
                  color: const Color(0xFF1E293B),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: allPassed ? AppColors.gradeA : AppColors.gradeReject,
                    width: 2,
                  ),
                ),
                child: Stack(
                  children: [
                    Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            allPassed ? Icons.check_circle : Icons.warning,
                            size: 48,
                            color: allPassed ? AppColors.gradeA : AppColors.gradeReject,
                          ),
                          const SizedBox(height: 8),
                          Text(
                            allPassed ? "IMAGE VALIDATED FOR AI INFERENCE" : "QUALITY CHECK FAILED",
                            style: TextStyle(
                              color: allPassed ? AppColors.gradeA : AppColors.gradeReject,
                              fontWeight: FontWeight.w800,
                              fontSize: 13,
                              letterSpacing: 0.5,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Positioned(
                      top: 10,
                      left: 10,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.black.withOpacity(0.6),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          inspection?.inspectionCode ?? "ACTIVE INSPECTION",
                          style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              const Text(
                "Automated Pre-Inference Checks",
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 10),

              // Checklist Cards
              _buildQualityRow(
                title: "Sharpness / Blur Variance",
                subtitle: "Threshold: >100.0 (Measured: ${blurVariance.toStringAsFixed(1)})",
                isPassed: isBlurPassed,
              ),
              const SizedBox(height: 8),

              _buildQualityRow(
                title: "Lighting & Exposure Level",
                subtitle: "Range: 40-220 (Measured: ${meanBrightness.toStringAsFixed(0)} / 255)",
                isPassed: isBrightnessPassed,
              ),
              const SizedBox(height: 8),

              _buildQualityRow(
                title: "Physical Calibration Reference",
                subtitle: calibrationDetected
                    ? "ArUco 50mm marker detected (${pixelsPerMm.toStringAsFixed(2)} px/mm)"
                    : "No reference marker detected (Physical measurements disabled)",
                isPassed: calibrationDetected,
              ),
              const SizedBox(height: 24),

              // Actions
              ElevatedButton.icon(
                onPressed: allPassed
                    ? () {
                        Navigator.pushReplacementNamed(
                          context,
                          '/ai_processing',
                          arguments: {
                            'inspection': inspection,
                            'imageBytes': imageBytes,
                            'calibrationDetected': calibrationDetected,
                            'pixelsPerMm': pixelsPerMm,
                          },
                        );
                      }
                    : null,
                icon: const Icon(Icons.psychology),
                label: const Text("PROCEED TO AI QUALITY ASSESSMENT"),
              ),
              const SizedBox(height: 10),

              OutlinedButton.icon(
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.replay),
                label: const Text("RETAKE TRAY IMAGE"),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildQualityRow({
    required String title,
    required String subtitle,
    required bool isPassed,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        child: Row(
          children: [
            CircleAvatar(
              radius: 14,
              backgroundColor: isPassed ? AppColors.gradeABg : AppColors.gradeRejectBg,
              child: Icon(
                isPassed ? Icons.check : Icons.close,
                color: isPassed ? AppColors.gradeA : AppColors.gradeReject,
                size: 16,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13.5),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: const TextStyle(fontSize: 11.5, color: AppColors.textSecondary),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
