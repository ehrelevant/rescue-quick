# Generated by Django 5.2 on 2025-04-29 18:29

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0005_cameralogs_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sensorcamera',
            name='current_depth',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='sensorcamera',
            name='flood_number',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='sensorcamera',
            name='location',
            field=models.TextField(null=True),
        ),
    ]
