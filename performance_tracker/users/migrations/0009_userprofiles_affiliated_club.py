# Generated by Django 5.1.6 on 2025-03-21 04:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_userprofiles_coaching_specialization_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofiles',
            name='affiliated_club',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
