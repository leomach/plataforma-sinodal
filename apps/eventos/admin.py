from django.contrib import admin
from .models import Evento, CampoEvento, Inscricao, RespostaInscricao, Sessao, Presenca, DocumentoEvento

class CampoEventoInline(admin.TabularInline):
    model = CampoEvento
    extra = 1

class DocumentoEventoInline(admin.TabularInline):
    model = DocumentoEvento
    extra = 1

class SessaoInline(admin.TabularInline):
    model = Sessao
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

@admin.register(Sessao)
class SessaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'evento', 'data_hora')
    list_filter = ('evento',)

@admin.register(Presenca)
class PresencaAdmin(admin.ModelAdmin):
    list_display = ('sessao', 'inscricao', 'presente')
    list_filter = ('sessao', 'presente')

admin.site.register(CampoEvento)
admin.site.register(RespostaInscricao)
admin.site.register(DocumentoEvento)
