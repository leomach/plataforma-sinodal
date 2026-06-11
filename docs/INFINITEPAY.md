# Integração InfinitePay — Guia de operação

Documentação do app `apps.pagamentos`, responsável por toda a integração com a InfinitePay.

## Arquitetura

```
apps/pagamentos/
├── services/infinitepay.py  → criar_link, payment_check, to_centavos
├── handlers.py              → registry (register_payment_handler, dispatch_payment_confirmed)
├── models.py                → TransacaoInfinitePay (auditoria de transações)
├── views.py                 → webhook_infinitepay (validado, idempotente, com payment_check)
└── urls.py                  → /webhooks/infinitepay/<token>/

apps/eventos/
├── handlers.py              → handler do prefixo "inscricao-"
└── services/infinitepay.py  → wrapper de compatibilidade (delega para pagamentos)
```

## Defesas de segurança implementadas

1. **Token no path** — `/webhooks/infinitepay/<token>/`. Token diferente do esperado retorna 404.
2. **Idempotência por `transaction_nsu`** — Cada transação só é processada uma vez. Webhook duplicado retorna 200 sem efeito colateral.
3. **Anti-spoof via `payment_check`** — TODO webhook chama a API real da InfinitePay para confirmar que o pagamento existe antes de aceitar. Sem isso, qualquer um com o token poderia forjar pagamentos.
4. **Validação de valor no handler** — O handler de `inscricao` compara `paid_amount_centavos` com o valor esperado do evento. Se for menor, log de erro e a transação fica `valor_validado=False` para revisão manual.
5. **Auditoria completa** — Toda transação fica registrada com payload completo (`payload_completo` em JSON), `transaction_nsu`, `receipt_url`, `capture_method`, etc.
6. **Resposta padronizada** — `{"success": true, "message": null}` para sucesso, `{"success": false, "message": "<motivo>"}` para erro. Erro 400 dispara retry pela InfinitePay.

## Fluxo de pagamento (inscrição em evento)

```
1. Usuário se inscreve no evento → apps.eventos.views.inscrever_evento
2. View chama apps.eventos.services.infinitepay.criar_link(inscricao, ...)
3. Wrapper delega para apps.pagamentos.services.infinitepay.criar_link(order_nsu='inscricao-<id>', ...)
4. Service POSTa em api.checkout.infinitepay.io/links → retorna { url, ... }
5. Usuário é redirecionado para a URL e completa o pagamento na InfinitePay
6. InfinitePay POSTa em /webhooks/infinitepay/<token>/
7. webhook_infinitepay:
   a. Valida token
   b. Parseia payload
   c. Checa idempotência (transaction_nsu único)
   d. Chama payment_check para confirmar pagamento de fato existe
   e. Cria TransacaoInfinitePay
   f. dispatch_payment_confirmed → busca handler do prefixo "inscricao" → confirmar_inscricao_paga
   g. Handler valida valor, marca inscricao.pago=True, envia e-mails
8. InfinitePay também redireciona o usuário para confirmacao_inscricao (UX)
```

## Como adicionar novo tipo de cobrança (ex.: pedido de loja)

1. No app de origem (ex.: `apps.loja`), criar `handlers.py`:

```python
from apps.pagamentos.handlers import register_payment_handler

@register_payment_handler('pedido')
def confirmar_pedido_pago(*, order_nsu, transacao, payload):
    pedido_id = int(order_nsu.split('-', 1)[1])
    # ... lógica específica ...
```

2. Importar `handlers` no `apps.py` do app (no `ready()`).
3. Ao gerar o link de pagamento, use `order_nsu=f'pedido-{pedido_id}'`.

O webhook genérico descobre automaticamente qual handler chamar via prefixo.

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `INFINITEPAY_HANDLE` | ✅ | InfiniteTag sem o `$` |
| `INFINITEPAY_WEBHOOK_SECRET` | ✅ | Token aleatório no path do webhook |
| `INFINITEPAY_SANDBOX` | ❌ | `True` para enviar header `Env: mock` (ambiente de testes) |

> Para acesso ao ambiente de testes (sandbox), solicite credenciais para `ecommerce@infinitepay.io`.

## Comando de fallback (recuperação)

Se o webhook falhar (timeout, indisponibilidade, deploy em andamento), o pagamento fica órfão. Para recuperá-lo:

```bash
python manage.py verificar_pagamentos_pendentes
```

Esse comando consulta a InfinitePay via `payment_check` para cada inscrição não confirmada e marca como paga se estiver paga.

### Configurar execução automática no Railway

O fallback deve rodar periodicamente em produção. No painel do Railway:

1. **Settings → Cron Schedule** no serviço da aplicação:
   - **Schedule:** `*/15 * * * *` (a cada 15 minutos)
   - **Command:** `python manage.py verificar_pagamentos_pendentes`

Ou via `railway.json`:

```json
{
  "cron": [
    {
      "schedule": "*/15 * * * *",
      "command": "python manage.py verificar_pagamentos_pendentes"
    }
  ]
}
```

## Testes de validação

Antes de deploy em produção, rodar localmente:

```bash
docker compose up -d db
poetry run python manage.py migrate
poetry run python manage.py runserver
```

E em outro terminal, testar os cenários de defesa (substitua o token):

```bash
TOKEN="$(grep INFINITEPAY_WEBHOOK_SECRET .env | cut -d= -f2)"

# Teste 1: Token inválido → 404
curl -X POST "http://localhost:8000/webhooks/infinitepay/TOKEN_FALSO/"

# Teste 2: Payload sem transaction_nsu → 400
curl -X POST "http://localhost:8000/webhooks/infinitepay/$TOKEN/" \
  -H "Content-Type: application/json" \
  -d '{"order_nsu": "inscricao-1"}'

# Teste 3: Webhook forjado com paid_amount baixo → 400 (payment_check rejeita)
curl -X POST "http://localhost:8000/webhooks/infinitepay/$TOKEN/" \
  -H "Content-Type: application/json" \
  -d '{
    "order_nsu": "inscricao-1",
    "transaction_nsu": "fake-nsu",
    "amount": 10000,
    "paid_amount": 100
  }'
```

Todos devem retornar erro ou 200 sem confirmar pagamento. Se algum confirmar, há regressão.

## Painel admin

A tabela `Transações InfinitePay` no Django admin (`/admin/pagamentos/transacaoinfinitepay/`) mostra todas as transações com:

- Filtros por método (pix/credit_card), validação, data
- Busca por `order_nsu`, `transaction_nsu`, `invoice_slug`
- Payload completo (read-only) para auditoria

> Registros são read-only no admin. Para reverter pagamento, edite a entidade origem (ex.: `Inscricao.pago=False`).
