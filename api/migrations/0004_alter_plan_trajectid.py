# Generated by Django 5.0.2 on 2024-02-29 02:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_traject_datetime'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plan',
            name='trajectId',
            field=models.ForeignKey(blank=True, default=1, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.traject'),
        ),
    ]
