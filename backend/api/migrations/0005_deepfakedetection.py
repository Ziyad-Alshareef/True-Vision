# Generated by Django 4.2.18 on 2025-05-03 19:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0004_alter_analysis_video"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeepFakeDetection",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("face_count", models.IntegerField(default=0)),
                ("frame_count", models.IntegerField(default=0)),
                ("detection_time", models.FloatField(default=0.0)),
                (
                    "detection_method",
                    models.CharField(default="dnn_face", max_length=255),
                ),
                ("model_version", models.CharField(default="1.0", max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "detection",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="deepfake_detection",
                        to="api.detection",
                    ),
                ),
            ],
        ),
    ]
