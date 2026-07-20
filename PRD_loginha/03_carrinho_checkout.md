# Etapa 03 — Carrinho e Checkout

## Objetivo

Permitir que usuário adicione produtos ao carrinho, gerencie quantidades, finalize o pedido informando dados de contato e modo de entrega. **A confirmação de pagamento via InfinitePay é tratada na Etapa 04**; aqui o pedido fica em status `AGUARDANDO_PAGAMENTO`.

## Pré-requisitos

- Etapa 02 concluída (catálogo)

## Modelos

### `Carrinho`

| Campo | Tipo | Notas |
|---|---|---|
| `usuario` | FK(User, null=True, on_delete=CASCADE, related_name='carrinhos') | Null se anônimo |
| `sessao_key` | CharField(40, blank=True, db_index=True) | Para anônimos |
| `criado_em` | DateTimeField(auto_now_add=True) | |
| `atualizado_em` | DateTimeField(auto_now=True) | |

`Meta.constraints`: ao menos um de `usuario` ou `sessao_key` deve estar preenchido (CheckConstraint).

Métodos:
- `total` → property `Decimal` (soma de `itens`)
- `quantidade_itens` → property `int`
- `vazio` → property `bool`
- `merge_de(outro_carrinho)` → método para fundir carrinhos no login
- `validar_disponibilidade()` → retorna lista de `ItemCarrinho` com problema (estoque insuficiente, produto arquivado)

### `ItemCarrinho`

| Campo | Tipo | Notas |
|---|---|---|
| `carrinho` | FK(Carrinho, on_delete=CASCADE, related_name='itens') | |
| `variacao` | FK(VariacaoProduto, on_delete=CASCADE) | Sempre é uma variação (mesmo produto sem variações terá uma padrão chamada "Único") |
| `quantidade` | PositiveIntegerField(default=1) | |
| `preco_unitario` | DecimalField(10, 2) | Snapshot do preço no momento de adicionar |
| `observacao` | CharField(255, blank=True) | Ex.: "Número da camisa: 10" |
| `adicionado_em` | DateTimeField(auto_now_add=True) | |

`Meta.unique_together = [('carrinho', 'variacao')]` — adicionar a mesma variação duas vezes incrementa quantidade.

Property:
- `subtotal` → `preco_unitario * quantidade`

## Adaptação no modelo Produto (Etapa 02)

Se um produto **não tem variações**, criar automaticamente uma `VariacaoProduto` chamada `"Único"` no `save()` do produto, com `preco_adicional=0` e `estoque` definido manualmente. Isso simplifica toda a lógica de carrinho — sempre referenciamos variação.

```python
def save(self, *args, **kwargs):
    super().save(*args, **kwargs)
    if not self.variacoes.exists():
        VariacaoProduto.objects.create(
            produto=self, nome='Único',
            preco_adicional=0, estoque=0, ordem=0,
        )
```

> Nota: documentar essa convenção no `index.md` da etapa 02.

## Constantes (core/constants.py)

```python
# Status do Pedido (será expandido na Etapa 04)
PEDIDO_AGUARDANDO_PAGAMENTO = 1
PEDIDO_PAGO = 2
PEDIDO_CANCELADO = 9   # gap nos números para acomodar status futuros

PEDIDO_STATUS_CHOICES_INICIAL = [
    (PEDIDO_AGUARDANDO_PAGAMENTO, _('Aguardando pagamento')),
    (PEDIDO_PAGO, _('Pago')),
    (PEDIDO_CANCELADO, _('Cancelado')),
]

# Modo de Entrega (será expandido na Etapa 05)
ENTREGA_RETIRADA = 1
ENTREGA_CORREIOS = 2

ENTREGA_MODO_CHOICES = [
    (ENTREGA_RETIRADA, _('Retirada presencial')),
    (ENTREGA_CORREIOS, _('Envio pelos Correios')),
]
```

## Service: `apps/loja/services/carrinho.py`

API pública (funções, não classe):

```python
def get_carrinho(request) -> Carrinho:
    """Retorna o carrinho do usuário/sessão. Cria se não existir."""

def adicionar_item(carrinho, variacao_id: int, quantidade: int = 1, observacao: str = '') -> ItemCarrinho:
    """Adiciona ou incrementa item. Lança ValueError se estoque insuficiente."""

def atualizar_quantidade(item_id: int, carrinho, nova_quantidade: int):
    """Atualiza ou remove se quantidade = 0. Valida estoque."""

def remover_item(item_id: int, carrinho):
    """Remove item."""

def limpar_carrinho(carrinho):
    """Remove todos os itens."""

def merge_carrinho_sessao(request, usuario):
    """Chamado no login: funde sessão anônima com carrinho do usuário."""
```

## Views e URLs

```python
# apps/loja/urls.py (adicionar)
urlpatterns += [
    path('carrinho/', carrinho.detalhe, name='carrinho'),
    path('carrinho/adicionar/', carrinho.adicionar, name='carrinho_adicionar'),  # POST
    path('carrinho/item/<int:item_id>/', carrinho.atualizar_item, name='carrinho_atualizar_item'),  # POST
    path('carrinho/item/<int:item_id>/remover/', carrinho.remover_item, name='carrinho_remover_item'),  # POST
    path('checkout/', checkout.iniciar, name='checkout'),
    path('checkout/confirmar/', checkout.confirmar, name='checkout_confirmar'),  # POST → cria Pedido
]
```

### Endpoints HTMX (responses parciais)

- `POST /loja/carrinho/adicionar/` → retorna fragmento `_widget_carrinho.html` (badge no header)
- `POST /loja/carrinho/item/<id>/` → retorna fragmento `_linha_item.html`
- `POST /loja/carrinho/item/<id>/remover/` → retorna fragmento `_linha_item.html` (vazio) + dispara update do total

### Views detalhadas

#### `carrinho.detalhe(request)`
Renderiza página com itens, total, botão "Finalizar compra".

#### `carrinho.adicionar(request)` (POST)
- Recebe `variacao_id`, `quantidade`, `observacao`
- Chama `service.adicionar_item`
- Se HTMX: retorna fragmento atualizado do badge
- Se POST tradicional: redireciona para `/loja/carrinho/`

#### `checkout.iniciar(request)` (GET, requires login)
- Valida disponibilidade (`carrinho.validar_disponibilidade()`)
- Se houver problema, redireciona pro carrinho com mensagem
- Renderiza form com: contato (auto-preenchido do user), modo de entrega, observações
- Se `request.user.perfil_completo == False`, redireciona pro perfil

#### `checkout.confirmar(request)` (POST, requires login, atomic + select_for_update)
- Valida form
- **Reserva estoque**: decrementa `variacao.estoque` em cada item (`select_for_update`)
- Cria `Pedido` com status `AGUARDANDO_PAGAMENTO`
- Cria `ItemPedido` para cada `ItemCarrinho`
- Esvazia o carrinho
- **Não chama InfinitePay aqui** — apenas redireciona para `/loja/pedido/<id>/` que mostra "Aguardando pagamento" + botão "Pagar agora" (Etapa 04 implementa)

## Templates

```
templates/loja/
├── carrinho/
│   ├── detalhe.html             # /loja/carrinho/
│   └── _widget_carrinho.html    # badge no header (qtd + total)
├── checkout/
│   └── iniciar.html             # /loja/checkout/
└── partials/
    ├── _linha_item.html         # <tr> de cada item no carrinho
    └── _resumo_total.html       # rodapé com total
```

### `_widget_carrinho.html` — para header global

```django
{% load loja %}
<a href="{% url 'loja:carrinho' %}" class="relative">
  <svg class="w-6 h-6"><!-- ícone --></svg>
  {% if carrinho_qtd %}
    <span class="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full px-1.5 py-0.5">
      {{ carrinho_qtd }}
    </span>
  {% endif %}
</a>
```

### Como atualizar o widget via HTMX

Toda action que muda o carrinho usa `hx-swap-oob="true"` para atualizar o widget no header sem reload:

```html
<button hx-post="/loja/carrinho/adicionar/"
        hx-vals='{"variacao_id": {{ variacao.id }}, "quantidade": 1}'
        hx-target="this" hx-swap="outerHTML">
  Adicionar ao carrinho
</button>
```

Resposta da view:
```html
<button ...>Adicionado!</button>
<span id="widget-carrinho" hx-swap-oob="true">
  {% include 'loja/carrinho/_widget_carrinho.html' %}
</span>
```

## Context processor

Atualizar `apps/loja/context_processors.py`:

```python
from .services.carrinho import get_carrinho

def carrinho_resumo(request):
    try:
        c = get_carrinho(request, criar=False)
    except Exception:
        return {'carrinho_qtd': 0, 'carrinho_total': 0}
    if not c:
        return {'carrinho_qtd': 0, 'carrinho_total': 0}
    return {
        'carrinho_qtd': c.quantidade_itens,
        'carrinho_total': c.total,
    }
```

## Signal de login (merge de carrinho)

Em `apps/loja/signals.py`:

```python
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .services.carrinho import merge_carrinho_sessao

@receiver(user_logged_in)
def on_login_merge_carrinho(sender, request, user, **kwargs):
    merge_carrinho_sessao(request, user)
```

Importar em `LojaConfig.ready()`.

## Critérios de aceite

- [ ] Usuário anônimo consegue adicionar item ao carrinho (persistido em sessão)
- [ ] Ao fazer login, carrinho anônimo é fundido com o carrinho do usuário
- [ ] Adicionar mesmo produto+variação duas vezes incrementa quantidade
- [ ] Não é possível adicionar mais que o estoque disponível
- [ ] Badge no header atualiza via HTMX sem reload
- [ ] Página `/loja/carrinho/` mostra:
  - [ ] Lista de itens com nome, variação, observação, preço unitário, quantidade, subtotal
  - [ ] Botões + / − para mudar quantidade (HTMX)
  - [ ] Botão "Remover" (HTMX)
  - [ ] Total geral
  - [ ] Botão "Finalizar compra" (visível só se logado; senão "Faça login")
- [ ] `/loja/checkout/` exige login
- [ ] Checkout exige perfil completo (redireciona para perfil se faltar nome/e-mail/whatsapp)
- [ ] Ao confirmar checkout:
  - [ ] Estoque é decrementado atomicamente
  - [ ] Pedido é criado com `status=AGUARDANDO_PAGAMENTO`
  - [ ] ItemPedido é criado para cada item
  - [ ] Carrinho é esvaziado
  - [ ] Redireciona para `/loja/pedido/<id>/`
- [ ] Race condition: dois usuários comprando o último item simultaneamente → apenas um consegue, outro vê erro claro
- [ ] Carrinho com produto que foi para `RASCUNHO/ARQUIVADO` mostra aviso no checkout
- [ ] Mobile: layout não quebra; botões + / − têm área de toque ≥ 44px

## Casos de uso cobertos

- CU-02 (compra avulsa de material) — parcial até a Etapa 04 confirmar pagamento

## Estimativa

1,5–2 dias (12–16 horas com Claude Code).

## Pontos de atenção

1. **`select_for_update` é obrigatório** na confirmação do checkout. Sem isso, dois clientes podem decrementar estoque do último item.
2. **Snapshot de preço** em `ItemCarrinho.preco_unitario`: garante que mudanças de preço do produto não afetam carrinhos abertos.
3. **Sessão anônima**: usar `request.session.session_key` (criar se não existir com `request.session.create()`).
4. **Reserva temporária de 15 min** mencionada no `01_arquitetura.md` é implementada na Etapa 04 (depende do conceito de Pedido pendente).
5. **HTMX `hx-swap-oob`** é a chave para atualizar o widget do header sem JS adicional.
