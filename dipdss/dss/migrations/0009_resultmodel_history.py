# Generated by Django 3.1.7 on 2021-04-08 12:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dss', '0008_auto_20210407_1904'),
    ]

    operations = [
        migrations.AddField(
            model_name='resultmodel',
            name='history',
            field=models.TextField(blank=True),
        ),
    ]
