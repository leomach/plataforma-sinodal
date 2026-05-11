from django.contrib import admin
from .models import Sessao, Presenca, DocumentoEvento

class DocumentoEventoInline(admin.TabularInline):
    model = DocumentoEvento
    extra = 1

class SessaoInline(admin.TabularInline):
    model = Sessao
    extra = 1

@admin.register(Sessao)
class SessaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'evento', 'data_hora')
    list_filter = ('evento',)

@admin.register(Presenca)
class PresencaAdmin(admin.ModelAdmin):
    list_display = ('sessao', 'inscricao', 'presente')
    list_filter = ('sessao', 'presente')

@admin.register(DocumentoEvento)
class DocumentoEventoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'evento', 'restrito_delegados')
    list_filter = ('evento', 'restrito_delegados')
