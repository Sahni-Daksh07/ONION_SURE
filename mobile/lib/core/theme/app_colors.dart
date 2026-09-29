import 'package:flutter/material.dart';

/// App color system specifically designed for outdoor/mandi field readability.
class AppColors {
  // Brand Colors - Government / APMC Mandi identity
  static const Color primaryGreen = Color(0xFF1B5E20);
  static const Color primaryGreenLight = Color(0xFF2E7D32);
  static const Color primaryGreenDark = Color(0xFF0D3311);

  static const Color harvestAmber = Color(0xFFD97706);
  static const Color harvestGold = Color(0xFFF59E0B);
  static const Color onionRed = Color(0xFF991B1B);

  // Quality Grading Badges (PS26031 Standard)
  static const Color gradeA = Color(0xFF059669); // Emerald - High Quality
  static const Color gradeABg = Color(0xFFD1FAE5);
  static const Color gradeURS = Color(0xFFD97706); // Amber - Under-grade / Secondary
  static const Color gradeURSBg = Color(0xFFFEF3C7);
  static const Color gradeReject = Color(0xFFDC2626); // Crimson - Critical defect
  static const Color gradeRejectBg = Color(0xFFFEE2E2);
  static const Color gradeReview = Color(0xFF7C3AED); // Purple - Needs manual review
  static const Color gradeReviewBg = Color(0xFFEDE9FE);

  // Surface & Neutrals
  static const Color backgroundLight = Color(0xFFF1F5F9);
  static const Color surfaceWhite = Color(0xFFFFFFFF);
  static const Color cardBorder = Color(0xFFE2E8F0);
  static const Color textPrimary = Color(0xFF0F172A);
  static const Color textSecondary = Color(0xFF475569);
  static const Color textMuted = Color(0xFF94A3B8);

  // Operational States
  static const Color online = Color(0xFF10B981);
  static const Color offline = Color(0xFF64748B);
  static const Color syncPending = Color(0xFFEAB308);
}
