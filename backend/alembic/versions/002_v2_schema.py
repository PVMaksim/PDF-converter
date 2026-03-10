"""002 v2 schema - UUID models, file_records, plans

Revision ID: 002
Revises: 001
Create Date: 2026-03-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    # Drop old tables
    op.drop_table("conversion_jobs")
    op.drop_table("users")

    # users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tg_id", sa.BigInteger(), unique=True, nullable=True),
        sa.Column("email", sa.String(255), unique=True, nullable=True),
        sa.Column("hashed_password", sa.String(), nullable=True),
        sa.Column(
            "plan",
            sa.Enum("free", "pro", "enterprise", name="userplan"),
            nullable=False,
            server_default="free",
        ),
        sa.Column("daily_limit", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # file_records
    op.create_table(
        "file_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("storage_path", sa.String(), nullable=False),
        sa.Column("original_name", sa.String(512), nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_file_records_sha256", "file_records", ["sha256_hash"])
    op.create_index("ix_file_records_expires_at", "file_records", ["expires_at"])

    # conversion_jobs
    op.create_table(
        "conversion_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "done", "failed", name="jobstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("source_format", sa.String(16), nullable=False, server_default="pdf"),
        sa.Column("target_format", sa.String(16), nullable=False),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("file_records.id"), nullable=True),
        sa.Column("result_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("file_records.id"), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_conversion_jobs_user_id", "conversion_jobs", ["user_id"])


def downgrade():
    op.drop_table("conversion_jobs")
    op.drop_table("file_records")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS jobstatus")
    op.execute("DROP TYPE IF EXISTS userplan")
