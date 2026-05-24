import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('eventos', '0011_alter_presenca_unique_together_and_more'),
        ('hub', '0003_remove_sessao_presenca'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Sessao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=200, verbose_name='Nome da Sessão')),
                ('data_hora', models.DateTimeField(verbose_name='Data e Hora')),
                ('status', models.PositiveSmallIntegerField(
                    choices=[(1, 'Em Breve'), (2, 'Chamada'), (3, 'Aberta'), (4, 'Encerrada')],
                    default=1,
                    verbose_name='Status',
                )),
                ('is_verificacao_poderes', models.BooleanField(default=False, verbose_name='Sessão de Verificação de Poderes')),
                ('evento', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sessoes',
                    to='eventos.evento',
                )),
            ],
            options={
                'verbose_name': 'Sessão',
                'verbose_name_plural': 'Sessões',
                'ordering': ['data_hora'],
            },
        ),
        migrations.CreateModel(
            name='Presenca',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('presente', models.BooleanField(default=False, verbose_name='Presente')),
                ('ultima_atualizacao', models.DateTimeField(auto_now=True)),
                ('sessao', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='presencas',
                    to='sessoes.sessao',
                )),
                ('inscricao', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='presencas_sessoes',
                    to='eventos.inscricao',
                )),
            ],
            options={
                'verbose_name': 'Presença',
                'verbose_name_plural': 'Presenças',
                'unique_together': {('sessao', 'inscricao')},
            },
        ),
        migrations.CreateModel(
            name='CredencialQRCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(db_index=True, max_length=64, unique=True)),
                ('gerado_em', models.DateTimeField(auto_now_add=True)),
                ('ativo', models.BooleanField(default=True)),
                ('inscricao', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='qr_code',
                    to='eventos.inscricao',
                )),
            ],
            options={
                'verbose_name': 'Credencial QR Code',
                'verbose_name_plural': 'Credenciais QR Code',
            },
        ),
        migrations.CreateModel(
            name='Votacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=500, verbose_name='Proposta / Título')),
                ('status', models.PositiveSmallIntegerField(
                    choices=[(1, 'Aberta'), (2, 'Aguardando Voto de Minerva'), (3, 'Encerrada')],
                    default=1,
                    verbose_name='Status',
                )),
                ('resultado', models.PositiveSmallIntegerField(
                    blank=True,
                    choices=[(1, 'Aprovada'), (2, 'Rejeitada')],
                    null=True,
                    verbose_name='Resultado',
                )),
                ('voto_minerva_favor', models.BooleanField(blank=True, null=True, verbose_name='Voto de Minerva — A Favor')),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
                ('encerrada_em', models.DateTimeField(blank=True, null=True)),
                ('sessao', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='votacoes',
                    to='sessoes.sessao',
                )),
                ('minerva_por', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='votos_minerva',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Votação',
                'verbose_name_plural': 'Votações',
                'ordering': ['-criada_em'],
            },
        ),
        migrations.CreateModel(
            name='VotoParticipante',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('voto', models.PositiveSmallIntegerField(
                    choices=[(1, 'A Favor'), (2, 'Contra'), (3, 'Abster-se')],
                    verbose_name='Voto',
                )),
                ('votado_em', models.DateTimeField(auto_now_add=True)),
                ('votacao', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='votos',
                    to='sessoes.votacao',
                )),
                ('inscricao', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='votos_participante',
                    to='eventos.inscricao',
                )),
            ],
            options={
                'verbose_name': 'Voto',
                'verbose_name_plural': 'Votos',
                'unique_together': {('votacao', 'inscricao')},
            },
        ),
        migrations.CreateModel(
            name='EventoLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.PositiveSmallIntegerField(
                    choices=[(1, 'Automático'), (2, 'Manual')],
                    default=1,
                    verbose_name='Tipo',
                )),
                ('descricao', models.TextField(verbose_name='Descrição')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('sessao', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='logs',
                    to='sessoes.sessao',
                )),
                ('usuario', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='logs_sessao',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Log da Sessão',
                'verbose_name_plural': 'Logs das Sessões',
                'ordering': ['timestamp'],
            },
        ),
    ]
