# Generated by Django 5.2.1 on 2025-05-11 17:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seguimientos', '0007_recordatorioemailconfig'),
    ]

    operations = [
        migrations.AddField(
            model_name='seguimiento',
            name='temario_completado',
            field=models.ManyToManyField(to='seguimientos.unidaddetrabajo'),
        ),
    ]
