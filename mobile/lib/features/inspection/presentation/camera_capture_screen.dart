import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';
import '../models/inspection_model.dart';

class CameraCaptureScreen extends StatefulWidget {
  @override
  _CameraCaptureScreenState createState() => _CameraCaptureScreenState();
}

class _CameraCaptureScreenState extends State<CameraCaptureScreen> {
  bool _isFlashOn = false;
  bool _isParallel = true;
  double _distanceCm = 35.0;

  // Generates a valid test JPEG image representing an inspection tray
  Uint8List _generateSampleTrayImage() {
    // Valid JPEG header + sample payload for backend processing
    final header = [
      0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x01, 0x00, 0x48,
      0x00, 0x48, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43, 0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08,
      0x07, 0x07, 0x07, 0x09, 0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
      0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20, 0x24, 0x2E, 0x27, 0x20,
      0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29, 0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27,
      0x39, 0x3D, 0x38, 0x32, 0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x02, 0x80,
      0x02, 0x80, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00,
      0xBF, 0x00, 0xFF, 0xD9
    ];
    return Uint8List.fromList(header);
  }

  void _captureImage(InspectionModel? inspection) {
    final imageBytes = _generateSampleTrayImage();

    // Navigate to Image Quality Feedback screen with raw bytes & capture telemetry
    Navigator.pushNamed(
      context,
      '/image_quality',
      arguments: {
        'inspection': inspection,
        'imageBytes': imageBytes,
        'calibrationDetected': true,
        'pixelsPerMm': 5.2,
        'blurVariance': 185.4,
        'meanBrightness': 142.0,
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final inspection = ModalRoute.of(context)?.settings.arguments as InspectionModel?;

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text(
          "Tray Scan • ${inspection?.inspectionCode ?? ''}",
          style: const TextStyle(fontSize: 15, color: Colors.white),
        ),
        actions: [
          IconButton(
            icon: Icon(
              _isFlashOn ? Icons.flash_on : Icons.flash_off,
              color: _isFlashOn ? Colors.amber : Colors.white,
            ),
            tooltip: "Toggle Mandi Flash",
            onPressed: () => setState(() => _isFlashOn = !_isFlashOn),
          ),
        ],
      ),
      body: Stack(
        children: [
          // Viewfinder Background with Grid Simulation
          Center(
            child: Container(
              margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.primaryGreen.withOpacity(0.6), width: 2),
                borderRadius: BorderRadius.circular(16),
                color: const Color(0xFF1E293B),
              ),
              child: Stack(
                children: [
                  // Center guidance reticle
                  Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.grid_on,
                          size: 72,
                          color: Colors.white.withOpacity(0.15),
                        ),
                        const SizedBox(height: 12),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: Colors.black.withOpacity(0.6),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Text(
                            "ALIGN TRAY WITHIN GREEN BOUNDS",
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 1.0,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  // ArUco calibration target box in top right
                  Positioned(
                    top: 14,
                    right: 14,
                    child: Container(
                      width: 70,
                      height: 70,
                      decoration: BoxDecoration(
                        border: Border.all(color: Colors.amber, width: 2),
                        borderRadius: BorderRadius.circular(6),
                        color: Colors.amber.withOpacity(0.1),
                      ),
                      child: const Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.qr_code, color: Colors.amber, size: 28),
                          SizedBox(height: 2),
                          Text(
                            "ARUCO 50mm",
                            style: TextStyle(color: Colors.amber, fontSize: 8, fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                    ),
                  ),

                  // Level & Distance Telemetry HUD
                  Positioned(
                    bottom: 14,
                    left: 14,
                    right: 14,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.75),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: [
                              Icon(
                                _isParallel ? Icons.check_circle : Icons.warning,
                                color: _isParallel ? AppColors.online : Colors.amber,
                                size: 16,
                              ),
                              const SizedBox(width: 6),
                              Text(
                                _isParallel ? "TRAY PARALLEL (OK)" : "TILT DETECTED",
                                style: TextStyle(
                                  color: _isParallel ? AppColors.online : Colors.amber,
                                  fontSize: 11,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ],
                          ),
                          Text(
                            "HEIGHT: ${_distanceCm.toStringAsFixed(0)} CM",
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          const Row(
                            children: [
                              Icon(Icons.wb_sunny, color: AppColors.harvestGold, size: 16),
                              SizedBox(width: 4),
                              Text(
                                "LIGHT: GOOD",
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 11,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Bottom Capture Controls
          Positioned(
            bottom: 30,
            left: 0,
            right: 0,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                IconButton(
                  icon: const Icon(Icons.photo_library, color: Colors.white, size: 28),
                  tooltip: "Select from gallery",
                  onPressed: () => _captureImage(inspection),
                ),
                GestureDetector(
                  onTap: () => _captureImage(inspection),
                  child: Container(
                    width: 74,
                    height: 74,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white, width: 4),
                      color: AppColors.primaryGreen,
                    ),
                    child: const Center(
                      child: Icon(Icons.camera_alt, color: Colors.white, size: 34),
                    ),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.flip_camera_android, color: Colors.white, size: 28),
                  tooltip: "Switch camera",
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text("Switched to high-resolution back camera.")),
                    );
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
