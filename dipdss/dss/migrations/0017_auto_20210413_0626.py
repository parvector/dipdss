# Generated by Django 3.1.7 on 2021-04-13 06:26

from django.db import migrations, models
import dss.models


class Migration(migrations.Migration):

    dependencies = [
        ('dss', '0016_auto_20210413_0612'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fgmodel',
            name='f',
            field=models.TextField(help_text='В качестве переменной поступает вектор чисел X. Введите X[:,0], чтобы получить первое значение, или X[:,1], чтобы получить второе значение.', validators=[dss.models.valid_fg_func]),
        ),
        migrations.AlterField(
            model_name='fgmodel',
            name='g',
            field=models.TextField(help_text='В качестве переменной поступает вектор чисел X. Введите X[:,0], чтобы получить первое значение, или X[:,1], чтобы получить второе значение.', validators=[dss.models.valid_fg_func]),
        ),
    ]
