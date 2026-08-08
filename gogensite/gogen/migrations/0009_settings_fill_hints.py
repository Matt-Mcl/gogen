from django.db import migrations, models


def vowels_to_hints(apps, schema_editor):
    """Anyone who had vowel hints on keeps them, now as a choice."""
    Settings = apps.get_model('gogen', 'Settings')
    Settings.objects.filter(fill_vowels_enabled=True).update(fill_hints='V')


def hints_to_vowels(apps, schema_editor):
    """Going back, both hint settings collapse to the old on/off."""
    Settings = apps.get_model('gogen', 'Settings')
    Settings.objects.filter(fill_hints__in=('V', 'A')).update(fill_vowels_enabled=True)


class Migration(migrations.Migration):

    dependencies = [
        ('gogen', '0008_settings_fill_vowels_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='settings',
            name='fill_hints',
            field=models.CharField(
                choices=[('N', 'Off'), ('V', 'Vowel hints'), ('A', 'All hints')],
                default='N',
                max_length=1,
            ),
        ),
        migrations.RunPython(vowels_to_hints, hints_to_vowels),
        migrations.RemoveField(
            model_name='settings',
            name='fill_vowels_enabled',
        ),
    ]
