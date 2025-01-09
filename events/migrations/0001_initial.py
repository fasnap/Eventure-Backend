# Generated by Django 5.1.4 on 2024-12-28 09:57

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
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=255)),
                ('category', models.CharField(choices=[('technology', 'Technology'), ('arts', 'Arts'), ('sports', 'Sports'), ('health', 'Health'), ('food', 'Food'), ('entertainment', 'Entertainment'), ('other', 'Other')], max_length=25)),
                ('event_type', models.CharField(choices=[('online', 'Online'), ('offline', 'Offline')], max_length=10)),
                ('date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('description', models.TextField()),
                ('image', models.ImageField(upload_to='event_images/')),
                ('venue', models.CharField(blank=True, max_length=250, null=True)),
                ('country', models.CharField(max_length=50)),
                ('state', models.CharField(max_length=50)),
                ('district', models.CharField(max_length=50)),
                ('location', models.CharField(blank=True, max_length=255, null=True)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
                ('is_created', models.BooleanField(default=False)),
                ('is_approved', models.BooleanField(default=False)),
                ('ticket_type', models.CharField(choices=[('paid', 'Paid'), ('free', 'Free')], default='free', max_length=10)),
                ('price', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=10, null=True)),
                ('total_tickets', models.PositiveIntegerField(default=100)),
                ('streaming_url', models.URLField(blank=True, null=True)),
                ('is_streaming', models.BooleanField(default=False)),
                ('signaling_room_id', models.CharField(blank=True, max_length=255, null=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EventRegistration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ticket', models.CharField(max_length=50, unique=True)),
                ('attendee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registered_events', to=settings.AUTH_USER_MODEL)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registrations', to='events.event')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
