# Generated by Django 5.1.4 on 2025-01-13 11:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatapp', '0004_alter_message_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='file_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='file_size',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='media_file',
            field=models.FileField(blank=True, null=True, upload_to='chat_media/%y/%m/%d/'),
        ),
        migrations.AddField(
            model_name='message',
            name='media_type',
            field=models.CharField(choices=[('text', 'Text'), ('image', 'Image'), ('video', 'Video'), ('file', 'File')], default='text', max_length=10),
        ),
    ]
