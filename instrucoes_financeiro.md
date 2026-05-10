# Instrucoes de Configuracao Financeira (InfinitePay + Railway)

Este documento explica, passo a passo, tudo que voce precisa fazer para que o sistema de pagamento funcione em producao no Railway.

---

## Visao Geral do Fluxo

```text
Usuario se inscreve → plataforma cria link InfinitePay → usuario paga →
InfinitePay avisa a plataforma via webhook → inscricao aprovada automaticamente
```

Existe tambem um "plano B": a cada 15 minutos, a plataforma consulta a InfinitePay para confirmar pagamentos cujo webhook nao chegou.

---

## Parte 1 — Criar conta na InfinitePay e obter o Handle

### 1.1 Criar conta de vendedor

1. Acesse <https://infinitepay.io> e crie uma conta como estabelecimento
2. Complete o cadastro com CNPJ (ou CPF) da Sinodal
3. Aguarde a aprovacao da conta (normalmente 1 dia util)

### 1.2 Obter o Handle (InfiniteTag)

O **handle** e o seu nome de usuario no App InfinitePay (chamado de **InfiniteTag**).
Ele aparece no app ou painel com o simbolo `$` na frente — use-o **sem o `$`**.

Exemplo: se sua InfiniteTag for `$sinodal`, o handle e `sinodal`.

Guarde esse valor — ele vai para a variavel `INFINITEPAY_HANDLE`.

> **Importante:** nao existe painel de desenvolvedores nem Client ID/Secret na InfinitePay.
> A identificacao e feita exclusivamente pelo `handle`.

---

## Parte 2 — Gerar o token secreto do webhook

O webhook e a URL que a InfinitePay vai chamar quando um pagamento for confirmado.
Para proteger essa URL, usamos um token secreto que so voce conhece.

No seu computador (com o projeto ativo), execute:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Voce vera algo como:

```text
xK9mP2qLnRvTjYwZaB4sDcEuFgHi7oN1
```

Copie esse valor — ele vai para `INFINITEPAY_WEBHOOK_SECRET`.

> **Importante:** nunca compartilhe esse token.
> Ele garante que so a InfinitePay consegue acionar o webhook da sua plataforma.

---

## Parte 3 — Configurar variaveis de ambiente no Railway

### 3.1 Acessar as variaveis

1. Acesse <https://railway.app> e entre no seu projeto
2. Clique no servico do Django
3. Va em **"Variables"** no menu superior

### 3.2 Variaveis que voce deve configurar

#### Django (producao)

| Variavel            | Valor                                                                                    |
| ------------------- | ---------------------------------------------------------------------------------------- |
| `DEBUG`             | `False`                                                                                  |
| `SECRET_KEY`        | Gere um novo com: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `ALLOWED_HOSTS`     | `seuapp.railway.app,seudominio.com.br`                                                   |

#### Banco de dados

O Railway cria as variaveis do PostgreSQL automaticamente quando voce adiciona o plugin:

| Variavel       | O Railway preenche como |
| -------------- | ----------------------- |
| `DATABASE_URL` | `postgresql://...`      |

#### Email (para envio de notificacoes)

| Variavel              | Valor                                       |
| --------------------- | ------------------------------------------- |
| `EMAIL_BACKEND`       | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST`          | Ex: `smtp.gmail.com` ou `smtp.sendgrid.net` |
| `EMAIL_PORT`          | `587`                                       |
| `EMAIL_USE_TLS`       | `True`                                      |
| `EMAIL_HOST_USER`     | Seu e-mail ou usuario SMTP                  |
| `EMAIL_HOST_PASSWORD` | Senha ou chave de API do servico            |
| `DEFAULT_FROM_EMAIL`  | `noreply@seudominio.com.br`                 |

> **Dica:** para producao, recomende usar **Brevo** (antigo Sendinblue) ou **Resend** —
> sao gratuitos para volumes pequenos e faceis de configurar.

#### InfinitePay

| Variavel                    | Valor                                      |
| --------------------------- | ------------------------------------------ |
| `INFINITEPAY_HANDLE`        | Sua InfiniteTag sem o `$` (ex: `sinodal`)  |
| `INFINITEPAY_WEBHOOK_SECRET`| Token gerado na Parte 2                    |
| `INFINITEPAY_SANDBOX`       | `False` (em producao)                      |

#### Cloudinary (upload de imagens)

| Variavel        | Valor                                                                        |
| --------------- | ---------------------------------------------------------------------------- |
| `CLOUDINARY_URL`| `cloudinary://331821918459561:YnkhvmbqNHlejoQ0YQHy5CURyYw@dz2pj0d0w`       |

---

## Parte 4 — Como o webhook funciona

O webhook e informado **diretamente no payload de criacao do link**, via o campo `webhook_url`.
A plataforma faz isso automaticamente ao gerar cada link de pagamento.

A URL tem o seguinte formato:

```text
https://SEUAPP.railway.app/webhooks/infinitepay/TOKEN_SECRETO/
```

Substitua `SEUAPP.railway.app` pelo dominio do seu servico no Railway
e `TOKEN_SECRETO` pelo valor de `INFINITEPAY_WEBHOOK_SECRET`.

Exemplo:

```text
https://plataforma-sinodal.railway.app/webhooks/infinitepay/xK9mP2qLnRvTjYwZaB4sDcEuFgHi7oN1/
```

> A InfinitePay so dispara o webhook quando o pagamento e aprovado,
> portanto a plataforma ja confirma a inscricao automaticamente ao receber a notificacao.

---

## Parte 5 — Configurar o cron job no Railway (plano B)

O cron job roda a cada 15 minutos para verificar pagamentos cujo webhook nao chegou
(por exemplo, em caso de queda de conexao).

### 5.1 Criar um novo servico no Railway

1. No seu projeto Railway, clique em **"New"** → **"Empty Service"**
2. Nome: `cron-pagamentos`
3. Em **"Settings"** → **"Start Command"**:

   ```bash
   python manage.py verificar_pagamentos_pendentes
   ```

4. Em **"Settings"** → **"Cron Schedule"**:

   ```text
   */15 * * * *
   ```

5. Compartilhe as mesmas variaveis de ambiente do servico principal
   (use **"Shared Variables"** no Railway ou copie manualmente).

---

## Parte 6 — Verificar se tudo esta funcionando

### 6.1 Teste em sandbox antes de ir para producao

Antes de mudar `INFINITEPAY_SANDBOX` para `False`:

1. Crie um evento com `tipo_financeiro = InfinitePay` e algum valor
2. Faca uma inscricao
3. Na confirmacao voce vera um link simulado (`sandbox.checkout.infinitepay.io/...`)
4. O webhook nao e disparado em sandbox — use o cron job para simular a verificacao

### 6.2 Verificar os logs no Railway

Monitore os logs do servico Django para erros como:

- `Falha ao criar link InfinitePay` → verifique se o handle esta correto
- `Falha ao verificar pagamento via payment_check` → verifique handle e order_nsu

### 6.3 Checklist final antes de ligar o InfinitePay em producao

- [ ] Conta InfinitePay aprovada e ativa
- [ ] `INFINITEPAY_HANDLE` configurado (InfiniteTag sem o `$`)
- [ ] `INFINITEPAY_WEBHOOK_SECRET` gerado e configurado
- [ ] `INFINITEPAY_SANDBOX=False` no Railway
- [ ] Cron job configurado no Railway
- [ ] Email SMTP configurado
- [ ] Teste completo: criar evento pago → inscrever → pagar → verificar aprovacao automatica

---

## Resumo: variaveis do `.env` local vs Railway

| Variavel                     | Desenvolvimento (`.env`)               | Producao (Railway)            |
| ---------------------------- | -------------------------------------- | ----------------------------- |
| `DEBUG`                      | `True`                                 | `False`                       |
| `INFINITEPAY_SANDBOX`        | `True`                                 | `False`                       |
| `INFINITEPAY_HANDLE`         | vazio (sandbox nao faz chamada real)   | sua InfiniteTag sem `$`       |
| `INFINITEPAY_WEBHOOK_SECRET` | qualquer string                        | token gerado com `secrets`    |
| `EMAIL_BACKEND`              | `console`                              | `smtp`                        |

Com `INFINITEPAY_SANDBOX=True`, nenhuma chamada real e feita a API —
tudo e simulado localmente sem precisar de credenciais.
