from django.db import migrations

class Migration(migrations.Migration):
    atomic = False
    dependencies = [
        ('file_sharing', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL([
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tempfile_active_expires ON temp_files(is_active, expires_at) WHERE is_active = true;",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tempfile_share_token_hash ON temp_files USING hash(share_token);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tempfile_created_at_desc ON temp_files(created_at DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_downloadlog_tempfile_time ON download_logs(temp_file_id, downloaded_at DESC);",
        ], reverse_sql=[
            "DROP INDEX IF EXISTS idx_tempfile_active_expires;",
            "DROP INDEX IF EXISTS idx_tempfile_share_token_hash;",
            "DROP INDEX IF EXISTS idx_tempfile_created_at_desc;",
            "DROP INDEX IF EXISTS idx_downloadlog_tempfile_time;",
        ]),
    ]
