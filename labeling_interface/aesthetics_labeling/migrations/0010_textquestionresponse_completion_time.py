# Generated by Django 3.2.4 on 2021-11-14 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aesthetics_labeling', '0009_textquestionresponse'),
    ]

    operations = [
        migrations.AddField(
            model_name='textquestionresponse',
            name='completion_time',
            field=models.DateTimeField(null=True),
        ),
    ]