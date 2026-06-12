# PRD — Lojinha da Plataforma Sinodal

> Documento central de planejamento. Cada arquivo numerado é uma etapa de implementação independente, que pode ser executada na ordem ou pulada (com seus pré-requisitos respeitados).

---

## Visão geral

Construir um módulo de e-commerce dentro da Plataforma Sinodal capaz de:

1. Vender produtos físicos (camisetas, materiais, kits) ligados ou não a eventos
2. Operar em modalidade de **pré-venda** com cota e relatório de produção
3. Suportar **rifa**, **vaquinha** e **doação livre** — modalidades específicas da UMP
4. Confirmar pagamentos via integração já existente com a InfinitePay (PIX 0%, cartão)
5. Anunciar produtos e campanhas em toda a plataforma
6. Permitir retirada presencial em eventos e envio pelos Correios

O módulo será um app Django chamado **`apps.loja`** seguindo o padrão monolito modular da plataforma.

---

## Etapas de implementação

A ordem das etapas reflete dependência técnica. As etapas 2, 3 e 4 formam o **MVP**. As demais são incrementais.

| # | Arquivo | Etapa | Pré-requisitos | Estimativa |
|---|---|---|---|---|
| 01 | [01_arquitetura.md](01_arquitetura.md) | Arquitetura e fundação técnica | — | 0,5 dia |
| 02 | [02_catalogo.md](02_catalogo.md) | Catálogo de produtos | 01 | 1–2 dias |
| 03 | [03_carrinho_checkout.md](03_carrinho_checkout.md) | Carrinho e checkout | 02 | 1,5–2 dias |
| 04 | [04_pedidos_pagamento.md](04_pedidos_pagamento.md) | Pedidos e pagamento | 03 | 1–1,5 dias |
| 05 | [05_entrega_retirada.md](05_entrega_retirada.md) | Entrega e retirada | 04 | 1 dia |
| 06 | [06_gestao_backoffice.md](06_gestao_backoffice.md) | Gestão / Backoffice | 04 | 1–1,5 dias |
| 07 | [07_pre_venda.md](07_pre_venda.md) | Pré-venda | 02, 04 | 2 dias |
| 08 | [08_anuncios.md](08_anuncios.md) | Anúncios e comunicação | 02 | 1 dia |
| 09 | [09_modalidades_ump.md](09_modalidades_ump.md) | Rifa, vaquinha, doação livre | 04 | 2–3 dias |
| 10 | [10_integracoes.md](10_integracoes.md) | Integrações (emblemas, perfil) | 04 | 0,5 dia |

**MVP funcional (etapas 01–04):** 4–6 dias úteis com Claude Code.
**Versão completa (todas):** 11–14 dias úteis com Claude Code.

---

## Decisões transversais (válidas para todas as etapas)

### Stack
- Django 5.1+, PostgreSQL, HTMX, Tailwind CSS — sem novas dependências de framework
- Pagamentos: app `apps.pagamentos` já implementado e auditado (InfinitePay)
- Templates seguem o padrão de `apps/eventos/` e `apps/sessoes/`

### Padrões obrigatórios

1. **Constantes em `core/constants.py`** com prefixo de domínio (`LOJA_`, `PEDIDO_`, `PRODUTO_`, `RIFA_`, `CAMPANHA_`)
2. **Choices nos models referenciam `core/constants.py`** via aliases:
   ```python
   from core import constants as _c
   class Produto(models.Model):
       STATUS_RASCUNHO = _c.PRODUTO_RASCUNHO
       STATUS_CHOICES = _c.PRODUTO_STATUS_CHOICES
   ```
3. **Decimal em centavos** ao integrar com InfinitePay — sempre usar `apps.pagamentos.services.infinitepay.to_centavos()`
4. **Pagamento via handler registrado**:
   ```python
   from apps.pagamentos.handlers import register_payment_handler

   @register_payment_handler('pedido')
   def confirmar_pedido_pago(*, order_nsu, transacao, payload):
       ...
   ```
   `order_nsu` para pedidos da loja sempre será `pedido-<id>`.
5. **`select_for_update()`** em qualquer operação que decremente estoque
6. **HTMX-first**: nenhuma página é recarregada para ações de carrinho. Use `hx-post`, `hx-target`, `hx-swap`
7. **Mobile-first**: regra global `font-size: 16px` em inputs (já configurada em `base.html`)
8. **Tailwind sem novas dependências** — usar utilitários existentes
9. **Imagens via Cloudinary** quando disponível (já configurado)

### Estrutura do app `loja`

```
apps/loja/
├── __init__.py
├── apps.py                       # LojaConfig.ready() → importa handlers
├── admin.py
├── handlers.py                   # @register_payment_handler('pedido')
├── models.py                     # ou divididos em models/ se ficar grande
├── forms.py
├── urls.py
├── services/
│   ├── __init__.py
│   ├── carrinho.py               # Lógica de carrinho (sessão + DB)
│   ├── estoque.py                # Reserva, decremento, alerta
│   ├── pedido.py                 # Criação de pedido a partir do carrinho
│   ├── frete.py                  # Cálculo Correios (etapa 05)
│   └── relatorios.py             # CSV, relatórios de produção
├── templatetags/
│   └── loja.py                   # Filtros de moeda, badge de fase
├── context_processors.py         # Carrinho no header
├── views/
│   ├── __init__.py
│   ├── catalogo.py
│   ├── carrinho.py
│   ├── checkout.py
│   ├── pedido.py
│   ├── gestao.py                 # Backoffice
│   └── modalidades.py            # Rifa, vaquinha, doação
├── management/
│   └── commands/
│       ├── transicionar_fases_produtos.py
│       └── notificar_lista_espera.py
└── migrations/
```

### Convenções de URL

| URL pública | View |
|---|---|
| `/loja/` | Catálogo |
| `/loja/categoria/<slug>/` | Produtos por categoria |
| `/loja/produto/<slug>/` | Detalhe do produto |
| `/loja/carrinho/` | Carrinho |
| `/loja/checkout/` | Checkout |
| `/loja/pedido/<id>/` | Confirmação / status do pedido |
| `/loja/meus-pedidos/` | Histórico |
| `/loja/gestao/` | Backoffice (liderança) |
| `/loja/rifa/<slug>/` | Página da rifa |
| `/loja/campanha/<slug>/` | Página da vaquinha |

### Convenções de status / fases (visão consolidada)

**Produto** → `RASCUNHO`, `EM_BREVE`, `PRE_VENDA`, `VENDA_NORMAL`, `ESGOTADO`, `ENCERRADO`, `ARQUIVADO`

**Pedido** → `AGUARDANDO_PAGAMENTO`, `PAGO`, `AGUARDANDO_PRODUCAO` (pré-venda), `PRONTO` (para retirada/envio), `ENVIADO`, `ENTREGUE`, `CANCELADO`, `REEMBOLSADO`

**Rifa** → `ABERTA`, `ESGOTADA`, `AGUARDANDO_SORTEIO`, `SORTEADA`, `CANCELADA`

**Campanha (Vaquinha)** → `ABERTA`, `META_ATINGIDA`, `ENCERRADA`, `CANCELADA`

> Todas essas constantes serão definidas em `core/constants.py` com prefixos `PRODUTO_`, `PEDIDO_`, `RIFA_`, `CAMPANHA_` na etapa que cada uma for usada pela primeira vez.

---

## Modelo de dados consolidado (visão alto nível)

```
Categoria ─────┐
               ▼
Produto ◄──── ImagemProduto
   │
   │ 1:N
   ▼
VariacaoProduto ◄── ItemCarrinho ◄── Carrinho ─── User
       │                                │
       │                                ▼
       │                          (sessão → pedido)
       │ 1:N                            │
       └─────── ItemPedido ─────── Pedido ─── User
                                    │
                                    │ 1:1
                                    ▼
                          TransacaoInfinitePay (apps.pagamentos)

Modalidades especiais:
   Rifa ─── BilheteRifa ─── User
   Campanha ─── ContribuicaoCampanha ─── User
```

Detalhamento por etapa nos arquivos numerados.

---

## Casos de uso de referência

Os arquivos de etapa usam esses casos como base para os critérios de aceite:

1. **CU-01 — Camiseta de evento em pré-venda**
   Liderança cria camiseta com fases `EM_BREVE → PRE_VENDA → VENDA_NORMAL`. 50 unidades em pré-venda, preço promocional. Após encerrar pré-venda, vê total pedido por tamanho para mandar produzir.

2. **CU-02 — Compra avulsa de material**
   Usuário compra devocional. Paga via PIX. Retira presencialmente no evento.

3. **CU-03 — Rifa para arrecadar fundo de missão**
   Liderança cria rifa com 100 bilhetes de R$ 10. Usuários compram bilhetes individuais. Sistema gera número único por bilhete. Quando esgota, liderança roda sorteio.

4. **CU-04 — Vaquinha para reforma da igreja**
   Liderança cria campanha com meta de R$ 15.000. Usuários contribuem com valor livre. Barra de progresso visível no hub.

5. **CU-05 — Camiseta esgotada com lista de espera**
   Produto esgota. Usuário entra na lista de espera. Quando liderança repõe estoque, usuários da lista recebem e-mail e têm 24h de prioridade.

6. **CU-06 — Liderança pré-vende camiseta sem precisar gerenciar estoque**
   Liderança cria pré-venda. Sistema deduz da cota de pré-venda. Quando produção chega, liderança ajusta estoque normal e altera status dos pedidos para "Pronto para retirada".

7. **CU-07 — Comprador de produto X ganha emblema**
   Usuário compra "Bíblia comemorativa 50 anos UMP". Sistema concede emblema "Coleção UMP" automaticamente.

---

## Como o Claude deve usar este PRD

Quando for implementar:

1. **Leia primeiro o `index.md` e o `01_arquitetura.md`** para entender padrões transversais
2. **Cada etapa tem um arquivo dedicado** com:
   - Objetivo (o que ela entrega)
   - Pré-requisitos
   - Modelos a criar
   - Constantes a adicionar
   - Views e URLs
   - Templates
   - Critérios de aceite (checklist objetivo)
   - Casos de uso cobertos
3. **Não pule etapas sem garantir os pré-requisitos**. As dependências estão na tabela acima.
4. **Sempre rode `python manage.py check` e `python manage.py makemigrations`** após criar modelos
5. **Para cada etapa, antes de seguir para a próxima, valide os critérios de aceite manualmente** (subir servidor, criar dados de teste, executar fluxo no navegador)

---

## Critérios globais de "pronto"

Uma etapa só está pronta quando:

- [ ] Todos os critérios de aceite da etapa estão validados manualmente no navegador
- [ ] Migrations criadas e aplicadas sem erro (`python manage.py migrate`)
- [ ] `python manage.py check` retorna 0 warnings novos
- [ ] Constantes adicionadas em `core/constants.py` (não nos models)
- [ ] Templates seguem o padrão visual de `apps/eventos/templates/`
- [ ] Mobile testado (DevTools modo iPhone 12 / Pixel 5)
- [ ] Nenhum endpoint público quebra autenticação ou autorização

---

## Glossário

| Termo | Significado |
|---|---|
| **UMP** | União da Mocidade Presbiteriana |
| **Liderança** | Usuário com `tipo=LIDERANCA` ou `is_superuser=True` |
| **Sócio** | Usuário com `tipo=SOCIO` |
| **Fase** (do produto) | Estado do produto no ciclo de vida (em breve → pré-venda → venda normal → encerrado) |
| **Cota** (de pré-venda) | Quantidade reservada exclusivamente para a pré-venda, separada do estoque normal |
| **Pedido** | Pedido de compra de produtos (não confundir com inscrição em evento) |
| **InfiniteTag** | Identificador da conta InfinitePay (`handle` sem o `$`) |
| **`order_nsu`** | Identificador externo do pedido na InfinitePay. Formato: `pedido-<id>` para a loja |
| **Bilhete** | Unidade vendável de uma rifa, com número único |
| **Contribuição** | Pagamento em uma campanha de vaquinha (valor livre) |

---

## Referências internas

- [`CLAUDE.md`](../CLAUDE.md) — convenções de código do projeto
- [`docs/INFINITEPAY.md`](../docs/INFINITEPAY.md) — integração de pagamentos
- [`lista_funcionalidades.md`](../lista_funcionalidades.md) — origem dos requisitos
- [`AUDITORIA_INFINITEPAY.md`](../AUDITORIA_INFINITEPAY.md) — estado atual da integração de pagamentos
- [`ANALISE_LOJA.md`](../ANALISE_LOJA.md) — análise inicial de viabilidade
