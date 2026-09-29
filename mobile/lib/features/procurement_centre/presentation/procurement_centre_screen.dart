import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/state_views.dart';
import '../repository/centre_repository.dart';

class ProcurementCentreScreen extends StatefulWidget {
  @override
  _ProcurementCentreScreenState createState() => _ProcurementCentreScreenState();
}

class _ProcurementCentreScreenState extends State<ProcurementCentreScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<CentreRepository>().fetchCentres();
    });
  }

  @override
  Widget build(BuildContext context) {
    final centreRepo = context.watch<CentreRepository>();
    final centres = centreRepo.centres;
    final activeCentre = centreRepo.activeCentre;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Procurement Centres (APMC)"),
      ),
      body: SafeArea(
        child: centreRepo.isLoading
            ? const LoadingView(message: "Loading procurement centres...")
            : centreRepo.errorMessage != null && centres.isEmpty
                ? ErrorView(
                    message: centreRepo.errorMessage!,
                    onRetry: () => centreRepo.fetchCentres(),
                  )
                : centres.isEmpty
                    ? const EmptyView(
                        title: "No Centres Registered",
                        message: "Contact DoCA administrator to configure procurement centres.",
                      )
                    : ListView.separated(
                        padding: const EdgeInsets.all(14),
                        itemCount: centres.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 10),
                        itemBuilder: (ctx, index) {
                          final centre = centres[index];
                          final isSelected = activeCentre?.id == centre.id;

                          return Card(
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                              side: BorderSide(
                                color: isSelected ? AppColors.primaryGreen : AppColors.cardBorder,
                                width: isSelected ? 2 : 1,
                              ),
                            ),
                            child: Padding(
                              padding: const EdgeInsets.all(16.0),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Expanded(
                                        child: Text(
                                          centre.name,
                                          style: const TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.w700,
                                          ),
                                        ),
                                      ),
                                      if (isSelected)
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                          decoration: BoxDecoration(
                                            color: AppColors.gradeABg,
                                            borderRadius: BorderRadius.circular(6),
                                          ),
                                          child: const Text(
                                            "ACTIVE MANDI",
                                            style: TextStyle(
                                              color: AppColors.gradeA,
                                              fontSize: 10.5,
                                              fontWeight: FontWeight.w800,
                                            ),
                                          ),
                                        ),
                                    ],
                                  ),
                                  const SizedBox(height: 6),
                                  Text(
                                    "Code: ${centre.centreCode} • District: ${centre.district}, ${centre.state}",
                                    style: const TextStyle(fontSize: 12.5, color: AppColors.textSecondary),
                                  ),
                                  const SizedBox(height: 14),
                                  if (!isSelected)
                                    OutlinedButton(
                                      onPressed: () {
                                        centreRepo.setActiveCentre(centre);
                                        ScaffoldMessenger.of(context).showSnackBar(
                                          SnackBar(content: Text("Active centre switched to: ${centre.name}")),
                                        );
                                      },
                                      child: const Text("Select As Active Centre"),
                                    ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
      ),
    );
  }
}
