# Generated by Django 4.0.6 on 2022-07-22 15:59

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gogen', '0002_alter_puzzlelog_board'),
    ]

    operations = [
        migrations.AddField(
            model_name='puzzlelog',
            name='placeholders',
            field=django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=30), size=5), default=[], size=5),
            preserve_default=False,
        ),
    ]
