from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE dashboard_runauditlog ENABLE ROW LEVEL SECURITY;",
            reverse_sql="ALTER TABLE dashboard_runauditlog DISABLE ROW LEVEL SECURITY;",
        ),
        migrations.RunSQL(
            sql="""
            CREATE POLICY tenant_isolation_policy ON dashboard_runauditlog
            FOR ALL
            USING (repository_name LIKE current_setting('app.current_tenant') || '/%');
            """,
            reverse_sql="DROP POLICY tenant_isolation_policy ON dashboard_runauditlog;",
        ),
    ]
