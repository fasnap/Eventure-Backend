# Generated by Django 5.1.4 on 2025-01-14 14:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='meeting_link',
        ),
    ]
