# Generated by Django 5.1.6 on 2025-03-05 12:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scores', '0006_activities'),
    ]

    operations = [
        migrations.RenameField(
            model_name='activities',
            old_name='Notes',
            new_name='notes',
        ),
    ]
