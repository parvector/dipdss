# Generated by Django 3.1.7 on 2021-04-10 10:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dss', '0013_resultmodel_hvs_gens_fig'),
    ]

    operations = [
        migrations.AddField(
            model_name='resultmodel',
            name='ref_dirs_fig',
            field=models.TextField(blank=True),
        ),
    ]
