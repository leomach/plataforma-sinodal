# Configuração de E-mail (Resend + Railway)

Guia para ativar as **notificações automáticas por e-mail** em produção.

## Por que Resend (e não SMTP/Gmail)?

A **Railway bloqueia todas as portas SMTP de saída** (25, 465, 587, 2525) nos planos
**Free, Trial e Hobby** — só o plano Pro libera. Este projeto está no plano Hobby, então
qualquer envio via SMTP (incluindo Gmail) **não funciona** em produção.

A solução é usar o **Resend**, que envia por **API HTTP (porta 443)** — que nunca é bloqueada.
O código continua usando o `send_mail` normal do Django; só o *backend* muda, via a
biblioteca `django-anymail` (já instalada).

> ⚠️ **Não use um endereço `@gmail.com` como remetente.** Desde 2024 o Gmail aplica DMARC
> `p=quarantine`: e-mails enviados "de" um `@gmail.com` por serviços terceiros são
> rejeitados ou caem em spam. O remetente precisa ser de um **domínio próprio verificado**.

## O que já está pronto no código

| Arquivo | O que faz |
|---|---|
| `core/settings.py` | Backend de e-mail configurável por env var; credenciais do Resend em `ANYMAIL`; `LOGGING` para falhas aparecerem nos logs |
| `apps/eventos/emails.py` | As 3 notificações (pagamento confirmado, credencial validada, inscrição aprovada). Falhas são **registradas em log**, não somem mais silenciosamente |
| `apps/eventos/management/commands/testar_email.py` | Comando `testar_email` para validar o envio |
| `pyproject.toml` | Dependência `django-anymail` |

**Nenhuma alteração de código é necessária.** Basta seguir os passos abaixo.

---

## Passo a passo

### 1. Criar conta no Resend

Acesse <https://resend.com> e crie uma conta.
Plano gratuito: **3.000 e-mails/mês** (100/dia) — suficiente para o volume do projeto.

### 2. Verificar o domínio

No painel do Resend: **Domains → Add Domain** e informe o domínio, por exemplo:

```
sinodalgaranhuns.com.br
```

> 💡 Boa prática: em vez do domínio raiz, você pode usar um **subdomínio de envio**
> (ex.: `mail.sinodalgaranhuns.com.br`). Isso isola a reputação de envio do domínio principal.
> O remetente ficaria `noreply@mail.sinodalgaranhuns.com.br`.

O Resend vai gerar **registros DNS** (SPF + DKIM), algo como:

| Tipo | Nome | Valor |
|---|---|---|
| TXT (SPF) | `send` (ou `send.mail`) | `v=spf1 include:amazonses.com ~all` |
| CNAME/TXT (DKIM) | `resend._domainkey` | *(valor gerado pelo Resend)* |
| MX (opcional) | `send` | `feedback-smtp.sa-east-1.amazonses.com` |

> Os valores exatos são exibidos no painel — **copie os que o Resend mostrar**, não os do
> exemplo acima.

Adicione esses registros no **painel de DNS do seu domínio** (onde o domínio está registrado
— Registro.br, Cloudflare, etc.) e clique em **Verify** no Resend. A propagação leva de
alguns minutos a algumas horas.

### 3. Gerar a API Key

No painel do Resend: **API Keys → Create API Key**.
Copie a chave (formato `re_xxxxxxxxxxxx`) — ela só aparece uma vez.

### 4. Definir as variáveis de ambiente na Railway

No painel da Railway: **seu serviço → aba Variables** → adicione:

```
EMAIL_BACKEND=anymail.backends.resend.EmailBackend
RESEND_API_KEY=re_sua_chave_aqui
DEFAULT_FROM_EMAIL=noreply@sinodalgaranhuns.com.br
```

> `DEFAULT_FROM_EMAIL` **precisa** usar o domínio verificado no passo 2.

A Railway vai reiniciar o serviço automaticamente ao salvar.

### 5. Testar o envio em produção

No shell da Railway (ou via `railway run`):

```bash
python manage.py testar_email seu-email-real@gmail.com
```

O comando imprime a configuração detectada e envia uma mensagem de teste.
Se chegar na sua caixa de entrada (confira o spam também), está tudo funcionando —
as 3 notificações automáticas passarão a ser enviadas.

---

## Desenvolvimento local

Em dev, o `.env` mantém o backend **console** (imprime o e-mail no terminal, não envia):

```
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@sinodalgaranhuns.com.br
RESEND_API_KEY=
```

Se quiser testar o envio real localmente, basta preencher `RESEND_API_KEY` e trocar o
`EMAIL_BACKEND` para `anymail.backends.resend.EmailBackend` no `.env`.

---

## Solução de problemas

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `testar_email` diz "aceito" mas o e-mail não chega | Domínio não verificado ou caiu em spam | Confira o status do domínio no Resend e a caixa de spam |
| Erro `The from address is not verified` | `DEFAULT_FROM_EMAIL` usa domínio não verificado | Use um remetente do domínio verificado |
| Erro de autenticação / `API key invalid` | `RESEND_API_KEY` errada ou vazia | Regere a chave no Resend e atualize na Railway |
| Nada aparece / falha silenciosa | — | As falhas agora vão para os **logs da Railway** (procure por `apps.eventos.emails`) |

## Referências

- [Railway — Outbound Networking (bloqueio de SMTP)](https://docs.railway.com/networking/outbound-networking)
- [Resend — Documentação](https://resend.com/docs)
- [django-anymail — Resend backend](https://anymail.dev/en/stable/esps/resend/)
