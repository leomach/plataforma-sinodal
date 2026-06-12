# Etapa 06 — Gestão / Backoffice da Loja

## Objetivo

Painel para liderança gerenciar produtos, pedidos, estoque e ver relatórios. Tudo dentro da plataforma (sem usar Django Admin para o uso diário — admin fica como fallback técnico).

## Pré-requisitos

- Etapa 04 concluída
- (Recomendado) Etapa 05 concluída para gestão completa de entrega

## Views e URLs

```python
# apps/loja/urls.py (adicionar)
urlpatterns += [
    path('gestao/', gestao.dashboard, name='gestao_dashboard'),
    path('gestao/produtos/', gestao.produtos_lista, name='gestao_produtos'),
    path('gestao/produtos/novo/', gestao.produto_criar, name='gestao_produto_criar'),
    path('gestao/produtos/<int:id>/', gestao.produto_editar, name='gestao_produto_editar'),
    path('gestao/produtos/<int:id>/imagens/', gestao.produto_imagens, name='gestao_produto_imagens'),
    path('gestao/produtos/<int:id>/variacoes/', gestao.produto_variacoes, name='gestao_produto_variacoes'),
    path('gestao/produtos/<int:id>/arquivar/', gestao.produto_arquivar, name='gestao_produto_arquivar'),

    path('gestao/pedidos/', gestao.pedidos_lista, name='gestao_pedidos'),
    path('gestao/pedidos/<int:id>/', gestao.pedido_detalhe, name='gestao_pedido_detalhe'),
    path('gestao/pedidos/<int:id>/confirmar-pagamento/', gestao.confirmar_pagamento_manual, name='gestao_confirmar_pagamento'),
    path('gestao/pedidos/exportar.csv', gestao.pedidos_csv, name='gestao_pedidos_csv'),

    path('gestao/estoque/', gestao.estoque_lista, name='gestao_estoque'),
    path('gestao/estoque/<int:variacao_id>/ajustar/', gestao.estoque_ajustar, name='gestao_estoque_ajustar'),

    path('gestao/categorias/', gestao.categorias_lista, name='gestao_categorias'),

    path('gestao/relatorios/', gestao.relatorios_index, name='gestao_relatorios'),
    path('gestao/relatorios/vendas/', gestao.relatorio_vendas, name='gestao_relatorio_vendas'),
    path('gestao/relatorios/por-evento/<slug:slug>/', gestao.relatorio_por_evento, name='gestao_relatorio_por_evento'),
]
```

Todas decoradas com `@login_required` + `@user_passes_test(is_lideranca)`.

## Modelo novo: `MovimentoEstoque`

Auditoria de movimentações de estoque:

| Campo | Tipo | Notas |
|---|---|---|
| `variacao` | FK(VariacaoProduto, on_delete=CASCADE) | |
| `tipo` | IntegerField(choices=ESTOQUE_MOVIMENTO_CHOICES) | ENTRADA, SAIDA, AJUSTE, RESERVA, RESTAURACAO |
| `quantidade` | IntegerField | Pode ser negativo |
| `estoque_anterior` | PositiveIntegerField | |
| `estoque_novo` | PositiveIntegerField | |
| `pedido` | FK(Pedido, null=True, blank=True, on_delete=SET_NULL) | Quando movimento veio de um pedido |
| `motivo` | CharField(255, blank=True) | Para ajustes manuais |
| `usuario` | FK(User, null=True, on_delete=SET_NULL) | Quem fez (null = automático) |
| `criado_em` | DateTimeField(auto_now_add=True) | |

`Meta.ordering = ['-criado_em']`

Constantes:
```python
ESTOQUE_ENTRADA = 1       # Liderança adicionou unidades
ESTOQUE_SAIDA = 2         # Pedido pago saiu do estoque
ESTOQUE_AJUSTE = 3        # Correção manual (ex.: contagem real)
ESTOQUE_RESERVA = 4       # Carrinho/checkout reservou
ESTOQUE_RESTAURACAO = 5   # Pedido cancelado/expirado devolveu

ESTOQUE_MOVIMENTO_CHOICES = [
    (ESTOQUE_ENTRADA, _('Entrada')),
    (ESTOQUE_SAIDA, _('Saída')),
    (ESTOQUE_AJUSTE, _('Ajuste')),
    (ESTOQUE_RESERVA, _('Reserva')),
    (ESTOQUE_RESTAURACAO, _('Restauração')),
]
```

## Service: `apps/loja/services/estoque.py`

```python
def ajustar_estoque(variacao, novo_valor: int, motivo: str, usuario):
    """Ajuste manual com log."""

def adicionar_estoque(variacao, quantidade: int, motivo: str, usuario):
    """Entrada (compra de fornecedor, produção chegou)."""

def reservar_estoque(item_pedido, pedido, usuario=None):
    """Reserva no checkout. Lança ValueError se insuficiente."""

def restaurar_estoque(item_pedido, pedido):
    """Restaura no cancelamento/expiração."""

def confirmar_saida(item_pedido, pedido):
    """Converte reserva em saída definitiva no marcar_pronto/enviado."""
```

Toda função grava `MovimentoEstoque`.

## Views principais

### `gestao.dashboard`

Mostra:
- Cards de KPI: pedidos hoje, vendido este mês, estoque baixo, pedidos aguardando ação
- Pedidos pagos aguardando preparação (status `PAGO` + retirada/envio)
- Variações com estoque ≤ `estoque_minimo_alerta`

### `gestao.produtos_lista`

- Tabela com filtros (status, categoria, evento)
- Coluna de ações (editar, arquivar, ver no catálogo)
- Busca por nome

### `gestao.produto_criar / produto_editar`

Form único cobrindo todos os campos do `Produto`. Imagens e variações em sub-páginas separadas (para não ficar gigante).

### `gestao.produto_imagens`

Upload múltiplo, drag-and-drop para reordenar (HTMX), deletar.

### `gestao.produto_variacoes`

Formset inline para adicionar/editar/remover variações.

### `gestao.pedidos_lista`

Filtros:
- Status
- Modo de entrega
- Evento
- Período (data início/fim)
- Pago no período
- Busca por número, e-mail do usuário, nome

Colunas: número, usuário, data, status (badge), modo entrega, valor, ações.

### `gestao.pedido_detalhe`

Mostra:
- Dados do cliente
- Itens com snapshot
- Pagamento (link InfinitePay, transação, comprovante)
- Endereço/ponto de retirada
- Histórico de status (timeline)
- Ações disponíveis por status:
  - `AGUARDANDO_PAGAMENTO`: confirmar manualmente, cancelar
  - `PAGO`: marcar pronto
  - `PRONTO`: gerar QR / marcar entregue manual
  - `ENVIADO`: editar rastreio / marcar entregue

### `gestao.confirmar_pagamento_manual` (POST)

Para casos em que o pagamento foi feito por fora (Pix manual, dinheiro). Cria uma "transação manual" e marca pedido como pago.

> Atenção: registrar no log que foi manual, e o usuário responsável.

### `gestao.pedidos_csv`

Exporta CSV com colunas: número, usuário, e-mail, whatsapp, status, data_pagamento, modo_entrega, valor_total, itens (concatenados).

### `gestao.estoque_lista`

Tabela por variação:
- Produto
- Variação
- Estoque atual
- Mínimo alerta
- Última movimentação
- Ação: ajustar

### `gestao.estoque_ajustar`

Form simples: novo valor, motivo. Gera `MovimentoEstoque` tipo `AJUSTE`.

### `gestao.relatorio_vendas`

Filtros: período, categoria, evento.

Mostra:
- Total faturado
- Total de pedidos
- Ticket médio
- Top 5 produtos mais vendidos
- Gráfico simples (CSS, sem libs) por dia

### `gestao.relatorio_por_evento`

Soma de pedidos vinculados a um evento. Útil para saber quanto foi arrecadado em um congresso, retiro, etc.

## Templates

```
templates/loja/gestao/
├── _base.html              # extends 'base.html' com menu lateral
├── dashboard.html
├── produtos/
│   ├── lista.html
│   ├── form.html
│   ├── imagens.html
│   └── variacoes.html
├── pedidos/
│   ├── lista.html
│   └── detalhe.html
├── estoque/
│   ├── lista.html
│   └── ajustar.html
├── categorias/
│   └── lista.html
└── relatorios/
    ├── index.html
    └── vendas.html
```

Menu lateral fixo com: Dashboard, Produtos, Pedidos, Estoque, Categorias, Relatórios.

## Critérios de aceite

- [ ] Apenas usuários com `tipo=LIDERANCA` ou `is_superuser` acessam `/loja/gestao/*`
- [ ] Dashboard exibe KPIs corretos com queries otimizadas (1–3 queries no total)
- [ ] CRUD completo de produtos pelo backoffice (sem precisar do Django admin)
- [ ] Upload de imagens com preview e reordenação
- [ ] Adicionar/remover variações sem reload (HTMX)
- [ ] Lista de pedidos com filtros funcionais
- [ ] Detalhe de pedido mostra timeline de status
- [ ] Confirmação manual de pagamento funciona e fica registrada
- [ ] Exportação CSV gera arquivo válido com pedidos filtrados
- [ ] Ajuste de estoque cria `MovimentoEstoque` com usuário responsável
- [ ] Relatório de vendas com totais corretos por período
- [ ] Relatório por evento bate com soma manual dos pedidos do evento
- [ ] Mobile: tabelas têm scroll horizontal; ações têm botões grandes

## Casos de uso cobertos

- CU-01 parcial (gerar relatório de produção — completo na Etapa 07)
- CU-02 parcial (acompanhar pedido)
- CU-06 (liderança ajusta estoque após produção chegar)

## Estimativa

1–1,5 dia (8–12 horas com Claude Code).

## Pontos de atenção

1. **Performance da lista de pedidos**: usar `select_related('usuario', 'transacao')` + paginação (50 por página).
2. **Permissões**: usar a função `is_lideranca` já existente em `apps/eventos/views.py` — extrair para `core/permissions.py` ou similar para reutilizar.
3. **Confirmação manual de pagamento**: criar uma `TransacaoInfinitePay` "fake" com `transaction_nsu = f'manual-{pedido.id}-{uuid}'` e `capture_method='manual'`. Mantém auditoria consistente.
4. **CSV em UTF-8 com BOM** para Excel não corromper acentos.
5. **Reutilizar componentes de gestão de eventos**: o template de `apps/eventos/templates/eventos/inscricoes.html` é uma boa referência visual.
