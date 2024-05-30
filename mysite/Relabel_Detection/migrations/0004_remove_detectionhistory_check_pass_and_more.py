# Generated by Django 5.0.1 on 2024-04-22 00:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Relabel_Detection', '0003_modelhistory_log_path'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='detectionhistory',
            name='check_pass',
        ),
        migrations.AddField(
            model_name='detectionhistory',
            name='check_MBB',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='detectionhistory',
            name='place',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='detectionhistory',
            name='tape',
            field=models.BooleanField(default=False),
        ),
    ]
