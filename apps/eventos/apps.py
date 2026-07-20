from django.apps import AppConfig


class EventosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.eventos'

    def ready(self):
        # Registra handlers de pagamento (efeito colateral do import)
        from . import handlers  # noqa: F401
