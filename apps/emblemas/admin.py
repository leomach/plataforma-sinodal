from django.contrib import admin
from .models import CatalogoEmblema, Emblema, EmblemaUsuario


@admin.register(CatalogoEmblema)
class CatalogoEmblemaAdmin(admin.ModelAdmin):
    list_display = ('icone', 'nome', 'categoria', 'ativo', 'criado_por', 'criado_em')
    list_filter = ('categoria', 'ativo')
    search_fields = ('nome',)


@admin.register(Emblema)
class EmblemaAdmin(admin.ModelAdmin):
    list_display = ('icone', 'nome', 'evento', 'categoria', 'status', 'criado_por', 'criado_em')
    list_filter = ('status', 'categoria', 'evento')
    search_fields = ('nome',)
    readonly_fields = ('criado_em', 'publicado_em')


@admin.register(EmblemaUsuario)
class EmblemaUsuarioAdmin(admin.ModelAdmin):
    list_display = ('emblema', 'usuario', 'concedido_por', 'concedido_em', 'notificado')
    list_filter = ('notificado', 'emblema__evento')
    search_fields = ('usuario__first_name', 'usuario__last_name', 'emblema__nome')
    readonly_fields = ('concedido_em',)
