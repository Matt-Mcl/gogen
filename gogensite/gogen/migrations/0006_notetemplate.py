# Generated by Django 4.2.4 on 2023-08-21 09:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gogen', '0005_puzzlelog_notes'),
    ]

    operations = [
        migrations.CreateModel(
            name='NoteTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('template', models.CharField(max_length=1024)),
            ],
        ),
    ]