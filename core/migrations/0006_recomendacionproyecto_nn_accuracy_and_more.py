# Generated by Django 5.1.7 on 2025-06-02 21:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_recomendacionusuario_match_conocimientos_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='recomendacionproyecto',
            name='nn_accuracy',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='recomendacionproyecto',
            name='nn_f1',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='recomendacionproyecto',
            name='nn_precision',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='recomendacionproyecto',
            name='nn_recall',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='recomendacionusuario',
            name='score_nn',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
