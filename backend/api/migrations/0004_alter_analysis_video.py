# Generated by Django 4.2.18 on 2025-04-20 19:37

import api.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0003_rename_user_customuser"),
    ]

    operations = [
        migrations.AlterField(
            model_name="analysis",
            name="video",
            field=models.FileField(
                storage=api.models.S3MediaStorage(), upload_to="uploads/"
            ),
        ),
    ]
