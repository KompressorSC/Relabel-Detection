# Generated by Django 5.0.1 on 2024-04-10 03:21

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ConfigHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('change_time', models.DateTimeField()),
                ('changes', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='DetectionHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateTimeField()),
                ('check_pass', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='ImageHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_date', models.DateTimeField()),
                ('image_path', models.CharField(max_length=100)),
                ('labeled', models.BooleanField(default=False)),
                ('trained', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='LabelHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label_date', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='ModelHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model_date', models.DateTimeField()),
                ('pt_path', models.CharField(max_length=100)),
                ('onnx_path', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='VideoHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('video_date', models.DateTimeField()),
                ('video_path', models.CharField(max_length=100)),
            ],
        ),
    ]
