from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0004_organization_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Deployment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organization_name', models.CharField(db_index=True, max_length=255)),
                ('repository_name', models.CharField(max_length=255)),
                ('commit_sha', models.CharField(max_length=40)),
                ('branch', models.CharField(default='main', max_length=255)),
                ('status', models.CharField(choices=[('QUEUED', 'Queued'), ('BUILDING', 'Building'), ('DEPLOYING', 'Deploying'), ('DEPLOYED', 'Deployed'), ('ROLLED_BACK', 'Rolled Back'), ('FAILED', 'Failed')], default='QUEUED', max_length=20)),
                ('strategy', models.CharField(choices=[('docker', 'Docker'), ('kubernetes', 'Kubernetes'), ('serverless', 'Serverless'), ('custom_script', 'Custom Script')], default='docker', max_length=20)),
                ('target_url', models.URLField(blank=True, default='')),
                ('logs', models.TextField(blank=True, default='')),
                ('triggered_by', models.CharField(default='auto', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('deployed_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),
    ]
