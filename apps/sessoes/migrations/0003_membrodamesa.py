from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('eventos', '0011_alter_presenca_unique_together_and_more'),
        ('sessoes', '0002_copy_hub_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='MembroDaMesa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cargo', models.PositiveSmallIntegerField(
                    choices=[
                        (1, 'Presidente da Mesa'),
                        (2, 'Vice-Presidente'),
                        (3, '1º Secretário'),
                        (4, '2º Secretário'),
                    ],
                    verbose_name='Cargo',
                )),
                ('assumiu_em', models.DateTimeField(auto_now_add=True)),
                ('encerrou_em', models.DateTimeField(blank=True, null=True)),
                ('sessao', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='membros_mesa',
                    to='sessoes.sessao',
                )),
                ('inscricao', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='cargos_mesa',
                    to='eventos.inscricao',
                )),
            ],
            options={
                'verbose_name': 'Membro da Mesa',
                'verbose_name_plural': 'Mesa Diretora',
                'ordering': ['cargo', 'assumiu_em'],
            },
        ),
    ]
