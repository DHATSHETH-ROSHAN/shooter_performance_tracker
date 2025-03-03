# Generated by Django 5.1.6 on 2025-03-03 07:09

import django.contrib.postgres.fields
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='manualscore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('match_type', models.CharField(choices=[('40-Shots', '40 shots'), ('60-Shots', '60 shots')], max_length=10)),
                ('series_1', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), blank=True, null=True, size=10)),
                ('series_2', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), blank=True, null=True, size=10)),
                ('series_3', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), blank=True, null=True, size=10)),
                ('series_4', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), blank=True, null=True, size=10)),
                ('series_5', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), blank=True, null=True, size=10)),
                ('series_6', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), blank=True, null=True, size=10)),
                ('s1t', models.IntegerField(editable=False, null=True)),
                ('s2t', models.IntegerField(editable=False, null=True)),
                ('s3t', models.IntegerField(editable=False, null=True)),
                ('s4t', models.IntegerField(editable=False, null=True)),
                ('s5t', models.IntegerField(editable=False, null=True)),
                ('s6t', models.IntegerField(editable=False, null=True)),
                ('total', models.FloatField(null=True)),
                ('date', models.DateField(null=True)),
                ('day', models.CharField(editable=False, max_length=10, null=True)),
                ('average', models.DecimalField(decimal_places=1, editable=False, max_digits=5, null=True)),
                ('current_time', models.DateTimeField(auto_now_add=True)),
                ('duration', models.IntegerField(null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('adjustment_made', models.BooleanField(default=False)),
                ('adjustment_comment', models.TextField(blank=True, null=True)),
                ('user_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='pdfScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('match_type', models.CharField(choices=[('40-Shots', '40 shots'), ('60-Shots', '60 shots')], max_length=10)),
                ('series_1', django.contrib.postgres.fields.ArrayField(base_field=models.DecimalField(decimal_places=1, max_digits=3), blank=True, null=True, size=10)),
                ('series_2', django.contrib.postgres.fields.ArrayField(base_field=models.DecimalField(decimal_places=1, max_digits=3), blank=True, null=True, size=10)),
                ('series_3', django.contrib.postgres.fields.ArrayField(base_field=models.DecimalField(decimal_places=1, max_digits=3), blank=True, null=True, size=10)),
                ('series_4', django.contrib.postgres.fields.ArrayField(base_field=models.DecimalField(decimal_places=1, max_digits=3), blank=True, null=True, size=10)),
                ('series_5', django.contrib.postgres.fields.ArrayField(base_field=models.DecimalField(decimal_places=1, max_digits=3), blank=True, null=True, size=10)),
                ('series_6', django.contrib.postgres.fields.ArrayField(base_field=models.DecimalField(decimal_places=1, max_digits=3), blank=True, null=True, size=10)),
                ('s1t', models.DecimalField(decimal_places=1, editable=False, max_digits=5, null=True)),
                ('s2t', models.DecimalField(decimal_places=1, editable=False, max_digits=5, null=True)),
                ('s3t', models.DecimalField(decimal_places=1, editable=False, max_digits=5, null=True)),
                ('s4t', models.DecimalField(decimal_places=1, editable=False, max_digits=5, null=True)),
                ('s5t', models.DecimalField(decimal_places=1, editable=False, max_digits=5, null=True)),
                ('s6t', models.DecimalField(decimal_places=1, editable=False, max_digits=5, null=True)),
                ('total', models.DecimalField(decimal_places=1, editable=False, max_digits=5, null=True)),
                ('inner_tens', models.DecimalField(decimal_places=0, editable=False, max_digits=3, null=True)),
                ('s1mpi', django.contrib.postgres.fields.ArrayField(base_field=models.DecimalField(decimal_places=1, max_digits=5), blank=True, null=True, size=2)),
                ('s2mpi', django.contrib.postgres.fields.ArrayField(base_field=models.DecimalField(decimal_places=1, max_digits=5), blank=True, null=True, size=2)),
                ('s3mpi', django.contrib.postgres.fields.ArrayField(base_field=models.DecimalField(decimal_places=1, max_digits=5), blank=True, null=True, size=2)),
                ('s4mpi', django.contrib.postgres.fields.ArrayField(base_field=models.DecimalField(decimal_places=1, max_digits=5), blank=True, null=True, size=2)),
                ('s5mpi', django.contrib.postgres.fields.ArrayField(base_field=models.DecimalField(decimal_places=1, max_digits=5), blank=True, null=True, size=2)),
                ('s6mpi', django.contrib.postgres.fields.ArrayField(base_field=models.DecimalField(decimal_places=1, max_digits=5), blank=True, null=True, size=2)),
                ('fmpi', django.contrib.postgres.fields.ArrayField(base_field=models.DecimalField(decimal_places=2, max_digits=5), blank=True, null=True, size=2)),
                ('date', models.DateField(null=True)),
                ('day', models.CharField(editable=False, max_length=10, null=True)),
                ('average_shot_score', models.DecimalField(decimal_places=1, editable=False, max_digits=5, null=True)),
                ('average_series_score', models.DecimalField(decimal_places=1, editable=False, max_digits=5, null=True)),
                ('current_time', models.DateTimeField(auto_now_add=True)),
                ('duration', models.IntegerField(null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('adjustment_made', models.BooleanField(default=False)),
                ('adjustment_comment', models.TextField(blank=True, null=True)),
                ('user_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
