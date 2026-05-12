from django.contrib import admin
from .models import Evento, CampoEvento, Inscricao, RespostaInscricao
from apps.hub.admin import SessaoInline, DocumentoEventoInline

class CampoEventoInline(admin.TabularInline):
    model = CampoEvento
    extra = 1

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'data_inicio', 'local', 'ativo')
    list_filter = ('categoria', 'ativo', 'data_inicio')
    search_fields = ('titulo', 'local')
    prepopulated_fields = {'slug': ('titulo',)}
    inlines = [CampoEventoInline, SessaoInline, DocumentoEventoInline]

class RespostaInscricaoInline(admin.TabularInline):
    model = RespostaInscricao
    extra = 0
    readonly_fields = ('campo', 'valor')

@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'evento', 'papel_evento', 'status', 'data_inscricao')
    list_filter = ('status', 'papel_evento', 'evento')
    search_fields = ('usuario__username', 'usuario__first_name', 'evento__titulo')
    inlines = [RespostaInscricaoInline]

admin.site.register(CampoEvento)
admin.site.register(RespostaInscricao)
