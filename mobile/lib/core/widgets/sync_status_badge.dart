import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../storage/sync_queue_manager.dart';

class SyncStatusBadge extends StatelessWidget {
  final SyncStatus status;
  final VoidCallback? onRetry;
  final VoidCallback? onAction;

  const SyncStatusBadge({
    required this.status,
    this.onRetry,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color fg;
    IconData icon;
    String text = status.label;

    switch (status) {
      case SyncStatus.synced:
        bg = AppColors.gradeABg;
        fg = AppColors.gradeA;
        icon = Icons.cloud_done;
        break;
      case SyncStatus.pending:
        bg = AppColors.gradeURSBg;
        fg = AppColors.gradeURS;
        icon = Icons.cloud_upload_outlined;
        break;
      case SyncStatus.syncing:
        bg = const Color(0xFFE0F2FE);
        fg = const Color(0xFF0284C7);
        icon = Icons.sync;
        break;
      case SyncStatus.failed:
        bg = AppColors.gradeRejectBg;
        fg = AppColors.gradeReject;
        icon = Icons.cloud_off;
        break;
      case SyncStatus.requiresAction:
        bg = AppColors.gradeReviewBg;
        fg = AppColors.gradeReview;
        icon = Icons.warning_amber_rounded;
        break;
    }

    return InkWell(
      onTap: status == SyncStatus.failed
          ? onRetry
          : status == SyncStatus.requiresAction
              ? onAction
              : null,
      borderRadius: BorderRadius.circular(6),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: fg.withOpacity(0.4)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (status == SyncStatus.syncing)
              SizedBox(
                width: 12,
                height: 12,
                child: CircularProgressIndicator(strokeWidth: 2, color: fg),
              )
            else
              Icon(icon, size: 14, color: fg),
            const SizedBox(width: 5),
            Text(
              text,
              style: TextStyle(
                color: fg,
                fontWeight: FontWeight.w800,
                fontSize: 10.5,
                letterSpacing: 0.3,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
