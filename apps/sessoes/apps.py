from django.apps import AppConfig


class SessoesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sessoes'
    verbose_name = 'Sessões'

    def ready(self):
        import apps.sessoes.signals  # noqa
