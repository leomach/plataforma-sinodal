# Análise: Vale a Pena Construir uma Loja na Plataforma Sinodal?

> **TL;DR — Sim, vale. E é mais barato do que você imagina.**
> A plataforma já tem 70% da infraestrutura necessária. Com Claude Code, um módulo de loja completo pode sair em **5–10 dias úteis** de trabalho focado.

---

## 1. O que estamos falando?

Uma loja completa envolveria:

| Funcionalidade | Descrição |
|---|---|
| **Catálogo de produtos** | Produto com nome, descrição, imagem, preço |
| **Variações** | Tamanho, cor, tipo — com preço diferenciado |
| **Estoque** | Controle por variação, alerta de esgotamento |
| **Carrinho** | Adicionar, remover, alterar quantidade |
| **Checkout** | Endereço, resumo, método de pagamento |
| **Pagamentos** | PIX (0% de taxa) e cartão via InfinitePay |
| **Pedidos** | Histórico, status, confirmação por e-mail |
| **Admin** | Gestão de produtos, pedidos, estoque |

---

## 2. Vantagem decisiva: o projeto já tem quase tudo

A Plataforma Sinodal não começa do zero. Ela já possui:

### ✅ InfinitePay integrada (e funcionando)

O sistema de **eventos já usa InfinitePay** para cobrar inscrições. Existe:
- Um service `apps/eventos/services/infinitepay.py`
- Um webhook ativo em `/webhooks/infinitepay/<token>/`
- Variáveis de ambiente configuradas (`.env`)
- A lógica de geração de link, confirmação de pagamento e tratamento de webhook **já está escrita e testada em produção**

Para a loja, seria adaptar esse mesmo código — não reescrever do zero.

### ✅ Stack perfeita para e-commerce

| Recurso | Uso atual | Uso na loja |
|---|---|---|
| Django 5.1 + PostgreSQL | Core do projeto | Modelos de produto, pedido, estoque |
| HTMX | Votações, presença em tempo real | Carrinho sem page-reload, atualização de estoque |
| Tailwind CSS | Todos os templates | Cards de produto, página de checkout |
| Cloudinary | Banners de eventos | Fotos de produtos |
| `core/constants.py` | Status de inscrição, sessão, votação | Status de pedido, tipo de variação |
| `segno` (QR Code) | Credenciais de presença | QR Code de comprovante de compra |
| Sistema de e-mail | Confirmação de inscrição | Confirmação de pedido, nota fiscal |

### ✅ Arquitetura de apps já estabelecida

O projeto tem um padrão claro:
```
apps/
  eventos/     → inscrições, pagamentos, campos dinâmicos
  sessoes/     → presença, votação, mesa diretora
  hub/         → documentos
  emblemas/    → prêmios
  loja/        → ← seria mais um app aqui
```

Adicionar `apps/loja/` segue exatamente o mesmo padrão que os outros apps.

---

## 3. Complexidade real de cada módulo

### Módulo A — Produtos e Variações

**O que é:** `Produto` com nome, descrição, preço, imagens + `VariacaoProduto` com estoque.

**Dificuldade: Baixa**. É o módulo mais simples. Modelos bem definidos, nenhuma lógica especial. A parte mais trabalhosa é a interface de upload de imagens (resolvida com Cloudinary, já integrado).

```python
# Estrutura de modelos — ~80 linhas
class Produto(models.Model):
    nome, descricao, preco_base, imagem, ativo, slug

class VariacaoProduto(models.Model):
    produto, atributo, valor, preco_adicional, estoque

class ImagemProduto(models.Model):
    produto, imagem, ordem
```

**Estimativa:** 1 dia com Claude Code.

---

### Módulo B — Carrinho

**O que é:** Carrinho persistido no banco (para usuário logado) ou em sessão (anônimo). Adicionar, remover, alterar quantidade.

**Dificuldade: Média.** O desafio é sincronizar o carrinho de sessão com o banco ao fazer login, e atualizar quantidades via HTMX sem reload.

**Estimativa:** 1–2 dias com Claude Code.

---

### Módulo C — Checkout

**O que é:** Formulário de endereço de entrega, resumo do pedido, escolha do método de pagamento, confirmação.

**Dificuldade: Média.** A lógica do form é padrão Django. O mais importante é validar estoque no momento do checkout (race condition se dois usuários comprarem o último item ao mesmo tempo — resolvido com `select_for_update()`).

**Estimativa:** 1–2 dias com Claude Code.

---

### Módulo D — Integração de Pagamento (InfinitePay)

**O que é:** Gerar link de pagamento para o pedido, redirecionar o usuário, receber webhook de confirmação.

**Dificuldade: Muito Baixa — este código já existe no projeto.**

O service `infinitepay.py` de eventos já faz exatamente isso. A adaptação para pedidos de loja leva horas, não dias.

**Limitações conhecidas da InfinitePay:**
- Sem checkout transparente — usuário é redirecionado para `checkout.infinitepay.com.br`
- Sem boleto (apenas PIX e cartão de crédito)
- PIX tem 0% de taxa; cartão online começa em ~4,2%

**Estimativa:** 4–6 horas com Claude Code.

---

### Módulo E — Pedidos e Histórico

**O que é:** `Pedido` com status (aguardando, pago, enviado, entregue) + `ItemPedido` + confirmação por e-mail.

**Dificuldade: Baixa.** Estrutura de modelos simples, e-mail transacional já existe no projeto para inscrições.

**Estimativa:** 1 dia com Claude Code.

---

### Módulo F — Admin / Gestão (backoffice)

**O que é:** Interface para administrar produtos, ver pedidos, atualizar estoque.

**Dificuldade: Baixa.** O Django Admin cobre 80% disso de graça. Para uma interface customizada, o padrão de views/templates do projeto (igual ao de sessões e eventos) resolve o resto.

**Estimativa:** 1 dia com Claude Code.

---

## 4. Cronograma realista

### MVP — Loja básica funcional

> Produtos simples + carrinho + checkout + PIX/cartão via InfinitePay

| Dia | Entrega |
|---|---|
| Dia 1 | Modelos, migrations, `core/constants.py` atualizado |
| Dia 2 | Catálogo de produtos + variações + admin básico |
| Dia 3 | Carrinho com HTMX (adicionar/remover sem reload) |
| Dia 4 | Checkout + integração InfinitePay adaptada do service de eventos |
| Dia 5–6 | Webhook de confirmação, e-mail de pedido, histórico |

**Total MVP: 5–6 dias úteis de trabalho focado com Claude Code.**

### Versão Completa — Tudo que foi pedido

> Tudo do MVP + variações com preço diferenciado + controle de estoque granular + painel de gestão completo

| Semana | Entrega |
|---|---|
| Semana 1 | MVP completo e funcional |
| Semana 2 | Variações com estoque por SKU, imagens múltiplas, filtros no catálogo |
| Semana 3 | Painel admin com dashboard de pedidos, alertas de estoque baixo |
| Semana 4 | Refinamento, testes de integração, edge cases |

**Total versão completa: 3–4 semanas com Claude Code.**

---

## 5. Quanto custaria sem Claude Code?

Para referência, o mesmo escopo para um dev sênior trabalhando sozinho:

| Módulo | Sem IA | Com Claude Code |
|---|---|---|
| Modelos + migrations | 16–24h | 4–6h |
| Catálogo + admin | 8–12h | 3–4h |
| Carrinho HTMX | 16–24h | 6–8h |
| Checkout + validações | 20–32h | 6–10h |
| Integração InfinitePay | 8–16h | 2–4h (já existe código!) |
| Webhook + e-mails | 8–12h | 3–4h |
| Testes + ajustes | 16–24h | 6–10h |
| **Total** | **92–144h (12–18 dias)** | **30–46h (4–6 dias)** |

**Claude Code reduz o tempo em ~67% nesse tipo de projeto Django.**

---

## 6. O que NÃO fazer

### ❌ Não use django-oscar

É o maior framework de e-commerce para Django. Robusto, maduro, com suporte enterprise. Mas:
- Foi projetado para **ser o coração do projeto**, não para ser inserido num projeto existente
- Requer "forkar" cada app para customizar — viola a arquitetura da Plataforma Sinodal
- Curva de 1–2 semanas só para entender a arquitetura dele
- Resultado: você ganharia complexidade, não velocidade

### ❌ Não use Saleor

Plataforma headless GraphQL-first com frontend em React. O backend é Django, mas o frontend é completamente separado. Incompatível com a abordagem HTMX + Django Templates do projeto.

### ❌ Não use django-shop

Menos mantido, documentação fraca. Não agrega vantagem sobre construção própria.

---

## 7. Considerações sobre frete

A loja pode ser:

**Opção A — Loja de produtos digitais/retirada:**  
Zero complexidade de frete. Pedido confirmado = produto disponível para download ou retirada presencial. Ideal para materiais religiosos, ingressos, produtos do sínodo.

**Opção B — Loja com frete:**  
Adiciona integração com Correios/Melhor Envio/Frenet. Aumenta o escopo em +1–2 semanas mas os dados de endereço já ficam no checkout. A integração com Melhor Envio é a mais simples do mercado para Django.

**Recomendação:** Lançar a v1 como loja de produtos físicos com **frete combinado/retirada** e adicionar cálculo automático de frete na v2.

---

## 8. Considerações de segurança e financeiras

- **Nunca confiar apenas no webhook** para confirmar pagamento — usar a rota `payment_check` da InfinitePay antes de liberar o pedido
- **Controle de estoque com `select_for_update()`** — evita overselling se dois usuários comprarem o último item simultaneamente
- **HTTPS obrigatório** para o webhook — já configurado via Railway
- **InfinitePay não cobra mensalidade** — custo é 0% no PIX, ~4,2% no cartão de crédito online
- Para faturamento acima de R$80k/mês, as taxas caem automaticamente

---

## 9. Veredicto

| Critério | Avaliação |
|---|---|
| **Vale a pena construir?** | ✅ Sim — a infraestrutura já existe |
| **É complexo?** | 🟡 Médio — mais trabalho que um CRUD simples, menos que um sistema de votação |
| **Demora muito?** | ✅ Não — MVP em ~1 semana com Claude Code |
| **Fica caro?** | ✅ Não — sem mensalidade de plataforma, InfinitePay é transacional |
| **Risco técnico?** | 🟡 Baixo-Médio — principalmente no controle de estoque e idempotência do webhook |
| **Recomendação** | Construir `apps/loja/` nativo, reutilizando InfinitePay e padrões do projeto |

### Prioridade sugerida de features

1. **Fase 1** (Semana 1–2): Produtos simples + variações + carrinho + checkout InfinitePay (PIX e crédito)
2. **Fase 2** (Semana 3): Estoque por SKU + alertas + painel de gestão de pedidos
3. **Fase 3** (futuro): Cupons de desconto, frete automático, avaliações de produto

---

*Análise gerada em 11/06/2026 com base na inspeção do código atual e pesquisa sobre InfinitePay e soluções de e-commerce para Django.*
