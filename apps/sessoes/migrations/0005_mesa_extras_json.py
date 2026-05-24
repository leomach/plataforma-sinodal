from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('sessoes', '0004_membrodamesa_novos_cargos'),
    ]

    operations = [
        # Remove cargo personalizado do MembroDaMesa (migrado para JSON em Sessao)
        migrations.RemoveField(
            model_name='membrodamesa',
            name='cargo_descricao',
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
                ],
                verbose_name='Cargo',
            ),
        ),
        # Adiciona campo JSON de membros extras à Sessao
        migrations.AddField(
            model_name='sessao',
            name='membros_extras',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Lista JSON de membros com cargos personalizados: [{inscricao_id, nome, cargo_descricao}]',
                verbose_name='Membros Extras da Mesa',
            ),
        ),
    ]
