import 'package:flutter/material.dart';
import 'core/network/api_client.dart';
import 'core/storage/local_storage.dart';
import 'core/storage/sync_queue_manager.dart';
import 'app.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize core services
  await LocalStorage().init();
  await ApiClient().init();
  await SyncQueueManager().init();

  runApp(OnionSureApp());
}
