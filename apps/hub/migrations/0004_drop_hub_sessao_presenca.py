from django.db import migrations


class Migration(migrations.Migration):
    """
    Drop das tabelas hub_sessao e hub_presenca após migração de dados para sessoes.
    """

    dependencies = [
        ('hub', '0003_remove_sessao_presenca'),
        ('sessoes', '0002_copy_hub_data'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[],
            database_operations=[
                migrations.RunSQL(
                    sql='DROP TABLE IF EXISTS hub_presenca CASCADE',
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    sql='DROP TABLE IF EXISTS hub_sessao CASCADE',
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
