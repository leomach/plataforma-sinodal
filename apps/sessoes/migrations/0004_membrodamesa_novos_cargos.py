from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('sessoes', '0003_membrodamesa'),
    ]

    operations = [
        migrations.AddField(
            model_name='membrodamesa',
            name='cargo_descricao',
            field=models.CharField(
                blank=True,
                default='',
                max_length=100,
                verbose_name='Descrição do Cargo',
            ),
        ),
        migrations.AlterField(
            model_name='membrodamesa',
            name='cargo',
            field=models.PositiveSmallIntegerField(
                choices=[
                    (1, 'Presidente da Mesa'),
                    (2, 'Vice-Presidente'),
                    (3, '1º Secretário'),
                    (4, '2º Secretário'),
                    (5, 'Tesoureiro'),
                    (6, 'Secretário Executivo'),
                    (7, 'Outros'),
                ],
                verbose_name='Cargo',
            ),
        ),
    ]
