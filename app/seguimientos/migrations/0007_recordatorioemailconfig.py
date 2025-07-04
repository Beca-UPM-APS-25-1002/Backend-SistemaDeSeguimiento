# Generated by Django 5.2.1 on 2025-05-10 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seguimientos', '0006_alter_añoacademico_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecordatorioEmailConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asunto', models.CharField(default='Recordatorio de seguimiento pendiente - {{ mes }}', max_length=255)),
                ('contenido', models.TextField(default='Estimado/a {{ nombre_profesor }},\n\nLe recordamos que tiene pendiente realizar el seguimiento del mes de {{ mes }} para las siguientes docencias:\n\n{{ listado_docencias }}\n\nPuede completar los seguimientos pendientes haciendo clic en el siguiente enlace:\n{{ url_frontend }}\n\nGracias por su colaboración.\n\nEste es un correo automático, por favor no responda a esta dirección.')),
                ('help_text', models.TextField(default='Variables disponibles:\n- {{ nombre_profesor }}: Nombre del profesor\n- {{ mes }}: Nombre del mes del seguimiento\n- {{ listado_docencias }}: Lista de docencias pendientes\n- {{ url_frontend }}: URL del frontend para acceder al sistema\nDebes añadir por lo menos el mes y el listado de docencias al contenido.\nPuedes poner las variables también en el asunto.\n¡Cuidado, tienes que añadir un espacio antes y despues del nombre de cada variable! \n        ', editable=False, verbose_name='Información de ayuda')),
            ],
            options={
                'verbose_name': 'Configuración de Email de Recordatorio',
            },
        ),
    ]
