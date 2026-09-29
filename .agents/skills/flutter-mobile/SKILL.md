---
name: flutter-mobile
description: >-
  Governs the Flutter mobile application for ONION_SURE: Android-first,
  clean architecture, state management, camera integration, AI processing,
  offline support, QR verification, and all UI screens. Business logic must
  be separated from widgets. Activate for any mobile/Flutter task.
---

# Flutter Mobile Skill

## Purpose

Define the architecture and standards for the ONION_SURE Flutter mobile
application. This is the primary user-facing component for onion quality
inspection at procurement centers.

## When to Use

- Creating or modifying Flutter screens/widgets.
- Implementing state management.
- Integrating camera functionality.
- Implementing offline support.
- Connecting to the FastAPI backend.
- Building the inspection workflow UI.
- Implementing QR code scanning/generation.

## Required Inputs

- Feature specification or screen requirements.
- API contract (from `api-integration` skill).
- UI/UX design (if available).

---

## Platform Target

- **Primary:** Android (API 24+)
- **Secondary:** iOS (if resources permit, not MVP)
- **Flutter SDK:** Latest stable channel
- **Dart:** Latest stable

---

## Clean Architecture

```
mobile/
├── lib/
│   ├── main.dart
│   ├── app.dart                    # App configuration, routing
│   ├── core/
│   │   ├── constants/
│   │   ├── errors/                 # Exception and failure classes
│   │   ├── network/                # API client, interceptors
│   │   ├── storage/                # Local database (SQLite/Hive)
│   │   ├── theme/                  # App theme, colors, typography
│   │   └── utils/
│   ├── features/
│   │   ├── auth/
│   │   │   ├── data/
│   │   │   │   ├── datasources/    # Remote + local data sources
│   │   │   │   ├── models/         # Data transfer objects
│   │   │   │   └── repositories/   # Repository implementations
│   │   │   ├── domain/
│   │   │   │   ├── entities/       # Business entities
│   │   │   │   ├── repositories/   # Repository interfaces
│   │   │   │   └── usecases/       # Business logic
│   │   │   └── presentation/
│   │   │       ├── bloc/           # or provider/riverpod
│   │   │       ├── pages/          # Screen widgets
│   │   │       └── widgets/        # Reusable widgets
│   │   ├── dashboard/
│   │   ├── farmer/
│   │   ├── lot/
│   │   ├── inspection/
│   │   │   ├── data/
│   │   │   ├── domain/
│   │   │   └── presentation/
│   │   │       ├── pages/
│   │   │       │   ├── inspection_page.dart
│   │   │       │   ├── camera_page.dart
│   │   │       │   ├── image_review_page.dart
│   │   │       │   ├── results_page.dart
│   │   │       │   └── lot_summary_page.dart
│   │   │       └── widgets/
│   │   ├── manual_review/
│   │   ├── reports/
│   │   ├── qr_verification/
│   │   ├── history/
│   │   └── settings/
│   └── injection.dart              # Dependency injection
├── test/
│   ├── unit/
│   ├── widget/
│   └── integration/
├── pubspec.yaml
├── analysis_options.yaml
└── android/
    └── ...
```

---

## Layer Responsibilities

### Presentation Layer (UI)

- Widgets render UI based on state.
- **NO business logic in widgets.**
- Widgets react to state changes (loading, success, error, empty, offline).
- Widgets dispatch events/actions to state management.

### State Management (BLoC/Provider/Riverpod)

- Manages UI state transitions.
- Calls use cases from the domain layer.
- Emits states: `loading`, `success`, `error`, `empty`, `offline`, `syncing`.
- Handles error mapping to user-friendly messages.

### Domain Layer

- Pure Dart — no Flutter or platform dependencies.
- Contains entities, repository interfaces, and use cases.
- Business rules live here.

### Data Layer

- Implements repository interfaces.
- Manages remote (API) and local (SQLite/Hive) data sources.
- Handles data mapping between API models and domain entities.
- Implements offline caching and sync logic.

---

## Required Screens

| Screen | Feature | Description |
|:---|:---|:---|
| Login | `auth` | Authentication with username/password |
| Dashboard | `dashboard` | Overview of recent inspections, stats |
| Farmer List/Detail | `farmer` | Manage farmer records |
| Lot List/Create | `lot` | Create and manage onion lots |
| Inspection Start | `inspection` | Begin new inspection for a lot |
| Camera Capture | `inspection` | Capture onion images |
| Image Quality Check | `inspection` | Validate captured image quality |
| AI Processing | `inspection` | Show inference progress |
| Onion Results | `inspection` | Per-onion detection and grade |
| Lot Summary | `inspection` | Lot-level Grade A%, URS%, Reject% |
| Manual Review | `manual_review` | Human review for flagged onions |
| Report View | `reports` | View generated quality report |
| QR Verification | `qr_verification` | Scan QR to verify report |
| History | `history` | Past inspections and reports |
| Settings | `settings` | User profile, sync status, app info |

---

## UI State Pattern

Every screen must handle ALL states:

```dart
abstract class InspectionState {}

class InspectionLoading extends InspectionState {}
class InspectionSuccess extends InspectionState {
  final InspectionData data;
}
class InspectionEmpty extends InspectionState {}
class InspectionError extends InspectionState {
  final String message;
  final String? errorCode;
}
class InspectionOffline extends InspectionState {
  final InspectionData? cachedData;
}
class InspectionSyncing extends InspectionState {
  final double progress;
}
```

Every screen must render appropriately for each state — no blank screens.

---

## Camera Integration

- Use `camera` or `image_picker` package.
- Validate image quality before submission.
- Support flash, auto-focus, resolution settings.
- Guide user with overlay for optimal capture angle.
- Store captured images locally before upload.

---

## Implementation Rules

1. **Clean architecture.** Separate presentation, domain, and data layers.
2. **No business logic in widgets.** Use BLoC, Provider, or Riverpod.
3. **Handle all UI states.** Loading, success, empty, error, offline, syncing.
4. **Offline-first design.** Core workflows work without network.
5. **Type-safe API integration.** Use generated or hand-crafted typed models.
6. **Consistent error handling.** Map API errors to user-friendly messages.
7. **Dependency injection.** Use `get_it`, `injectable`, or `riverpod`.
8. **Responsive layouts.** Support various Android screen sizes.
9. **Accessibility.** Use semantic labels for screen readers.

---

## Validation Rules

- ✅ Every screen handles loading, success, error, empty, offline states.
- ✅ No business logic inside widget `build()` methods.
- ✅ API calls go through the repository layer.
- ✅ Captured images are stored locally before upload.
- ✅ Navigation follows defined routes (no ad-hoc navigation).
- ✅ Theme and styling are centralized in `core/theme/`.

---

## Forbidden Behavior

- ❌ Business logic directly in widgets.
- ❌ Raw API calls in the UI layer (must go through repository → service → API).
- ❌ Blank screens for any state (loading, error, empty, offline).
- ❌ Hardcoded strings (use localization or constants).
- ❌ Storing credentials in shared preferences without encryption.
- ❌ Ignoring offline state.
- ❌ Platform-specific code without abstraction.

---

## Expected Outputs

1. **Flutter project** with clean architecture.
2. **All required screens** implemented with proper state handling.
3. **Camera integration** with image quality validation.
4. **Offline support** with local persistence.
5. **API integration** with typed models.
6. **Tests** — unit, widget, and integration.

---

## Dependencies on Other Skills

| Skill | Relationship |
|:---|:---|
| `api-integration` | API contract and typed schemas |
| `offline-sync` | Offline persistence and sync queue |
| `reporting-qr` | QR code generation and verification |
| `security` | Secure credential storage |
| `testing` | Flutter test requirements |
| `ps26031-requirements` | Screen/feature alignment with PS26031 |
