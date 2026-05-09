# Product Requirements Document (PRD) - Módulo de Eventos e Gestão Financeira

## 1. Visão Geral
O módulo de eventos é o componente central da Plataforma Sinodal, integrando a logística de inscrições, a validação institucional (Verificação de Poderes) e o controle financeiro (Tesouraria). O sistema deve garantir que apenas participantes devidamente validados e quitados tenham acesso aos recursos restritos (Hub do Evento).

## 2. Objetivos
- **Gestão Centralizada:** Criar e gerir eventos com controle de vagas e prazos.
- **Transformação Digital:** Digitalizar o envio de credenciais de delegados (via links externos como Google Drive).
- **Controle Financeiro Ágil:** Implementar um fluxo de validação de pagamento, iniciando com conferência manual de PIX e evoluindo para integração automática.
- **Segurança de Acesso:** Garantir o Dual Check (Secretaria + Tesouraria) para liberação de acesso a documentos oficiais.

---

## 3. Fluxo Financeiro e Validação

O sistema deve permitir que o organizador escolha o tipo de gestão financeira para cada evento no momento da criação ou edição.

### 3.1. Opções de Gestão
- **Manual (Padrão):** 
    1. A liderança define o `valor_inscricao` e a `chave_pix` no cadastro do evento.
    2. O usuário preenche os dados e recebe os dados de pagamento na tela de confirmação.
    3. O usuário realiza o PIX externamente.
    4. O Tesoureiro marca o campo `pago` como `True` após conferência manual.
- **InfinitePay (Automatizado):**
    1. O sistema realiza uma chamada para a API da InfinitePay gerando um link de pagamento exclusivo.
    2. O usuário é redirecionado para o checkout ou recebe o link na tela de confirmação.
    3. A baixa ocorre automaticamente via Webhook (`pago=True` e `data_pagamento`).

---

## 4. Requisitos Técnicos - InfinitePay

### 4.1. Configurações de API
- **Autenticação:** Uso de `Bearer Token` (JWT) obtido via Client ID e Client Secret.
- **Payload:** Os valores devem ser convertidos para centavos (inteiros). Ex: R$ 50,00 -> `5000`.
- **Campos Obrigatórios:** `items`, `redirect_url`, `webhook_url`.
- **Metadados:** Enviar o `inscricao_id` nos metadados ou campos extras para facilitar a conciliação no retorno do webhook.

### 4.2. Segurança e Confiabilidade
- **Validação de Webhook:** Implementar verificação de autenticidade da notificação.
- **Polling/Fallback:** Implementar um comando de console (cron job) que consulta o status de links pendentes via endpoint `payment_check` caso o webhook falhe.
- **Logs:** Registrar todas as transações e respostas da API para auditoria.

---

## 5. Matriz de Aprovação e Acessos

O acesso ao **Hub do Evento** (onde ficam as Atas, Relatórios e Propostas) depende do cumprimento dos requisitos baseados no papel do usuário:

| Papel do Inscrito | Requisito 1: Tesouraria | Requisito 2: Secretaria | Acesso ao Hub |
| :--- | :--- | :--- | :--- |
| **Delegado** | Pagamento Confirmado | Credencial Validada | Liberado |
| **Ex-Officio** | Pagamento Confirmado | Credencial Validada | Liberado |
| **Visitante** | Pagamento Confirmado | N/A | Liberado |
| **Correspondente**| Pagamento Confirmado | N/A | Liberado |

---

## 6. Bibliotecas Recomendadas

Para fortalecer a parte financeira e facilitar a evolução do sistema, recomendamos:

1.  **`django-money`**: Gerenciamento preciso de valores monetários.
2.  **`requests`**: Para chamadas de API à InfinitePay.
3.  **`python-jose` ou `PyJWT`**: Para lidar com tokens JWT se necessário.
4.  **`django-import-export`**: Exportar lista de inscritos e status financeiros.

---

## 7. Modelo de Dados (Detalhamento Técnico)

### 7.1. Extensões no Modelo `Evento`
- **`tipo_financeiro`**: `IntegerField` (Choices: Manual=1, InfinitePay=2. Default: 1)
- `valor_inscricao`: `DecimalField`
- `chave_pix`: `CharField` (Obrigatório se `tipo_financeiro` for Manual)
- `instrucoes_pagamento`: `TextField`

### 7.2. Extensões no Modelo `Inscricao`
- `pago`: `BooleanField`
- `data_pagamento`: `DateTimeField`
- `credencial_validada`: `BooleanField`
- `infinitepay_link_id`: `CharField` (Para rastreio na API externa)
- `infinitepay_url`: `URLField` (Link gerado para o usuário)

---

## 8. Requisitos de Interface (UX)
- **Criação/Edição de Evento:** Campo de seleção para "Tipo de Gestão Financeira".
- **Dashboard do Tesoureiro:** Filtro rápido para "Pendentes de Pagamento".
- **Dashboard do Secretário:** Filtro rápido para "Credenciais não validadas".
- **Tela de Confirmação:** Botão "Pagar com InfinitePay" ou Instruções de PIX baseadas no tipo de evento.
- **Minhas Inscrições:** Opção de "Retomar Pagamento" se o link ainda for válido.
