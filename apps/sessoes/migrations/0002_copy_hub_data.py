from django.db import migrations


def copy_sessoes_from_hub(apps, schema_editor):
    db = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO sessoes_sessao (id, evento_id, nome, data_hora, status, is_verificacao_poderes)
            SELECT id, evento_id, nome, data_hora, 1, false
            FROM hub_sessao
            ON CONFLICT (id) DO NOTHING
        """)
        cursor.execute("""
            INSERT INTO sessoes_presenca (id, sessao_id, inscricao_id, presente, ultima_atualizacao)
            SELECT id, sessao_id, inscricao_id, presente, NOW()
            FROM hub_presenca
            ON CONFLICT (id) DO NOTHING
        """)
        # Resync sequences para evitar conflito de ID no futuro
        cursor.execute(
            "SELECT setval('sessoes_sessao_id_seq', "
            "COALESCE((SELECT MAX(id) FROM sessoes_sessao), 1))"
        )
        cursor.execute(
            "SELECT setval('sessoes_presenca_id_seq', "
            "COALESCE((SELECT MAX(id) FROM sessoes_presenca), 1))"
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('sessoes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(copy_sessoes_from_hub, reverse_code=noop),
    ]
