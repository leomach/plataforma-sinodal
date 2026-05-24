from django.db import migrations


class Migration(migrations.Migration):
    """
    Remove Sessao e Presenca do estado do app hub (sem operações no banco).
    As tabelas hub_sessao e hub_presenca permanecem para a migração de dados
    em sessoes/0002, e serão removidas em hub/0004.
    """

    dependencies = [
        ('hub', '0002_tipodocumento_alter_documentoevento_options_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterUniqueTogether(
                    name='presenca',
                    unique_together=set(),
                ),
                migrations.RemoveField(model_name='presenca', name='sessao'),
                migrations.RemoveField(model_name='presenca', name='inscricao'),
                migrations.RemoveField(model_name='presenca', name='presente'),
                migrations.DeleteModel(name='Presenca'),
                migrations.RemoveField(model_name='sessao', name='evento'),
                migrations.RemoveField(model_name='sessao', name='nome'),
                migrations.RemoveField(model_name='sessao', name='data_hora'),
                migrations.DeleteModel(name='Sessao'),
            ],
            database_operations=[],
        ),
    ]
