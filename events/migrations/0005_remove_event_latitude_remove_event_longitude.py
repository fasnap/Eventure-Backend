# Generated by Django 5.1.2 on 2024-11-30 14:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0004_event_latitude_event_longitude'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='latitude',
        ),
        migrations.RemoveField(
            model_name='event',
            name='longitude',
        ),
    ]