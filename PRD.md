# Product Requirements Document (PRD) - Módulo de Eventos e Gestão Financeira
**Versão:** 2.0 | **Atualizado em:** 2026-05-09

---

## 1. Visão Geral

O módulo de eventos é o componente central da Plataforma Sinodal, integrando a logística de inscrições, a validação institucional (Verificação de Poderes) e o controle financeiro (Tesouraria). O sistema deve garantir que apenas participantes devidamente validados e quitados tenham acesso aos recursos restritos (Hub do Evento).

**Decisão de papéis:** Não há roles dedicados de "Tesoureiro" ou "Secretário". Qualquer usuário com `tipo = LIDERANÇA` acumula todas as permissões administrativas: aprovação de credenciais, confirmação de pagamentos e gestão de eventos.

---

## 2. Objetivos

- **Gestão Centralizada:** Criar e gerir eventos com controle de vagas e prazos.
- **Transformação Digital:** Digitalizar o envio de credenciais de delegados (via links externos como Google Drive).
- **Controle Financeiro Ágil:** Fluxo de validação manual (PIX) e automatizado (InfinitePay).
- **Segurança de Acesso:** Garantir o Dual Check (credencial + pagamento) para delegados e ex-officio, com aprovação automática ao completar os requisitos.

---

## 3. Tipos de Evento e Fluxo Financeiro

O organizador define o tipo ao criar ou editar o evento. O campo `tipo_financeiro` rege todo o fluxo da inscrição.

### 3.1. Gratuito (valor_inscricao = 0)

- Não há nenhum fluxo financeiro na plataforma.
- O campo InfinitePay **não deve ser exibido** no formulário quando `valor_inscricao = 0`.
- **Aprovação automática:**
  - Visitantes e Correspondentes: aprovados imediatamente ao se inscrever.
  - Delegados e Ex-Officio: aprovados quando a liderança marcar `credencial_validada = True`.

### 3.2. Pago — Manual (PIX)

1. A liderança define `valor_inscricao` e `chave_pix` no cadastro do evento.
2. O usuário preenche os dados e recebe as instruções de PIX na tela de confirmação.
3. O usuário realiza o PIX externamente.
4. A liderança acessa o painel de inscrições e confirma o pagamento clicando em **"Confirmar Pagamento"** (seta `pago = True` e `data_pagamento = now()`).
5. Ao confirmar, o sistema dispara e-mail de notificação para o participante (ver seção 7).

### 3.3. Pago — InfinitePay (Automatizado)

1. Ao finalizar a inscrição, o sistema chama a API da InfinitePay e gera um link de pagamento.
2. O link é exibido ao usuário na tela de confirmação junto com botão "Pagar agora".
3. O usuário é redirecionado para o checkout da InfinitePay.
4. A baixa ocorre automaticamente via Webhook (`pago = True`, `data_pagamento = now()`).
5. **Não é enviado e-mail** pelo sistema neste fluxo, pois a InfinitePay envia notificação própria ao pagador.
6. A liderança **não precisa** confirmar o pagamento manualmente.

---

## 4. Máquina de Estados — Aprovação da Inscrição

A lógica de aprovação é centralizada no método `Inscricao.save()` e calculada automaticamente a cada save, sem intervenção manual para o campo `status`.

```
status = PENDENTE (padrão)

Condição de APROVAÇÃO por papel:
  ┌─────────────────────────────────────────────────────────────┐
  │ VISITANTE / CORRESPONDENTE                                  │
  │   evento gratuito  → aprovado imediatamente                 │
  │   evento pago      → aprovado quando pago = True            │
  ├─────────────────────────────────────────────────────────────┤
  │ DELEGADO / EX-OFFICIO                                       │
  │   evento gratuito  → aprovado quando credencial_validada    │
  │   evento pago      → aprovado quando pago E credencial_val. │
  └─────────────────────────────────────────────────────────────┘

Se a condição for satisfeita  → status = APROVADO
Se a condição deixar de ser satisfeita → status = PENDENTE
```

**Implementação no `save()`:**

```python
def save(self, *args, **kwargs):
    pago_ok = self.pago or self.evento.valor_inscricao == 0
    precisa_credencial = self.papel_evento in [PAPEL_DELEGADO, PAPEL_EX_OFFICIO]

    if precisa_credencial:
        aprovado = pago_ok and self.credencial_validada
    else:
        aprovado = pago_ok

    self.status = STATUS_APROVADO if aprovado else STATUS_PENDENTE
    super().save(*args, **kwargs)
```

> **Observação:** O campo `status` deixa de ser editado manualmente pela liderança. Os botões de ação no painel de inscrições passam a ser **"Confirmar Pagamento"** e **"Validar Credencial"** (ações independentes), e o status é recalculado automaticamente a cada ação.

---

## 5. Interface — Painel de Inscrições (Liderança)

### 5.1. Botões de Ação por Papel

| Papel | Botão 1 | Botão 2 |
|-------|---------|---------|
| Visitante / Correspondente (pago) | ✅ Confirmar Pagamento | — |
| Delegado / Ex-Officio (pago) | ✅ Confirmar Pagamento | ✅ Validar Credencial |
| Qualquer papel (gratuito + delegado) | — | ✅ Validar Credencial |
| Qualquer papel (gratuito + visitante) | — | — (já aprovado) |

Quando `tipo_financeiro = INFINITEPAY`, o botão **"Confirmar Pagamento"** é omitido (confirmação é automática via webhook).

### 5.2. Filtros no Painel

- Filtro: **Pendentes de Pagamento** (`pago = False` e `evento.valor_inscricao > 0`)
- Filtro: **Credencial Pendente** (`credencial_validada = False` e papel é delegado/ex-officio)
- Filtro: **Aprovados** (`status = APROVADO`)

---

## 6. Integração InfinitePay

### 6.1. Autenticação

- **Método:** Bearer Token (OAuth2 — Client Credentials Flow).
- **Variáveis de ambiente:**
  ```
  INFINITEPAY_CLIENT_ID=...
  INFINITEPAY_CLIENT_SECRET=...
  INFINITEPAY_HANDLE=...         # InfiniteTag sem o símbolo $
  INFINITEPAY_WEBHOOK_SECRET=... # Segredo compartilhado para validação
  INFINITEPAY_SANDBOX=False      # True em desenvolvimento
  ```
- O token é obtido via POST para o endpoint de autenticação da InfinitePay e deve ser **cacheado** (ex: Django cache backend ou variável de módulo) para evitar chamadas desnecessárias.
- Implementar renovação automática quando o token expira.

### 6.2. Criação do Link de Pagamento

**Endpoint:** `POST https://api.checkout.infinitepay.io/links`

**Payload:**

```json
{
  "handle": "{{ INFINITEPAY_HANDLE }}",
  "order_nsu": "inscricao-{{ inscricao.id }}",
  "redirect_url": "https://plataforma.com/eventos/{{ slug }}/confirmacao/",
  "webhook_url": "https://plataforma.com/webhooks/infinitepay/{{ WEBHOOK_SECRET_TOKEN }}/",
  "customer": {
    "name": "{{ user.display_name }}",
    "email": "{{ user.email }}"
  },
  "items": [
    {
      "quantity": 1,
      "price": {{ valor_em_centavos }},
      "description": "Inscrição — {{ evento.titulo }}"
    }
  ]
}
```

**Notas:**
- `valor_inscricao` deve ser convertido para centavos: `int(Decimal(valor_inscricao) * 100)`.
- O `order_nsu` usa o prefixo `inscricao-` + `inscricao.id` para garantir rastreabilidade e unicidade.
- A resposta retorna `{ "url": "https://checkout.infinitepay.com.br/..." }`, que é salva em `inscricao.infinitepay_url`.

### 6.3. Fluxo de Link Expirado / Falha na Geração

- Se a chamada à API falhar na inscrição, a inscrição é salva com `infinitepay_url = None` e o usuário vê botão **"Gerar link de pagamento"** na tela de detalhes.
- Se o usuário retorna e o link já foi utilizado ou expirou, o sistema verifica via `payment_check` (ver 6.5) se o pagamento foi efetuado. Se sim, marca como pago. Se não, oferece opção de **"Gerar novo link"**.
- Ao gerar novo link, o `order_nsu` permanece o mesmo (`inscricao-{{ id }}`); a nova URL sobrescreve `infinitepay_url`.

### 6.4. Ambiente de Teste (Sandbox)

A InfinitePay não documenta oficialmente um ambiente sandbox. A estratégia adotada é:

- Com `INFINITEPAY_SANDBOX=True` (em `.env` de desenvolvimento):
  - As chamadas à API **não são realizadas**.
  - O sistema simula a criação do link e registra um log de aviso.
  - O webhook pode ser simulado localmente usando ferramentas como [ngrok](https://ngrok.com/) + Postman para disparar manualmente o payload.
- Em produção (`INFINITEPAY_SANDBOX=False`): chamadas reais à API.

### 6.5. Polling / Fallback (Management Command)

Caso o webhook falhe (timeout, servidor fora do ar, etc.), um comando de management verificará periodicamente as inscrições pendentes de pagamento:

```bash
python manage.py verificar_pagamentos_pendentes
```

**Lógica:**
1. Busca inscrições com `pago=False`, `tipo_financeiro=INFINITEPAY` e `infinitepay_url` não nula.
2. Para cada inscrição, chama `POST https://api.checkout.infinitepay.io/payment_check` com `handle`, `order_nsu` e `slug`.
3. Se `paid = True` na resposta, atualiza `pago=True` e `data_pagamento`.

Este comando deve ser agendado como cron job (ex: a cada 15 minutos via Railway Cron ou similar).

---

## 7. Segurança do Webhook

Como a InfinitePay não documenta validação por assinatura HMAC, adota-se a estratégia de **dupla verificação**:

### 7.1. Token Secreto na URL

O `webhook_url` enviado à InfinitePay inclui um token secreto aleatório gerado uma única vez e armazenado em `INFINITEPAY_WEBHOOK_SECRET`:

```
https://plataforma.com/webhooks/infinitepay/<WEBHOOK_SECRET_TOKEN>/
```

Qualquer requisição para esse endpoint sem o token correto retorna `404`.

### 7.2. Dupla Verificação (Double-Check)

Ao receber o webhook, o sistema **não confia cegamente** no payload. O fluxo é:

1. Recebe o POST com o payload da InfinitePay.
2. Extrai `order_nsu` e valida se existe uma `Inscricao` com esse identificador. Se não existir → retorna `400`.
3. Chama `payment_check` independentemente para confirmar o status do pagamento junto à InfinitePay.
4. Somente se `paid = True` na resposta do `payment_check`, atualiza `inscricao.pago = True`.
5. Retorna `200 {"success": true, "message": null}` em menos de 1 segundo.

### 7.3. Idempotência

Se o webhook for disparado mais de uma vez para o mesmo `order_nsu` (inscrição já paga), o sistema verifica `inscricao.pago` antes de processar e retorna `200` sem duplicar ações.

---

## 8. Notificações por E-mail

| Evento | Destinatário | Condição |
|--------|-------------|----------|
| Pagamento PIX confirmado manualmente | Participante | `tipo_financeiro = MANUAL` e liderança clica "Confirmar Pagamento" |
| Credencial validada | Participante | Liderança clica "Validar Credencial" |
| Inscrição aprovada (hub liberado) | Participante | `status` muda para `APROVADO` |

**InfinitePay:** O sistema **não envia e-mail** quando o pagamento é confirmado via InfinitePay (a própria InfinitePay envia comprovante ao pagador).

**Implementação:** As notificações são disparadas em `post_save` signal ou diretamente nas views de ação da liderança, usando `django.core.mail.send_mail` com templates de e-mail.

---

## 9. Modelo de Dados

### 9.1. Campos a adicionar em `Evento`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `tipo_financeiro` | `IntegerField` | Choices: `GRATUITO=0`, `MANUAL=1`, `INFINITEPAY=2`. Default: `MANUAL`. |

> `valor_inscricao = 0` implica gratuito, mas `tipo_financeiro` torna a intenção explícita e controla a UI.

### 9.2. Campos a adicionar em `Inscricao`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `infinitepay_link_id` | `CharField(max_length=100, blank=True)` | `invoice_slug` retornado no webhook, para rastreio. |
| `infinitepay_url` | `URLField(blank=True, null=True)` | URL do checkout gerada pela API. |

### 9.3. Constantes necessárias (core/constants.py)

```python
# Tipo Financeiro do Evento
GRATUITO = 0
MANUAL = 1
INFINITEPAY = 2
TIPO_FINANCEIRO_CHOICES = [(GRATUITO, 'Gratuito'), (MANUAL, 'Manual (PIX)'), (INFINITEPAY, 'InfinitePay')]
```

---

## 10. Requisitos de Interface (UX)

- **Criação/Edição de Evento:**
  - Exibir campo `tipo_financeiro` somente quando `valor_inscricao > 0` (via JS dinâmico).
  - Exibir `chave_pix` e `instrucoes_pagamento` somente quando `tipo_financeiro = MANUAL`.

- **Tela de Confirmação da Inscrição:**
  - `GRATUITO`: mensagem de confirmação direta.
  - `MANUAL`: exibir chave PIX, valor e instruções.
  - `INFINITEPAY`: botão "Pagar agora" com link para o checkout.

- **Painel de Inscrições (Liderança):**
  - Filtros: Pendentes de pagamento | Credencial pendente | Aprovados.
  - Botão "Confirmar Pagamento" (apenas para eventos manuais, inscrições não pagas).
  - Botão "Validar Credencial" (para delegados e ex-officio com credencial pendente).

- **Minhas Inscrições (Participante):**
  - Exibir botão "Retomar Pagamento" se `infinitepay_url` não for nula e `pago = False`.

---

## 11. Bibliotecas

| Biblioteca | Uso |
|-----------|-----|
| `requests` | Chamadas HTTP à API InfinitePay |
| `python-jose` ou `PyJWT` | Manipulação de JWT se necessário para autenticação InfinitePay |

---

## 12. Variáveis de Ambiente Necessárias

```env
# InfinitePay
INFINITEPAY_CLIENT_ID=
INFINITEPAY_CLIENT_SECRET=
INFINITEPAY_HANDLE=              # InfiniteTag sem $
INFINITEPAY_WEBHOOK_SECRET=      # Token aleatório para proteger a URL do webhook
INFINITEPAY_SANDBOX=True         # False em produção
```

---

## 13. Fases de Implementação

### Fase 1 — Fluxo Manual Completo
1. Adicionar `tipo_financeiro` ao model `Evento` (migration).
2. Implementar lógica de auto-aprovação no `Inscricao.save()`.
3. Refatorar painel de inscrições: dois botões de ação + filtros.
4. Implementar notificações por e-mail (pagamento manual + credencial + aprovação).
5. Ajustar tela de confirmação da inscrição por tipo de evento.

### Fase 2 — Integração InfinitePay
1. Adicionar campos `infinitepay_link_id` e `infinitepay_url` ao model `Inscricao` (migration).
2. Implementar serviço de autenticação com cache de token (`apps/eventos/services/infinitepay.py`).
3. Implementar criação de link de pagamento na view de inscrição.
4. Implementar endpoint de webhook com dupla verificação.
5. Implementar management command `verificar_pagamentos_pendentes` (polling/fallback).
6. Configurar cron job na Railway.
