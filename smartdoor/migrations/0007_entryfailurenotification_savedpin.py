# Generated by Django 5.1.6 on 2025-03-28 00:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smartdoor', '0006_alter_entryfailurenotification_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='entryfailurenotification',
            name='savedPin',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
