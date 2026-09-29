import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';
import '../models/inspection_model.dart';

class SamplingGuidanceScreen extends StatefulWidget {
  @override
  _SamplingGuidanceScreenState createState() => _SamplingGuidanceScreenState();
}

class _SamplingGuidanceScreenState extends State<SamplingGuidanceScreen> {
  bool _step1Sampled = false;
  bool _step2Spread = false;
  bool _step3ReferencePlaced = false;

  @override
  Widget build(BuildContext context) {
    final inspection = ModalRoute.of(context)?.settings.arguments as InspectionModel?;
    final canProceed = _step1Sampled && _step2Spread && _step3ReferencePlaced;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Sampling Protocol (PS26031)"),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppColors.harvestAmber.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: AppColors.harvestAmber.withOpacity(0.3)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.info_outline, color: AppColors.harvestAmber, size: 24),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            "DoCA Standard Mandi Sampling",
                            style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13.5),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            "Inspection: ${inspection?.inspectionCode ?? 'Active Inspection'}\nTarget: ${inspection?.sampleSize ?? 50} onions",
                            style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              const Text(
                "Operational Checklist Before Scan",
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 10),

              _buildCheckTile(
                title: "1. Three-Tier Sack Sampling",
                subtitle: "Extract onions from top, middle, and bottom of selected lot bags to prevent sorting bias.",
                value: _step1Sampled,
                onChanged: (val) => setState(() => _step1Sampled = val ?? false),
              ),
              const SizedBox(height: 10),

              _buildCheckTile(
                title: "2. Single-Layer Spread on Inspection Tray",
                subtitle: "Spread sample onions on a non-reflective matte tray with minimum 1cm spacing between bulbs (no stacking).",
                value: _step2Spread,
                onChanged: (val) => setState(() => _step2Spread = val ?? false),
              ),
              const SizedBox(height: 10),

              _buildCheckTile(
                title: "3. Calibration Reference Placement",
                subtitle: "Place the official 50mm ArUco marker or reference calibration disc in the top-right corner of the tray.",
                value: _step3ReferencePlaced,
                onChanged: (val) => setState(() => _step3ReferencePlaced = val ?? false),
              ),
              const SizedBox(height: 24),

              ElevatedButton.icon(
                onPressed: canProceed
                    ? () {
                        Navigator.pushNamed(context, '/camera', arguments: inspection);
                      }
                    : null,
                icon: const Icon(Icons.camera_alt),
                label: const Text("OPEN GUIDED SCAN CAMERA"),
              ),
              if (!canProceed)
                const Padding(
                  padding: EdgeInsets.only(top: 8.0),
                  child: Text(
                    "Please confirm all 3 mandatory sampling checklist items above to open the camera.",
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 12, color: AppColors.textMuted),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCheckTile({
    required String title,
    required String subtitle,
    required bool value,
    required ValueChanged<bool?> onChanged,
  }) {
    return Card(
      child: CheckboxListTile(
        value: value,
        onChanged: onChanged,
        activeColor: AppColors.primaryGreen,
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13.5)),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 4.0),
          child: Text(subtitle, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
        ),
      ),
    );
  }
}
