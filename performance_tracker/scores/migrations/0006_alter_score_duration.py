# Generated by Django 5.1.6 on 2025-02-26 07:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scores', '0005_score_duration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='score',
            name='duration',
            field=models.IntegerField(null=True),
        ),
    ]
