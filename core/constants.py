from django.utils.translation import gettext_lazy as _

# Tipos de Usuário
SOCIO = 1
LIDERANCA = 2

TIPO_USUARIO_CHOICES = [
    (SOCIO, _('Sócio')),
    (LIDERANCA, _('Liderança')),
]

# Categorias de Evento
ADMINISTRATIVO = 1
COMUNHAO = 2

CATEGORIA_EVENTO_CHOICES = [
    (ADMINISTRATIVO, _('Administrativo (Congressos, CEs)')),
    (COMUNHAO, _('Comunhão (Acampamentos, Encontros)')),
]

# Papéis no Evento
PAPEL_DELEGADO = 1
PAPEL_EX_OFFICIO = 2
PAPEL_CORRESPONDENTE = 3
PAPEL_VISITANTE = 4

PAPEL_EVENTO_CHOICES = [
    (PAPEL_DELEGADO, _('Delegado (Efetivo)')),
    (PAPEL_EX_OFFICIO, _('Ex-Officio')),
    (PAPEL_CORRESPONDENTE, _('Correspondente')),
    (PAPEL_VISITANTE, _('Visitante')),
]

# Status de Inscrição
STATUS_PENDENTE = 1
STATUS_APROVADO = 2
STATUS_REJEITADO = 3

STATUS_INSCRICAO_CHOICES = [
    (STATUS_PENDENTE, _('Pendente')),
    (STATUS_APROVADO, _('Aprovado')),
    (STATUS_REJEITADO, _('Rejeitado')),
]

# Tipo Financeiro do Evento
GRATUITO = 0
MANUAL = 1
INFINITEPAY = 2

TIPO_FINANCEIRO_CHOICES = [
    (GRATUITO, 'Gratuito'),
    (MANUAL, 'Manual (PIX)'),
    (INFINITEPAY, 'InfinitePay'),
]

# Tipos de Campos Dinâmicos
CAMPO_TEXTO = 1
CAMPO_NUMERO = 2
CAMPO_SELECAO = 3
CAMPO_CHECKBOX = 4

TIPO_CAMPO_CHOICES = [
    (CAMPO_TEXTO, _('Texto')),
    (CAMPO_NUMERO, _('Número')),
    (CAMPO_SELECAO, _('Seleção (Dropdown)')),
    (CAMPO_CHECKBOX, _('Checkbox')),
]

# Status de Sessão
SESSAO_EM_BREVE = 1
SESSAO_CHAMADA = 2
SESSAO_ABERTA = 3
SESSAO_ENCERRADA = 4

SESSAO_STATUS_CHOICES = [
    (SESSAO_EM_BREVE, _('Em Breve')),
    (SESSAO_CHAMADA, _('Chamada')),
    (SESSAO_ABERTA, _('Aberta')),
    (SESSAO_ENCERRADA, _('Encerrada')),
]

SESSAO_STATUS_ATIVOS = [SESSAO_CHAMADA, SESSAO_ABERTA]

# Status de Votação
VOTACAO_ABERTA = 1
VOTACAO_EMPATADA = 2
VOTACAO_ENCERRADA = 3

VOTACAO_STATUS_CHOICES = [
    (VOTACAO_ABERTA, _('Aberta')),
    (VOTACAO_EMPATADA, _('Aguardando Voto de Minerva')),
    (VOTACAO_ENCERRADA, _('Encerrada')),
]

# Resultado de Votação
VOTACAO_APROVADA = 1
VOTACAO_REJEITADA = 2

VOTACAO_RESULTADO_CHOICES = [
    (VOTACAO_APROVADA, _('Aprovada')),
    (VOTACAO_REJEITADA, _('Rejeitada')),
]

# Voto do Participante
VOTO_FAVOR = 1
VOTO_CONTRA = 2
VOTO_ABSTER = 3

VOTO_CHOICES = [
    (VOTO_FAVOR, _('A Favor')),
    (VOTO_CONTRA, _('Contra')),
    (VOTO_ABSTER, _('Abster-se')),
]

# Tipo de Log de Sessão
LOG_AUTO = 1
LOG_MANUAL = 2

LOG_TIPO_CHOICES = [
    (LOG_AUTO, _('Automático')),
    (LOG_MANUAL, _('Manual')),
]

# Cargos da Mesa Diretora
CARGO_PRESIDENTE = 1
CARGO_VICE_PRESIDENTE = 2
CARGO_PRIMEIRO_SECRETARIO = 3
CARGO_SEGUNDO_SECRETARIO = 4
CARGO_TESOUREIRO = 5
CARGO_SECRETARIO_EXECUTIVO = 6

CARGO_MESA_CHOICES = [
    (CARGO_PRESIDENTE, _('Presidente da Mesa')),
    (CARGO_VICE_PRESIDENTE, _('Vice-Presidente')),
    (CARGO_PRIMEIRO_SECRETARIO, _('1º Secretário')),
    (CARGO_SEGUNDO_SECRETARIO, _('2º Secretário')),
    (CARGO_TESOUREIRO, _('Tesoureiro')),
    (CARGO_SECRETARIO_EXECUTIVO, _('Secretário Executivo')),
]
