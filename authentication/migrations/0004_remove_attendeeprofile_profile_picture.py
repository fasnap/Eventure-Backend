# Generated by Django 5.1.4 on 2025-01-10 06:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_alter_attendeeprofile_profile_picture'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attendeeprofile',
            name='profile_picture',
        ),
    ]
