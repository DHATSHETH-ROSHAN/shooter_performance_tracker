# Generated by Django 5.1.6 on 2025-03-05 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scores', '0007_rename_notes_activities_notes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activities',
            name='notes',
            field=models.TextField(blank=True, null=True),
        ),
    ]
