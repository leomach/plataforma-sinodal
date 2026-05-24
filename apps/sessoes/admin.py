from django.contrib import admin

from .models import MembroDaMesa, Sessao, Presenca, CredencialQRCode, Votacao, VotoParticipante, EventoLog


class MembroDaMesaInline(admin.TabularInline):
    model = MembroDaMesa
    extra = 0
    readonly_fields = ['assumiu_em']
    fields = ['cargo', 'inscricao', 'assumiu_em', 'encerrou_em']


@admin.register(Sessao)
class SessaoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'evento', 'data_hora', 'status', 'is_verificacao_poderes']
    list_filter = ['status', 'is_verificacao_poderes', 'evento']
    search_fields = ['nome', 'evento__titulo']
    ordering = ['evento', 'data_hora']
    inlines = [MembroDaMesaInline]


@admin.register(Presenca)
class PresencaAdmin(admin.ModelAdmin):
    list_display = ['inscricao', 'sessao', 'presente', 'ultima_atualizacao']
    list_filter = ['presente', 'sessao']
    search_fields = ['inscricao__usuario__first_name', 'inscricao__usuario__last_name']


@admin.register(CredencialQRCode)
class CredencialQRCodeAdmin(admin.ModelAdmin):
    list_display = ['inscricao', 'token', 'ativo', 'gerado_em']
    list_filter = ['ativo']
    search_fields = ['inscricao__usuario__username', 'token']
    readonly_fields = ['token', 'gerado_em']


class VotoParticipanteInline(admin.TabularInline):
    model = VotoParticipante
    extra = 0
    readonly_fields = ['inscricao', 'voto', 'votado_em']


@admin.register(Votacao)
class VotacaoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'sessao', 'status', 'resultado', 'criada_em']
    list_filter = ['status', 'resultado', 'sessao']
    inlines = [VotoParticipanteInline]


@admin.register(EventoLog)
class EventoLogAdmin(admin.ModelAdmin):
    list_display = ['sessao', 'tipo', 'descricao', 'timestamp', 'usuario']
    list_filter = ['tipo', 'sessao']
    readonly_fields = ['sessao', 'tipo', 'descricao', 'timestamp', 'usuario']
    ordering = ['-timestamp']


@admin.register(MembroDaMesa)
class MembroDaMesaAdmin(admin.ModelAdmin):
    list_display = ['sessao', 'inscricao', 'cargo', 'assumiu_em', 'encerrou_em']
    list_filter = ['cargo', 'sessao']
    search_fields = ['inscricao__usuario__first_name', 'inscricao__usuario__last_name']
    ordering = ['sessao', 'cargo', 'assumiu_em']
    readonly_fields = ['assumiu_em']
