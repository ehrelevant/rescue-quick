# Generated by Django 5.2 on 2025-05-14 15:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0018_sensorcamera_is_wet'),
    ]

    operations = [
        migrations.AddField(
            model_name='sensorcamera',
            name='token',
            field=models.CharField(blank=True, max_length=128, null=True, unique=True),
        ),
        migrations.CreateModel(
            name='RescuerContacts',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('email_addr', models.EmailField(max_length=254, unique=True)),
                (
                    'devices',
                    models.ManyToManyField(
                        related_name='devices', to='core.sensorcamera'
                    ),
                ),
            ],
        ),
    ]
