import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'core/theme/app_theme.dart';
import 'core/storage/sync_queue_manager.dart';
import 'features/auth/repository/auth_repository.dart';
import 'features/farmer/repository/farmer_repository.dart';
import 'features/procurement_centre/repository/centre_repository.dart';
import 'features/lot/repository/lot_repository.dart';
import 'features/inspection/repository/inspection_repository.dart';

// Screens
import 'features/splash/presentation/splash_screen.dart';
import 'features/auth/presentation/login_screen.dart';
import 'features/dashboard/presentation/dashboard_screen.dart';
import 'features/farmer/presentation/farmer_list_screen.dart';
import 'features/procurement_centre/presentation/procurement_centre_screen.dart';
import 'features/lot/presentation/create_lot_screen.dart';
import 'features/inspection/presentation/create_inspection_screen.dart';
import 'features/inspection/presentation/sampling_guidance_screen.dart';
import 'features/inspection/presentation/camera_capture_screen.dart';
import 'features/inspection/presentation/image_quality_screen.dart';
import 'features/inspection/presentation/ai_processing_screen.dart';
import 'features/inspection/presentation/onion_results_screen.dart';
import 'features/inspection/presentation/lot_results_screen.dart';
import 'features/manual_review/presentation/manual_review_screen.dart';
import 'features/history/presentation/inspection_history_screen.dart';
import 'features/reports/presentation/report_screen.dart';
import 'features/qr_verification/presentation/qr_verification_screen.dart';
import 'features/settings/presentation/settings_screen.dart';

class OnionSureApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthRepository()),
        ChangeNotifierProvider(create: (_) => FarmerRepository()),
        ChangeNotifierProvider(create: (_) => CentreRepository()),
        ChangeNotifierProvider(create: (_) => LotRepository()),
        ChangeNotifierProvider(create: (_) => InspectionRepository()),
        ChangeNotifierProvider(create: (_) => SyncQueueManager()),
      ],
      child: MaterialApp(
        title: 'ONION_SURE',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        initialRoute: '/',
        routes: {
          '/': (ctx) => SplashScreen(),
          '/login': (ctx) => LoginScreen(),
          '/dashboard': (ctx) => DashboardScreen(),
          '/farmers': (ctx) => FarmerListScreen(),
          '/procurement_centres': (ctx) => ProcurementCentreScreen(),
          '/create_lot': (ctx) => CreateLotScreen(),
          '/create_inspection': (ctx) => CreateInspectionScreen(),
          '/sampling': (ctx) => SamplingGuidanceScreen(),
          '/camera': (ctx) => CameraCaptureScreen(),
          '/image_quality': (ctx) => ImageQualityScreen(),
          '/ai_processing': (ctx) => AiProcessingScreen(),
          '/onion_results': (ctx) => OnionResultsScreen(),
          '/lot_results': (ctx) => LotResultsScreen(),
          '/manual_review': (ctx) => ManualReviewScreen(),
          '/history': (ctx) => InspectionHistoryScreen(),
          '/report': (ctx) => ReportScreen(),
          '/qr_verification': (ctx) => QrVerificationScreen(),
          '/settings': (ctx) => SettingsScreen(),
        },
      ),
    );
  }
}
