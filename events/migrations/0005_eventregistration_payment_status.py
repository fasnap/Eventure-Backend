# Generated by Django 5.1.4 on 2024-12-31 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0004_eventregistration_payment_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventregistration',
            name='payment_status',
            field=models.CharField(blank=True, default='pending', max_length=20, null=True),
        ),
    ]
