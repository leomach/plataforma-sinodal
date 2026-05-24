from django.urls import path

from apps.sessoes.views import log, mesa, painel, presenca, votacao

urlpatterns = [
    # Sessões
    path('sessoes/', painel.lista_sessoes, name='lista_sessoes'),
    path('sessoes/nova/', painel.criar_sessao, name='criar_sessao'),
    path('sessoes/<int:sessao_id>/', painel.painel_sessao, name='painel_sessao'),
    path('sessoes/<int:sessao_id>/editar/', painel.editar_sessao, name='editar_sessao'),
    path('sessoes/<int:sessao_id>/status/', painel.alterar_status, name='alterar_status_sessao'),

    # Presença
    path('sessoes/<int:sessao_id>/leitor/', presenca.leitor_presenca, name='leitor_presenca'),
    path('sessoes/<int:sessao_id>/presenca/toggle/', presenca.toggle_presenca, name='toggle_presenca'),
    path('sessoes/<int:sessao_id>/presenca/contagem/', presenca.contagem_presenca, name='contagem_presenca'),

    # Votações (liderança)
    path('sessoes/<int:sessao_id>/votacoes/nova/', votacao.criar_votacao, name='criar_votacao'),
    path('sessoes/<int:sessao_id>/votacoes/<int:votacao_id>/encerrar/', votacao.encerrar_votacao, name='encerrar_votacao'),
    path('sessoes/<int:sessao_id>/votacoes/<int:votacao_id>/minerva/', votacao.voto_minerva, name='voto_minerva'),
    path('sessoes/<int:sessao_id>/votacoes/<int:votacao_id>/resultado/', votacao.resultado_votacao, name='resultado_votacao'),

    # Voto do delegado
    path('votacoes/<int:votacao_id>/votar/', votacao.registrar_voto, name='registrar_voto'),

    # Log / Linha do tempo
    path('sessoes/<int:sessao_id>/log/adicionar/', log.adicionar_log_manual, name='adicionar_log_manual'),
    path('sessoes/<int:sessao_id>/log/exportar/', log.exportar_log, name='exportar_log'),
    path('sessoes/<int:sessao_id>/log/excluir/<int:log_id>/', log.excluir_log_manual, name='excluir_log_manual'),

    # Mesa Diretora
    path('sessoes/<int:sessao_id>/mesa/', mesa.compor_mesa, name='compor_mesa'),
    path('sessoes/<int:sessao_id>/mesa/transferir/', mesa.transferir_presidencia, name='transferir_presidencia'),

    # QR Code
    path('inscricoes/<int:inscricao_id>/regenerar-qr/', presenca.regenerar_qrcode, name='regenerar_qrcode'),
]
