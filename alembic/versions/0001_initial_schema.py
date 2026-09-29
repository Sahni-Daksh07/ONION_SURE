"""Initial schema for ONION_SURE normalized relational tables

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-30 02:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Procurement Centres
    op.create_table(
        'procurement_centres',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('centre_code', sa.String(50), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('district', sa.String(100), nullable=False),
        sa.Column('state', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_pc_code', 'procurement_centres', ['centre_code'])

    # 2. Roles
    op.create_table(
        'roles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 3. Users
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('procurement_centre_id', sa.String(36), sa.ForeignKey('procurement_centres.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 4. User Roles
    op.create_table(
        'user_roles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_id', sa.String(36), sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('user_id', 'role_id', name='uq_user_role'),
    )

    # 5. Farmers
    op.create_table(
        'farmers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('farmer_code', sa.String(50), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('village', sa.String(100), nullable=False),
        sa.Column('district', sa.String(100), nullable=False),
        sa.Column('state', sa.String(100), nullable=False),
        sa.Column('aadhaar_masked', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 6. Lots
    op.create_table(
        'lots',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('lot_number', sa.String(100), nullable=False, unique=True),
        sa.Column('farmer_id', sa.String(36), sa.ForeignKey('farmers.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('procurement_centre_id', sa.String(36), sa.ForeignKey('procurement_centres.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('variety', sa.String(50), nullable=False, server_default='Red Onion'),
        sa.Column('quantity_quintals', sa.Float(), nullable=False),
        sa.Column('bag_count', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='REGISTERED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 7. Inspections
    op.create_table(
        'inspections',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('inspection_code', sa.String(100), nullable=False, unique=True),
        sa.Column('lot_id', sa.String(36), sa.ForeignKey('lots.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('inspector_id', sa.String(36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('sample_size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='DRAFT'),
        sa.Column('total_onions_evaluated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('grade_a_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('grade_a_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('urs_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('urs_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('reject_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reject_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('manual_review_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('lot_decision', sa.String(50), nullable=True),
        sa.Column('decision_reason', sa.Text(), nullable=True),
        sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 8. Inspection Images
    op.create_table(
        'inspection_images',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('inspection_id', sa.String(36), sa.ForeignKey('inspections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('storage_key', sa.String(500), nullable=False),
        sa.Column('bucket', sa.String(100), nullable=False, server_default='onion-sure-inspections'),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('content_type', sa.String(50), nullable=False, server_default='image/jpeg'),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('sha256_hash', sa.String(64), nullable=True),
        sa.Column('quality_status', sa.String(50), nullable=False, server_default='PASSED'),
        sa.Column('blur_variance', sa.Float(), nullable=True),
        sa.Column('mean_brightness', sa.Float(), nullable=True),
        sa.Column('contrast_std', sa.Float(), nullable=True),
        sa.Column('quality_reasons', sa.JSON(), nullable=True),
        sa.Column('calibration_detected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('pixels_per_mm', sa.Float(), nullable=True),
        sa.Column('calibration_method', sa.String(50), nullable=True),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 9. Onion Detections
    op.create_table(
        'onion_detections',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('image_id', sa.String(36), sa.ForeignKey('inspection_images.id', ondelete='CASCADE'), nullable=False),
        sa.Column('onion_index', sa.String(50), nullable=False),
        sa.Column('bbox_x', sa.Float(), nullable=False),
        sa.Column('bbox_y', sa.Float(), nullable=False),
        sa.Column('bbox_w', sa.Float(), nullable=False),
        sa.Column('bbox_h', sa.Float(), nullable=False),
        sa.Column('segmentation_polygon', sa.JSON(), nullable=True),
        sa.Column('detection_confidence', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 10. Model Versions
    op.create_table(
        'model_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('version', sa.String(50), nullable=False, unique=True),
        sa.Column('model_type', sa.String(50), nullable=False),
        sa.Column('artifact_reference', sa.String(500), nullable=False),
        sa.Column('dataset_version', sa.String(50), nullable=False, server_default='1.0.0'),
        sa.Column('metrics_summary', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 11. Defect Results
    op.create_table(
        'defect_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('detection_id', sa.String(36), sa.ForeignKey('onion_detections.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('defect_class', sa.String(50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('all_probabilities', sa.JSON(), nullable=True),
        sa.Column('model_version_id', sa.String(36), sa.ForeignKey('model_versions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 12. Measurements
    op.create_table(
        'measurements',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('detection_id', sa.String(36), sa.ForeignKey('onion_detections.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('diameter_mm', sa.Float(), nullable=True),
        sa.Column('diameter_min_mm', sa.Float(), nullable=True),
        sa.Column('diameter_max_mm', sa.Float(), nullable=True),
        sa.Column('diameter_pixels', sa.Float(), nullable=False),
        sa.Column('calibration_method', sa.String(50), nullable=True),
        sa.Column('calibration_confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('pixels_per_mm', sa.Float(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 13. Grading Policies & Versions
    op.create_table(
        'grading_policies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('code', sa.String(50), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('crop', sa.String(50), nullable=False, server_default='Onion'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'grading_policy_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('policy_id', sa.String(36), sa.ForeignKey('grading_policies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('configuration', sa.JSON(), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('effective_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('policy_id', 'version', name='uq_policy_version'),
    )

    # 14. Grade Results
    op.create_table(
        'grade_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('inspection_id', sa.String(36), sa.ForeignKey('inspections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('detection_id', sa.String(36), sa.ForeignKey('onion_detections.id', ondelete='SET NULL'), unique=True, nullable=True),
        sa.Column('grade', sa.String(50), nullable=False),
        sa.Column('reason_codes', sa.JSON(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('decision_trace', sa.JSON(), nullable=False),
        sa.Column('grading_policy_version_id', sa.String(36), sa.ForeignKey('grading_policy_versions.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('model_version_id', sa.String(36), sa.ForeignKey('model_versions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('requires_review', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 15. Manual Reviews
    op.create_table(
        'manual_reviews',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('inspection_id', sa.String(36), sa.ForeignKey('inspections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('grade_result_id', sa.String(36), sa.ForeignKey('grade_results.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('reviewer_id', sa.String(36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('original_grade', sa.String(50), nullable=False),
        sa.Column('reviewed_grade', sa.String(50), nullable=False),
        sa.Column('reason', sa.String(255), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='APPROVED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 16. Reports
    op.create_table(
        'reports',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('report_code', sa.String(100), nullable=False, unique=True),
        sa.Column('inspection_id', sa.String(36), sa.ForeignKey('inspections.id', ondelete='RESTRICT'), unique=True, nullable=False),
        sa.Column('qr_verification_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('summary_metrics', sa.JSON(), nullable=False),
        sa.Column('pdf_storage_key', sa.String(500), nullable=True),
        sa.Column('is_finalized', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 17. Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('actor_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.String(36), nullable=False),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('correlation_id', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_audit_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('ix_audit_action', 'audit_logs', ['action'])

    # 18. Sync Records
    op.create_table(
        'sync_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('client_id', sa.String(100), nullable=False),
        sa.Column('sync_key', sa.String(100), nullable=False, unique=True),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.String(36), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='SYNCED'),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('sync_records')
    op.drop_table('audit_logs')
    op.drop_table('reports')
    op.drop_table('manual_reviews')
    op.drop_table('grade_results')
    op.drop_table('grading_policy_versions')
    op.drop_table('grading_policies')
    op.drop_table('measurements')
    op.drop_table('defect_results')
    op.drop_table('model_versions')
    op.drop_table('onion_detections')
    op.drop_table('inspection_images')
    op.drop_table('inspections')
    op.drop_table('lots')
    op.drop_table('farmers')
    op.drop_table('user_roles')
    op.drop_table('users')
    op.drop_table('roles')
    op.drop_table('procurement_centres')
