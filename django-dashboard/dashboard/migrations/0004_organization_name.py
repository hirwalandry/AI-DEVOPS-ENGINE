from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0003_developerapikey"),
    ]

    operations = [
        migrations.AddField(
            model_name="runauditlog",
            name="organization_name",
            field=models.CharField(default="default", max_length=255, db_index=True),
            preserve_default=False,
        ),
        migrations.RunSQL(
            sql="""
            UPDATE dashboard_runauditlog
            SET organization_name = SPLIT_PART(repository_name, '/', 1)
            WHERE organization_name = 'default';
            """,
            reverse_sql="",
        ),
        migrations.RunSQL(
            sql="DROP POLICY IF EXISTS tenant_isolation_policy ON dashboard_runauditlog;",
            reverse_sql="""
            CREATE POLICY tenant_isolation_policy ON dashboard_runauditlog
            FOR ALL
            USING (
                current_setting('app.current_tenant', true) IS NULL
                OR organization_name = current_setting('app.current_tenant')
            );
            """,
        ),
        migrations.RunSQL(
            sql="""
            CREATE POLICY tenant_isolation_policy ON dashboard_runauditlog
            FOR ALL
            USING (
                current_setting('app.current_tenant', true) IS NULL
                OR organization_name = current_setting('app.current_tenant')
            );
            """,
            reverse_sql="DROP POLICY tenant_isolation_policy ON dashboard_runauditlog;",
        ),
    ]
