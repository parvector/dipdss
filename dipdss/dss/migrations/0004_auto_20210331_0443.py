# Generated by Django 3.1.7 on 2021-03-31 04:43

from django.db import migrations, models
import dss.models


class Migration(migrations.Migration):

    dependencies = [
        ('dss', '0003_resultmodel_hv'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nsga3model',
            name='n_offsprings',
            field=models.CharField(blank=True, default='None', max_length=16, null=10, validators=[dss.models.is_positive_int_or_None]),
        ),
    ]
