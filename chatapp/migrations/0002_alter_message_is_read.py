# Generated by Django 5.1.4 on 2025-01-13 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='is_read',
            field=models.CharField(choices=[('sent', 'Sent'), ('delivered', 'Delivered'), ('ready', 'Read')], default='sent', max_length=10),
        ),
    ]
