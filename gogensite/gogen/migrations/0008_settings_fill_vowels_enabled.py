# Generated by Django 4.2.14 on 2025-03-19 18:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gogen', '0007_settings_preset_notes'),
    ]

    operations = [
        migrations.AddField(
            model_name='settings',
            name='fill_vowels_enabled',
            field=models.BooleanField(default=False),
        ),
    ]
