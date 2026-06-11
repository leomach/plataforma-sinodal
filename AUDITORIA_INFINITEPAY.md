# Auditoria Técnica — Integração InfinitePay

> **Veredicto curto:** A integração **funciona para o caso de uso atual (inscrições de eventos)**, mas tem **6 problemas críticos e 8 problemas médios** que precisam ser resolvidos antes de virar coração de uma lojinha. Nenhum é grave o suficiente para impedir o uso, mas alguns são vulnerabilidades de segurança que permitiriam fraude.
>
> **Status atual:** ⚠️ Funcional, mas inseguro e incompleto para e-commerce.
> **Tempo para deixar 100%:** 1–2 dias com Claude Code.

---

## 1. Inventário do que existe hoje

| Arquivo | Função |
|---|---|
| `apps/eventos/services/infinitepay.py` | Service com `criar_link()` e `payment_check()` |
| `apps/eventos/views.py:381–420` | Webhook `webhook_infinitepay` |
| `apps/eventos/views.py:29–47` | Helper `_verificar_pagamento_infinitepay` |
| `apps/eventos/views.py:341–378` | View `gerar_link_pagamento` (regenerar link) |
| `apps/eventos/management/commands/verificar_pagamentos_pendentes.py` | Comando manual para varrer pagamentos não confirmados |
| `apps/eventos/models.py:97–98` | Campos `infinitepay_link_id` e `infinitepay_url` em `Inscricao` |
| `core/urls.py:15` | Rota `/webhooks/infinitepay/<str:token>/` |
| `core/settings.py:146–147` | `INFINITEPAY_HANDLE` e `INFINITEPAY_WEBHOOK_SECRET` |

---

## 2. Verificação contra a documentação oficial

### ✅ O que está CORRETO

| Item | Status |
|---|---|
| URL `POST https://api.checkout.infinitepay.io/links` | ✅ Correto |
| URL `POST https://api.checkout.infinitepay.io/payment_check` | ✅ Correto |
| Header `Content-Type: application/json` | ✅ Correto |
| Sem autenticação Bearer (apenas `handle`) | ✅ Correto |
| `handle` sem o `$` | ✅ Correto (`lucas-lima-2j6`) |
| Preço em centavos | ✅ Correto |
| Campo `paid` (boolean) como indicador | ✅ Correto |
| `order_nsu` para rastrear (`inscricao-{id}`) | ✅ Correto |
| Webhook `csrf_exempt` + `require_POST` | ✅ Correto |
| Idempotência básica (`if inscricao.pago: return`) | ✅ Correto |
| Token aleatório no path do webhook | ✅ Correto |
| Try/except no parse do JSON | ✅ Correto |
| `.env` no `.gitignore` | ✅ Correto (não commitado) |

---

## 3. 🚨 Problemas CRÍTICOS (impedem virar coração da lojinha)

### 🔴 CRÍTICO #1 — Webhook confia cegamente no payload sem validar com `payment_check`

**Arquivo:** `apps/eventos/views.py:405–406`

```python
# O webhook só é disparado pela InfinitePay quando o pagamento é aprovado,
# portanto podemos confirmar diretamente sem consulta adicional.
```

**Problema:** Como a InfinitePay **não tem assinatura HMAC** no webhook, qualquer pessoa que descobrir a URL pode disparar um POST falso e marcar uma inscrição como paga. Hoje a URL contém o `WEBHOOK_SECRET` no path, o que é uma camada, mas:

- Se vazar uma única vez (logs de servidor, history do browser, screenshot), é game over
- Sem `payment_check`, não há defesa em segundo nível
- Para uma loja com produtos físicos (estoque que vai sair de armazém), o risco é financeiro real

**Como deveria ser:**

```python
@csrf_exempt
@require_POST
def webhook_infinitepay(request, token):
    if token != settings.INFINITEPAY_WEBHOOK_SECRET:
        raise Http404

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'success': False, 'message': 'invalid payload'}, status=400)

    order_nsu = payload.get('order_nsu', '')
    if not order_nsu.startswith('inscricao-'):
        return JsonResponse({'success': True, 'message': None})

    # ... obter inscrição ...

    # ⚠️ SEMPRE VALIDAR via payment_check antes de confirmar pagamento
    if not _confirmar_via_payment_check(inscricao, payload):
        return JsonResponse({'success': False, 'message': 'payment not confirmed'}, status=400)

    # Só agora confirma
    inscricao.pago = True
    # ...
```

**Severidade:** 🔴 CRÍTICA para loja. ⚠️ Aceitável para inscrições (impacto financeiro menor, lideranças aprovam manualmente).

---

### 🔴 CRÍTICO #2 — Webhook não valida `paid_amount` contra o valor esperado

**Arquivo:** `apps/eventos/views.py:407–415`

**Problema:** O webhook não verifica se o `paid_amount` recebido corresponde ao valor esperado da inscrição. Um atacante pode forjar um webhook com `paid_amount: 1` (1 centavo) e marcar a inscrição como paga.

**Como deveria ser:**

```python
amount_recebido = payload.get('paid_amount', 0)
amount_esperado = int(inscricao.evento.valor_inscricao * 100)

if amount_recebido < amount_esperado:
    logger.warning(
        'Webhook InfinitePay com paid_amount inferior ao esperado. '
        'Inscrição: %s | Esperado: %s | Recebido: %s',
        inscricao.id, amount_esperado, amount_recebido
    )
    return JsonResponse({'success': False, 'message': 'amount mismatch'}, status=400)
```

**Severidade:** 🔴 CRÍTICA.

---

### 🔴 CRÍTICO #3 — Sem auditoria de transações (perda de dados financeiros)

**Problema:** O webhook recebe campos importantes que são **descartados**:

| Campo recebido | Salvo? |
|---|---|
| `invoice_slug` | ✅ Sim (em `infinitepay_link_id`) |
| `transaction_nsu` | ❌ **DESCARTADO** |
| `amount` | ❌ **DESCARTADO** |
| `paid_amount` | ❌ **DESCARTADO** |
| `capture_method` (pix/credit_card) | ❌ **DESCARTADO** |
| `installments` | ❌ **DESCARTADO** |
| `receipt_url` (comprovante) | ❌ **DESCARTADO** |

**Consequência:** Se um cliente reclamar "paguei e não recebi", você não tem como mostrar o comprovante. Se a Receita Federal pedir histórico, você não tem.

**Solução:** Criar tabela `TransacaoInfinitePay`:

```python
class TransacaoInfinitePay(models.Model):
    inscricao = models.ForeignKey(Inscricao, ...)
    transaction_nsu = models.CharField(max_length=100, unique=True)  # ← idempotência REAL
    invoice_slug = models.CharField(max_length=100)
    amount_centavos = models.PositiveIntegerField()
    paid_amount_centavos = models.PositiveIntegerField()
    capture_method = models.CharField(max_length=20)  # pix, credit_card
    installments = models.PositiveSmallIntegerField(default=1)
    receipt_url = models.URLField(max_length=500, blank=True)
    payload_completo = models.JSONField()  # backup de tudo
    criado_em = models.DateTimeField(auto_now_add=True)
```

**Severidade:** 🔴 CRÍTICA para conformidade fiscal e suporte ao cliente.

---

### 🔴 CRÍTICO #4 — Idempotência incompleta (webhook duplicado pode reprocessar)

**Arquivo:** `apps/eventos/views.py:402–403`

```python
if inscricao.pago:
    return JsonResponse({'ok': True})
```

**Problema:** A idempotência atual é por inscrição (`pago=True`). Mas:

- E se a InfinitePay manda webhook do mesmo `transaction_nsu` duas vezes em paralelo? Race condition.
- E se houver estorno e novo pagamento? Você nunca saberia.
- E na lojinha, se o cliente comprar o mesmo produto duas vezes? `order_nsu` seria diferente, mas e se houver retry?

**Solução correta:** Usar `transaction_nsu` (UUID único) como chave de idempotência em tabela própria com `unique=True` (ver crítico #3).

**Severidade:** 🔴 CRÍTICA para loja (vendas concorrentes).

---

### 🔴 CRÍTICO #5 — Resposta do webhook não segue formato esperado pela InfinitePay

**Arquivo:** `apps/eventos/views.py:394, 400, 403, 420`

```python
return JsonResponse({'ok': True})  # ← formato não documentado
```

**Documentação oficial espera:**

```json
{ "success": true, "message": null }   // sucesso (HTTP 200)
{ "success": false, "message": "..." } // erro (HTTP 400)
```

**Consequência:** A InfinitePay pode **interpretar como erro** e disparar retentativas. Como o código atual responde 200 com payload diferente, **provavelmente** funciona na prática, mas é frágil — uma atualização no parser deles quebra tudo.

**Severidade:** 🟡 ALTA (não crítica imediata, mas frágil).

---

### 🔴 CRÍTICO #6 — Multiplicação float/Decimal em `criar_link`

**Arquivo:** `apps/eventos/services/infinitepay.py:13`

```python
valor_centavos = int(inscricao.evento.valor_inscricao * 100)
```

**Problema:** `valor_inscricao` é `DecimalField`. Multiplicar por `100` (int) **funciona** em Decimal, mas se o valor tiver mais de 2 casas decimais (ex.: vagamente possível em testes), `int()` trunca em vez de arredondar.

**Exemplos de bug:**
- `Decimal("99.99") * 100 = Decimal("9999.00")` → `int(...)` = `9999` ✅
- `Decimal("99.995") * 100 = Decimal("9999.50")` → `int(...)` = `9999` (perdeu meio centavo) ❌
- Se algum cálculo dinâmico (desconto, juros) produzir `Decimal("10.005")`, vira `1000` em vez de `1001`.

**Solução:**

```python
from decimal import Decimal, ROUND_HALF_UP
valor_centavos = int(
    (inscricao.evento.valor_inscricao * Decimal("100"))
    .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
)
```

**Severidade:** 🟡 MÉDIA hoje (valores são inteiros redondos), 🔴 CRÍTICA na loja (cupons, descontos parciais).

---

## 4. ⚠️ Problemas MÉDIOS

### #7 — `payment_check` envia payload incompleto

**Arquivo:** `apps/eventos/services/infinitepay.py:43–48`

A documentação sugere que `payment_check` precisa de `transaction_nsu` E `slug`. O código envia só `handle`, `order_nsu` e (opcionalmente) `slug`. Pode funcionar, mas não está conforme spec.

---

### #8 — Variáveis `INFINITEPAY_CLIENT_ID` e `INFINITEPAY_CLIENT_SECRET` no `.env` mas não usadas

```env
INFINITEPAY_CLIENT_ID=
INFINITEPAY_CLIENT_SECRET=
```

Não são lidas em nenhum lugar do código. Confunde quem mantém. Remover do `.env` e do `.env.example` (se existir) ou implementar autenticação OAuth se um dia for necessário.

---

### #9 — `INFINITEPAY_SANDBOX=True` não tem efeito

```env
INFINITEPAY_SANDBOX=True
```

A documentação oficial menciona sandbox via header `Env: mock`, mas o service não envia esse header. Ou seja: **mesmo com `SANDBOX=True`, todas as cobranças vão para produção real**. Isso é perigoso para testes.

**Solução:** No service, ler `settings.INFINITEPAY_SANDBOX` e injetar `Env: mock` quando True.

---

### #10 — Comando `verificar_pagamentos_pendentes` não é executado automaticamente

O comando existe mas:

- Não há cron job no Procfile (`worker:` linha ausente)
- Não há GitHub Actions, Celery beat, ou Railway scheduled job mencionado
- Em produção, só roda se alguém entrar via SSH e rodar `python manage.py verificar_pagamentos_pendentes`

**Consequência:** Se o webhook falhar (timeout, deploy em andamento, bug), o pagamento fica órfão. O usuário paga, mas a plataforma nunca confirma.

**Solução para Railway:** Adicionar um worker no Procfile ou usar [Railway Cron](https://docs.railway.app/reference/cron-jobs):

```procfile
web: ...
cron-pagamentos: python manage.py verificar_pagamentos_pendentes
```

E configurar para rodar a cada 15 minutos.

---

### #11 — Inconsistência no e-mail enviado pelo fallback

**Arquivo:** `apps/eventos/management/commands/verificar_pagamentos_pendentes.py:38`

O comando envia `enviar_inscricao_aprovada` mas **não envia `enviar_pagamento_confirmado`**. O webhook envia ambos. Resultado: cliente que pagou e foi confirmado pelo fallback **não recebe o e-mail de pagamento confirmado**.

---

### #12 — `gerar_link_pagamento` recria link toda vez

**Arquivo:** `apps/eventos/views.py:354–369`

Cada chamada cria um link novo na InfinitePay, mesmo se já houver um válido. A cada clique do usuário em "Pagar" você cria um link novo. Isso polui o painel da InfinitePay e pode causar confusão se múltiplos links forem pagos.

**Solução:** Antes de criar novo, verificar se `inscricao.infinitepay_url` ainda é válido (link da InfinitePay tem validade de 7 dias por padrão segundo a doc).

---

### #13 — Sem logs estruturados de eventos do webhook

Hoje só há `logger.exception` em erros. Eventos importantes (webhook recebido, pagamento confirmado, valor divergente) não geram log. Em produção, debugar fraude/perda de pagamento fica difícil.

**Solução:** Logar com nível `INFO` cada evento do webhook em formato estruturado (JSON):

```python
logger.info('infinitepay.webhook.received', extra={
    'order_nsu': order_nsu,
    'transaction_nsu': payload.get('transaction_nsu'),
    'amount': payload.get('paid_amount'),
})
```

---

### #14 — Race condition no `inscrever_evento`

**Arquivo:** `apps/eventos/views.py:107–111`

```python
inscricao.save()              # Cria inscrição
form.save_custom_fields(...)  # Salva campos dinâmicos
# ...
resultado = ip_service.criar_link(inscricao, ...)
Inscricao.objects.filter(pk=inscricao.pk).update(...)
```

A inscrição é salva ANTES do link ser criado. Se a chamada HTTP à InfinitePay falhar/demorar 10s, a inscrição existe sem link de pagamento. O usuário vê confirmação mas não tem como pagar (a menos que clique em "regenerar link" depois).

**Hoje** isso é mitigado pelo try/except, mas o usuário não é avisado. Em uma loja, é inaceitável — o carrinho sumiu mas o produto está pago?

---

## 5. 🟢 Pontos positivos / boas práticas já implementadas

1. ✅ Token aleatório no path do webhook (defesa em profundidade)
2. ✅ `csrf_exempt` apenas no webhook, não em outras views
3. ✅ Idempotência básica via `inscricao.pago`
4. ✅ `select_for_update()` no fluxo de inscrição (evita corrida em vagas)
5. ✅ `transaction.atomic` em `inscrever_evento`
6. ✅ Try/except envolvendo a chamada InfinitePay (não bloqueia inscrição)
7. ✅ Logger Python configurado
8. ✅ Sentry instalado (`pyproject.toml`)
9. ✅ Comando manual de fallback existe
10. ✅ Helper `_verificar_pagamento_infinitepay` reutilizável

---

## 6. Roadmap de correção (antes da lojinha)

### Fase 1 — Correções urgentes (1 dia)

- [ ] Criar model `TransacaoInfinitePay` com `transaction_nsu` único (crítico #3, #4)
- [ ] Adicionar validação de `paid_amount` no webhook (crítico #2)
- [ ] Adicionar chamada `payment_check` no webhook como verificação dupla (crítico #1)
- [ ] Corrigir resposta JSON do webhook para `{success, message}` (crítico #5)
- [ ] Corrigir conversão Decimal → centavos (crítico #6)
- [ ] Implementar sandbox real via header `Env: mock` (médio #9)

### Fase 2 — Robustez (meio dia)

- [ ] Configurar cron job para `verificar_pagamentos_pendentes` (médio #10)
- [ ] Corrigir e-mail de pagamento confirmado no fallback (médio #11)
- [ ] Adicionar logs estruturados (médio #13)
- [ ] Limpar `INFINITEPAY_CLIENT_ID/SECRET` não usadas (médio #8)
- [ ] Reutilizar link válido em vez de recriar (médio #12)

### Fase 3 — Generalização para loja (meio dia)

- [ ] Refatorar service para ser agnóstico de "inscrição" (criar abstração `Cobranca` ou usar `Generic Foreign Key`)
- [ ] Mover `apps/eventos/services/infinitepay.py` para `apps/pagamentos/services/infinitepay.py` ou `core/payments/infinitepay.py`
- [ ] Webhook genérico que despacha por tipo de `order_nsu` (`inscricao-X`, `pedido-Y`, etc.)

**Total estimado:** 2 dias úteis com Claude Code.

---

## 7. Teste manual recomendado antes da lojinha

Antes de implementar qualquer coisa nova, faça este checklist com o ambiente atual:

1. **Criar evento de teste com `tipo_financeiro=INFINITEPAY`** e valor R$ 1,00
2. **Inscrever-se como usuário comum** — verificar se link é gerado
3. **Acessar o link e completar pagamento via PIX** (R$ 1,00)
4. **Conferir no log do Django** se webhook chega
5. **Conferir no banco** se `inscricao.pago = True` e `data_pagamento` setados
6. **Conferir e-mail** de confirmação chegou
7. **Forçar erro:** desligar a internet do servidor durante o pagamento, voltar depois, rodar `python manage.py verificar_pagamentos_pendentes` — deve confirmar via fallback
8. **Teste de fraude (em ambiente isolado):** dispare manualmente o webhook com `paid_amount: 1` e veja se confirma — **se confirmar, é vulnerabilidade comprovada do crítico #2**

```bash
# Comando para teste de fraude (rode em LOCALHOST, não em produção)
curl -X POST http://localhost:8000/webhooks/infinitepay/SEU_TOKEN/ \
  -H "Content-Type: application/json" \
  -d '{
    "order_nsu": "inscricao-1",
    "invoice_slug": "fake_slug",
    "amount": 100,
    "paid_amount": 1,
    "transaction_nsu": "fake_uuid"
  }'
```

Se a inscrição 1 ficar como paga, está confirmada a vulnerabilidade.

---

## 8. Conclusão

**A integração está funcional para o uso atual** (inscrições com volume baixo, lideranças validando manualmente). Não é um lixo — tem boas práticas, é organizada, segue padrões do Django.

**Mas não está pronta para ser o coração de uma lojinha** porque:

1. **Risco de fraude real**: webhook não valida valor nem confirma via API
2. **Perda de dados financeiros**: histórico de transações não é salvo
3. **Race conditions** em alto volume
4. **Sandbox não funciona** apesar de estar configurado
5. **Não há recuperação automática** se webhook falhar

**Recomendação:** Antes de qualquer linha de código de loja, **dedicar 2 dias para a Fase 1 + Fase 2** desse roadmap. Depois a loja pode ser construída em cima de uma base sólida em 5–7 dias.

**Sem essas correções**, construir loja em cima do que existe hoje é convidar fraude.

---

*Auditoria realizada em 11/06/2026 contra código em branch `dev` (commit `025e3ee`) e documentação oficial da InfinitePay vigente.*
