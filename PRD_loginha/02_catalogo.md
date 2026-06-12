# Etapa 02 — Catálogo de produtos

## Objetivo

Permitir que a liderança cadastre produtos com variações, categorias e imagens. Permitir que usuários naveguem pelo catálogo público, filtrem por categoria e abram o detalhe do produto. **Ainda não há carrinho nessa etapa** — apenas exibição.

## Pré-requisitos

- Etapa 01 concluída

## Modelos

### `Categoria`

| Campo | Tipo | Notas |
|---|---|---|
| `nome` | CharField(100) | |
| `slug` | SlugField(unique=True) | Auto-gerado de `nome` |
| `ordem` | PositiveIntegerField(default=0) | Ordem de exibição |
| `ativa` | BooleanField(default=True) | |
| `icone` | CharField(10, blank=True) | Emoji opcional |

`Meta.ordering = ['ordem', 'nome']`

### `Produto`

| Campo | Tipo | Notas |
|---|---|---|
| `nome` | CharField(200) | |
| `slug` | SlugField(unique=True) | Auto-gerado |
| `categoria` | FK(Categoria, on_delete=PROTECT) | |
| `descricao` | TextField | Markdown ou HTML simples |
| `descricao_curta` | CharField(255, blank=True) | Para cards |
| `preco` | DecimalField(max_digits=10, decimal_places=2) | Preço base; variações podem ajustar |
| `imagem_principal` | ImageField(upload_to='loja/produtos/') | Cloudinary em prod |
| `status` | IntegerField(choices=PRODUTO_STATUS_CHOICES, default=RASCUNHO) | |
| `evento` | FK(Evento, null=True, blank=True, on_delete=SET_NULL) | Produto vinculado a evento |
| `visivel_apenas_inscritos` | BooleanField(default=False) | Só vê quem está inscrito no evento |
| `visivel_apenas_lideranca` | BooleanField(default=False) | Produtos restritos |
| `destaque` | BooleanField(default=False) | Aparece em destaque na home |
| `ordem_destaque` | PositiveIntegerField(default=0) | Ordem entre destaques |
| `criado_em` | DateTimeField(auto_now_add=True) | |
| `atualizado_em` | DateTimeField(auto_now=True) | |
| `criado_por` | FK(User, on_delete=PROTECT) | |

`Meta.ordering = ['-criado_em']`

Métodos auxiliares:
- `disponivel_para(user)` → `bool` (combina status + visibilidade + inscrição)
- `tem_variacoes` → property `bool`
- `preco_minimo` / `preco_maximo` → properties (entre todas as variações ativas)
- `estoque_total` → property (soma de todas as variações ativas)

### `VariacaoProduto`

| Campo | Tipo | Notas |
|---|---|---|
| `produto` | FK(Produto, on_delete=CASCADE, related_name='variacoes') | |
| `nome` | CharField(60) | Ex.: "P / Preto", "Tamanho M" |
| `sku` | CharField(50, blank=True) | Código interno (opcional) |
| `preco_adicional` | DecimalField(default=0) | Pode ser negativo (desconto) |
| `estoque` | PositiveIntegerField(default=0) | Estoque atual desta variação |
| `estoque_minimo_alerta` | PositiveIntegerField(default=5) | Para alerta no backoffice |
| `ativa` | BooleanField(default=True) | |
| `ordem` | PositiveIntegerField(default=0) | |

`Meta.ordering = ['ordem', 'nome']`
`Meta.unique_together = [('produto', 'nome')]`

Propriedades:
- `preco_final` → `produto.preco + preco_adicional`
- `disponivel` → `ativa and estoque > 0`

### `ImagemProduto`

| Campo | Tipo | Notas |
|---|---|---|
| `produto` | FK(Produto, on_delete=CASCADE, related_name='imagens') | |
| `imagem` | ImageField(upload_to='loja/produtos/') | |
| `legenda` | CharField(200, blank=True) | |
| `ordem` | PositiveIntegerField(default=0) | |

`Meta.ordering = ['ordem']`

## Constantes (core/constants.py)

```python
# Status do Produto
PRODUTO_RASCUNHO = 1
PRODUTO_EM_BREVE = 2
PRODUTO_PRE_VENDA = 3        # usado a partir da Etapa 07
PRODUTO_VENDA_NORMAL = 4
PRODUTO_ESGOTADO = 5
PRODUTO_ENCERRADO = 6
PRODUTO_ARQUIVADO = 7

PRODUTO_STATUS_CHOICES = [
    (PRODUTO_RASCUNHO, _('Rascunho')),
    (PRODUTO_EM_BREVE, _('Em breve')),
    (PRODUTO_PRE_VENDA, _('Pré-venda')),
    (PRODUTO_VENDA_NORMAL, _('À venda')),
    (PRODUTO_ESGOTADO, _('Esgotado')),
    (PRODUTO_ENCERRADO, _('Encerrado')),
    (PRODUTO_ARQUIVADO, _('Arquivado')),
]

# Status visíveis no catálogo público (exclui RASCUNHO, ENCERRADO, ARQUIVADO)
PRODUTO_STATUS_VISIVEIS = [
    PRODUTO_EM_BREVE,
    PRODUTO_PRE_VENDA,
    PRODUTO_VENDA_NORMAL,
    PRODUTO_ESGOTADO,
]

# Status que aceitam adicionar ao carrinho
PRODUTO_STATUS_COMPRAVEIS = [
    PRODUTO_PRE_VENDA,
    PRODUTO_VENDA_NORMAL,
]
```

## Views e URLs

```python
# apps/loja/urls.py
urlpatterns = [
    path('', catalogo.index, name='index'),
    path('categoria/<slug:slug>/', catalogo.por_categoria, name='por_categoria'),
    path('produto/<slug:slug>/', catalogo.detalhe_produto, name='detalhe_produto'),
]
```

### `catalogo.index(request)`

- Lista produtos com `status in PRODUTO_STATUS_VISIVEIS`
- Aplica filtro de visibilidade (`visivel_apenas_lideranca`, `visivel_apenas_inscritos`)
- Ordena: destaques primeiro (`destaque=True, ordem_destaque`), depois `-criado_em`
- Renderiza grid com cards de produto

### `catalogo.por_categoria(request, slug)`

- Filtra por categoria
- Mesmas regras de visibilidade do index

### `catalogo.detalhe_produto(request, slug)`

- Carrega produto + `prefetch_related('imagens', 'variacoes')`
- Se `produto.visivel_apenas_inscritos`: valida que `request.user` tem inscrição aprovada no `produto.evento`
- Se `produto.visivel_apenas_lideranca`: valida `is_lideranca(request.user)`
- Renderiza detalhes, galeria de imagens, seletor de variação (sem ação ainda — botão "adicionar ao carrinho" é da Etapa 03)

## Templates

```
templates/loja/
├── catalogo/
│   ├── index.html              # Grid de produtos
│   ├── por_categoria.html      # Reaproveita partial _grid.html
│   └── detalhe_produto.html    # Página de produto
└── partials/
    ├── _card_produto.html      # Card usado no grid
    ├── _galeria_imagens.html
    └── _badge_status.html      # Badge colorido por status
```

### `_card_produto.html` — estrutura

```django
<a href="{% url 'loja:detalhe_produto' produto.slug %}"
   class="block rounded-lg overflow-hidden border border-gray-200 hover:shadow-lg transition-shadow">
  <div class="aspect-square bg-gray-100">
    {% if produto.imagem_principal %}
      <img src="{{ produto.imagem_principal.url }}" alt="{{ produto.nome }}"
           class="w-full h-full object-cover">
    {% endif %}
  </div>
  <div class="p-3">
    <h3 class="font-semibold text-sm">{{ produto.nome }}</h3>
    {% include 'loja/partials/_badge_status.html' with status=produto.status %}
    <p class="text-blue-600 font-bold mt-1">{{ produto.preco|moeda }}</p>
  </div>
</a>
```

## Admin

```python
# apps/loja/admin.py
class VariacaoProdutoInline(admin.TabularInline):
    model = VariacaoProduto
    extra = 1

class ImagemProdutoInline(admin.TabularInline):
    model = ImagemProduto
    extra = 1

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'status', 'preco', 'destaque')
    list_filter = ('status', 'categoria', 'destaque')
    search_fields = ('nome', 'descricao')
    prepopulated_fields = {'slug': ('nome',)}
    inlines = [ImagemProdutoInline, VariacaoProdutoInline]

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ordem', 'ativa')
    prepopulated_fields = {'slug': ('nome',)}
```

## Critérios de aceite

- [ ] Migrations criadas e aplicadas sem erro
- [ ] Liderança consegue criar categoria, produto, variações e imagens pelo admin
- [ ] Slug é gerado automaticamente ao salvar
- [ ] `/loja/` mostra produtos com status visíveis, ordenados (destaque primeiro)
- [ ] `/loja/categoria/<slug>/` filtra corretamente
- [ ] `/loja/produto/<slug>/` mostra:
  - [ ] Galeria de imagens (principal + adicionais)
  - [ ] Nome, descrição, preço
  - [ ] Lista de variações com nome, preço final, estoque
  - [ ] Badge do status (cor diferente para cada)
- [ ] Produto com `status=RASCUNHO` **não** aparece no catálogo público
- [ ] Produto com `visivel_apenas_lideranca=True` retorna 404 para usuário comum
- [ ] Produto com `visivel_apenas_inscritos=True` e evento X só é visível para quem tem inscrição aprovada em X
- [ ] Mobile: cards quebram corretamente em 2 colunas; detalhe legível
- [ ] Performance: `index` faz no máximo 4 queries (use `select_related('categoria')` + `prefetch_related('variacoes')`)

## Casos de uso cobertos

- Parte de CU-01, CU-02 (cadastro de produto)
- Parte de CU-05 (estoque pode ficar zero — badge "Esgotado")

## Estimativa

1–2 dias (8–16 horas com Claude Code).

## Pontos de atenção para implementação

1. **Imagens em produção** vão para Cloudinary automaticamente (já configurado). Em dev vão para `media/loja/produtos/`.
2. **`unique_together` em variações** garante que não existam dois "Tamanho M" no mesmo produto.
3. **`PROTECT` em criado_por** — não deixar deletar usuário que criou produto.
4. **`SET_NULL` em evento** — se evento for deletado, produto continua existindo (só perde o vínculo).
5. **Slug duplicado**: usar `slugify(nome)` + sufixo numérico se já existir (`-2`, `-3`...).
