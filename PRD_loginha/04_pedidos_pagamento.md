# Etapa 04 — Pedidos e pagamento

## Objetivo

Implementar o ciclo completo de um pedido: criação a partir do carrinho (já feito na Etapa 03), geração do link InfinitePay, recebimento do webhook, confirmação do pagamento, envio de e-mails. Ao final, o usuário consegue completar uma compra real do começo ao fim.

## Pré-requisitos

- Etapa 03 concluída
- App `apps.pagamentos` funcionando (já implementado e auditado)

## Modelo `Pedido`

Já mencionado na Etapa 03. Definição completa aqui:

| Campo | Tipo | Notas |
|---|---|---|
| `usuario` | FK(User, on_delete=PROTECT) | |
| `numero` | CharField(20, unique=True, db_index=True) | Ex.: `PED-2026-00042` (gerado no save) |
| `status` | IntegerField(choices=PEDIDO_STATUS_CHOICES) | |
| `modo_entrega` | IntegerField(choices=ENTREGA_MODO_CHOICES, default=RETIRADA) | |
| `valor_total` | DecimalField(10, 2) | Snapshot no momento do checkout |
| `valor_frete` | DecimalField(10, 2, default=0) | 0 nesta etapa; Etapa 05 implementa |
| `observacoes` | TextField(blank=True) | Observação geral do pedido |
| `contato_nome` | CharField(150) | Snapshot |
| `contato_email` | EmailField | Snapshot |
| `contato_whatsapp` | CharField(20) | Snapshot |
| `evento` | FK(Evento, null=True, blank=True, on_delete=SET_NULL) | Se todo o pedido for de produtos de um único evento |
| `infinitepay_url` | URLField(500, blank=True) | Link de pagamento |
| `infinitepay_invoice_slug` | CharField(100, blank=True) | |
| `transacao` | FK(TransacaoInfinitePay, null=True, on_delete=SET_NULL) | Preenchido pelo handler |
| `criado_em` | DateTimeField(auto_now_add=True) | |
| `data_pagamento` | DateTimeField(null=True, blank=True) | |
| `data_reserva_expira` | DateTimeField(null=True) | Reserva de 15 min — se não pagar até aqui, estoque volta |
| `cancelado_em` | DateTimeField(null=True) | |
| `motivo_cancelamento` | CharField(255, blank=True) | |

`Meta.ordering = ['-criado_em']`

Métodos:
- `gerar_numero()` → `PED-YYYY-NNNNN` (sequencial por ano)
- `reservar_estoque()` → decrementa em todos os `ItemPedido` (atômico)
- `restaurar_estoque()` → incrementa de volta (em cancelamento/expiração)
- `marcar_pago(transacao)` → muda status, salva data, envia e-mail
- `expirou()` → property `bool` (now > data_reserva_expira and status == AGUARDANDO_PAGAMENTO)

## Modelo `ItemPedido`

| Campo | Tipo | Notas |
|---|---|---|
| `pedido` | FK(Pedido, on_delete=CASCADE, related_name='itens') | |
| `variacao` | FK(VariacaoProduto, on_delete=PROTECT) | PROTECT para não perder histórico |
| `produto_nome` | CharField(200) | Snapshot |
| `variacao_nome` | CharField(60) | Snapshot |
| `quantidade` | PositiveIntegerField | |
| `preco_unitario` | DecimalField(10, 2) | Snapshot |
| `observacao` | CharField(255, blank=True) | |

Property:
- `subtotal` → `preco_unitario * quantidade`

> Snapshots são importantes: se o produto for renomeado ou removido, o pedido continua legível.

## Constantes (core/constants.py)

Expandir o bloco da Etapa 03:

```python
PEDIDO_AGUARDANDO_PAGAMENTO = 1
PEDIDO_PAGO = 2
PEDIDO_AGUARDANDO_PRODUCAO = 3   # pré-venda (Etapa 07)
PEDIDO_PRONTO = 4                # pronto para retirada/envio (Etapa 05)
PEDIDO_ENVIADO = 5               # Etapa 05
PEDIDO_ENTREGUE = 6              # Etapa 05
PEDIDO_CANCELADO = 9
PEDIDO_REEMBOLSADO = 10

PEDIDO_STATUS_CHOICES = [
    (PEDIDO_AGUARDANDO_PAGAMENTO, _('Aguardando pagamento')),
    (PEDIDO_PAGO, _('Pago')),
    (PEDIDO_AGUARDANDO_PRODUCAO, _('Aguardando produção')),
    (PEDIDO_PRONTO, _('Pronto para retirada/envio')),
    (PEDIDO_ENVIADO, _('Enviado')),
    (PEDIDO_ENTREGUE, _('Entregue')),
    (PEDIDO_CANCELADO, _('Cancelado')),
    (PEDIDO_REEMBOLSADO, _('Reembolsado')),
]

# Status considerados "ativos" (pedido ainda em andamento)
PEDIDO_STATUS_ATIVOS = [
    PEDIDO_AGUARDANDO_PAGAMENTO,
    PEDIDO_PAGO,
    PEDIDO_AGUARDANDO_PRODUCAO,
    PEDIDO_PRONTO,
    PEDIDO_ENVIADO,
]

# Reserva de estoque em minutos
PEDIDO_RESERVA_MINUTOS = 15
```

## Handler de pagamento

Substituir o placeholder de `apps/loja/handlers.py`:

```python
import logging
from django.utils import timezone

from apps.pagamentos.handlers import register_payment_handler
from apps.pagamentos.services import infinitepay as ip_service
from core import constants

from . import emails
from .models import Pedido

logger = logging.getLogger(__name__)


@register_payment_handler('pedido')
def confirmar_pedido_pago(*, order_nsu, transacao, payload):
    try:
        pedido_id = int(order_nsu.split('-', 1)[1])
    except (ValueError, IndexError):
        logger.warning('loja.handler.invalid_order_nsu', extra={'order_nsu': order_nsu})
        return

    try:
        pedido = Pedido.objects.select_related('usuario').get(pk=pedido_id)
    except Pedido.DoesNotExist:
        logger.warning('loja.handler.pedido_not_found', extra={'pedido_id': pedido_id})
        return

    # Valida valor pago
    esperado_centavos = ip_service.to_centavos(pedido.valor_total + pedido.valor_frete)
    pago_centavos = transacao.paid_amount_centavos

    if pago_centavos < esperado_centavos:
        logger.error(
            'loja.handler.amount_mismatch',
            extra={
                'pedido_id': pedido_id,
                'esperado_centavos': esperado_centavos,
                'recebido_centavos': pago_centavos,
            },
        )
        return

    transacao.valor_validado = True
    transacao.save(update_fields=['valor_validado'])

    if pedido.status == constants.PEDIDO_PAGO:
        return

    if pedido.status not in [constants.PEDIDO_AGUARDANDO_PAGAMENTO]:
        logger.warning(
            'loja.handler.unexpected_status',
            extra={'pedido_id': pedido_id, 'status': pedido.status},
        )
        return

    pedido.status = constants.PEDIDO_PAGO
    pedido.data_pagamento = timezone.now()
    pedido.transacao = transacao
    if transacao.invoice_slug and not pedido.infinitepay_invoice_slug:
        pedido.infinitepay_invoice_slug = transacao.invoice_slug
    pedido.save()

    emails.enviar_pedido_pago(pedido)
```

## E-mails

Criar `apps/loja/emails.py`:

```python
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def _send(assunto, template, context, destinatario):
    html = render_to_string(template, context)
    send_mail(
        subject=assunto, message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[destinatario],
        html_message=html, fail_silently=True,
    )


def enviar_pedido_criado(pedido):
    _send(
        f'[Plataforma Sinodal] Pedido recebido — {pedido.numero}',
        'emails/loja/pedido_criado.html',
        {'pedido': pedido},
        pedido.contato_email,
    )


def enviar_pedido_pago(pedido):
    _send(
        f'[Plataforma Sinodal] Pagamento confirmado — {pedido.numero}',
        'emails/loja/pedido_pago.html',
        {'pedido': pedido},
        pedido.contato_email,
    )
```

Criar templates:
- `templates/emails/loja/pedido_criado.html`
- `templates/emails/loja/pedido_pago.html`

## Views adicionais

```python
# apps/loja/urls.py (adicionar)
urlpatterns += [
    path('pedido/<int:pedido_id>/', pedido.detalhe, name='pedido_detalhe'),
    path('pedido/<int:pedido_id>/pagar/', pedido.gerar_link_pagamento, name='pedido_pagar'),
    path('pedido/<int:pedido_id>/cancelar/', pedido.cancelar, name='pedido_cancelar'),
    path('meus-pedidos/', pedido.historico, name='meus_pedidos'),
]
```

### `pedido.detalhe(request, pedido_id)`

- `get_object_or_404(Pedido, id=pedido_id, usuario=request.user)`
- Se `status == AGUARDANDO_PAGAMENTO`:
  - Se `pedido.expirou()`: cancela o pedido, restaura estoque, mostra mensagem
  - Senão: mostra botão "Pagar agora" (gera link InfinitePay)
- Se `status == PAGO`: mostra detalhes, comprovante (link `transacao.receipt_url`)
- Se outros status: mostra status + próximas instruções

### `pedido.gerar_link_pagamento(request, pedido_id)`

Idêntico ao `apps.eventos.views.gerar_link_pagamento` mas para Pedido:

- Reutiliza link existente se houver e usuário não pediu `?force=1`
- Senão, chama `apps.pagamentos.services.infinitepay.criar_link(
      order_nsu=f'pedido-{pedido.id}',
      descricao=f'Pedido {pedido.numero}',
      valor=pedido.valor_total + pedido.valor_frete,
      customer_name=pedido.contato_nome,
      customer_email=pedido.contato_email,
      redirect_url=...,
      webhook_url=...,
  )`
- Salva `infinitepay_url` e `infinitepay_invoice_slug` no pedido
- Redireciona para `infinitepay_url`

### `pedido.cancelar(request, pedido_id)` (POST)

- Só permite cancelar se `status == AGUARDANDO_PAGAMENTO`
- Marca `cancelado_em`, muda status, restaura estoque atomicamente
- Mensagem de sucesso

### `pedido.historico(request)`

Lista pedidos do usuário ordenados por `-criado_em`.

## Comando de cleanup de pedidos expirados

`apps/loja/management/commands/expirar_pedidos_pendentes.py`:

```python
class Command(BaseCommand):
    help = 'Cancela pedidos AGUARDANDO_PAGAMENTO cuja reserva expirou e restaura estoque.'

    def handle(self, *args, **opts):
        agora = timezone.now()
        pendentes = Pedido.objects.filter(
            status=constants.PEDIDO_AGUARDANDO_PAGAMENTO,
            data_reserva_expira__lt=agora,
        )
        for p in pendentes:
            with transaction.atomic():
                p.restaurar_estoque()
                p.status = constants.PEDIDO_CANCELADO
                p.cancelado_em = agora
                p.motivo_cancelamento = 'Reserva expirou sem pagamento'
                p.save()
        self.stdout.write(f'Cancelados: {pendentes.count()}')
```

Não precisa de cron — pode ser executado manualmente, ou via comando manual.

## Templates

```
templates/loja/
└── pedido/
    ├── detalhe.html          # /loja/pedido/<id>/
    ├── historico.html        # /loja/meus-pedidos/
    └── _linha_pedido.html    # card de pedido no histórico
```

### `pedido/detalhe.html` — comportamento por status

| Status | Conteúdo |
|---|---|
| `AGUARDANDO_PAGAMENTO` | Resumo + botão "Pagar agora" + cronômetro de expiração + botão "Cancelar" |
| `PAGO` | Resumo + "Pagamento confirmado em ..." + link do comprovante |
| `PRONTO` (Etapa 05) | "Pronto para retirada em ..." |
| `ENVIADO` (Etapa 05) | "Enviado em ... — Código de rastreio: ..." |
| `CANCELADO` | "Pedido cancelado em ... — motivo: ..." |

## Critérios de aceite

- [ ] Confirmação do checkout (Etapa 03) gera Pedido com `data_reserva_expira` = now + 15 min
- [ ] Numeração: pedidos saem com formato `PED-2026-00001`, `PED-2026-00002`, etc.
- [ ] Em `/loja/pedido/<id>/`, usuário vê seus dados, itens e botão "Pagar agora"
- [ ] Clicar em "Pagar agora" gera link InfinitePay e redireciona
- [ ] Após pagar via InfinitePay, webhook é chamado:
  - [ ] Cria `TransacaoInfinitePay` (já testado na auditoria)
  - [ ] Handler `confirmar_pedido_pago` é disparado
  - [ ] Pedido muda para `PAGO`
  - [ ] E-mail de confirmação é enviado
- [ ] Ataque de fraude: webhook falso com `paid_amount` baixo → pedido NÃO marcado como pago (já testado na auditoria)
- [ ] Cancelar pedido restaura estoque
- [ ] Comando `expirar_pedidos_pendentes` cancela pedidos com reserva vencida e restaura estoque
- [ ] `/loja/meus-pedidos/` lista pedidos do usuário com status colorido
- [ ] Usuário não consegue ver pedido de outro usuário (404)

## Casos de uso cobertos

- CU-02 completo (compra avulsa)
- Parte de CU-01 (pagamento de pré-venda — finalização em Etapa 07)

## Estimativa

1–1,5 dia (8–12 horas com Claude Code).

## Pontos de atenção

1. **Order NSU padronizado**: `pedido-<id>` — não inventar outro formato, o handler está registrado para esse prefixo.
2. **Snapshot de e-mail/nome do contato** ao criar o Pedido: evita problemas se o usuário mudar o cadastro depois.
3. **Reserva expirada**: o estoque só é restaurado **uma vez**. O comando deve usar `select_for_update` para evitar dupla restauração.
4. **Frete em zero**: Etapa 05 vai mexer no cálculo. Hoje `valor_frete=0` sempre.
5. **Handler de pagamento já registrado**: confirme com `apps.pagamentos.handlers.get_registered_prefixes()` que retorna `['inscricao', 'pedido']`.
6. **E-mails opcionais**: usar `fail_silently=True` para não derrubar handler se SMTP falhar.
