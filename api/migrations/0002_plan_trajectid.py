# Generated by Django 5.0.2 on 2024-02-29 00:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='trajectId',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='api.traject'),
        ),
    ]
