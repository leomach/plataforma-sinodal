# Etapa 07 — Pré-venda

## Objetivo

Implementar o conceito completo de pré-venda: fases do produto (Em breve → Pré-venda → Venda normal → Encerrado), cota separada de pré-venda, status de pedido `AGUARDANDO_PRODUCAO`, relatório de produção, lista de espera.

## Pré-requisitos

- Etapa 02 concluída (catálogo)
- Etapa 04 concluída (pedidos e pagamento)

## Adições ao modelo `Produto`

| Campo | Tipo | Notas |
|---|---|---|
| `em_breve_inicio` | DateTimeField(null=True, blank=True) | A partir daqui aparece como "Em breve" |
| `pre_venda_inicio` | DateTimeField(null=True, blank=True) | A partir daqui status vira `PRE_VENDA` automaticamente |
| `pre_venda_fim` | DateTimeField(null=True, blank=True) | Aqui termina pré-venda |
| `venda_normal_inicio` | DateTimeField(null=True, blank=True) | A partir daqui status vira `VENDA_NORMAL` |
| `venda_normal_fim` | DateTimeField(null=True, blank=True) | Encerra |
| `cota_pre_venda` | PositiveIntegerField(default=0) | Quantidade reservada para pré-venda; 0 = sem pré-venda |
| `preco_pre_venda` | DecimalField(10, 2, null=True, blank=True) | Preço promocional na pré-venda; null = usa `preco` |
| `producao_estimada_dias` | PositiveIntegerField(default=0) | Quantos dias para o produto chegar após pré-venda |

> A transição entre fases pode ser manual (liderança troca `status` no admin) ou automática (comando agendado). As datas existem para o cálculo automático e para exibir contador regressivo ao usuário.

## Adições ao modelo `VariacaoProduto`

| Campo | Tipo | Notas |
|---|---|---|
| `cota_pre_venda` | PositiveIntegerField(default=0) | Cota por variação; soma deve bater com `produto.cota_pre_venda` |
| `vendido_pre_venda` | PositiveIntegerField(default=0) | Contador específico de pré-venda |

> **Decisão de design:** `vendido_pre_venda` é um contador separado do `estoque` normal. Pré-venda **não** decrementa `estoque`. Quando produção chega, liderança adiciona o `estoque` manualmente (Etapa 06: ajuste de estoque).

## Adições ao modelo `Pedido`

| Campo | Tipo | Notas |
|---|---|---|
| `eh_pre_venda` | BooleanField(default=False) | Se `True`, segue fluxo de pré-venda |
| `data_producao_estimada` | DateField(null=True, blank=True) | Quando o produto deve chegar |
| `data_disponivel_retirada` | DateTimeField(null=True, blank=True) | Quando virou `PRONTO` |

Quando o pedido é todo de pré-venda, `eh_pre_venda=True`. Pedidos mistos (pré-venda + venda normal) **não são permitidos** — bloquear no checkout.

## Modelo novo: `ListaEspera`

| Campo | Tipo | Notas |
|---|---|---|
| `produto` | FK(Produto, on_delete=CASCADE, related_name='lista_espera') | |
| `variacao` | FK(VariacaoProduto, null=True, blank=True, on_delete=CASCADE) | Pode ser por variação específica |
| `usuario` | FK(User, on_delete=CASCADE) | |
| `criado_em` | DateTimeField(auto_now_add=True) | |
| `notificado_em` | DateTimeField(null=True, blank=True) | |

`Meta.unique_together = [('produto', 'variacao', 'usuario')]`

## Constantes

Já cobertos: `PRODUTO_EM_BREVE`, `PRODUTO_PRE_VENDA`, `PEDIDO_AGUARDANDO_PRODUCAO`.

Adicionar:
```python
# Tempo de prioridade para lista de espera (em horas)
LISTA_ESPERA_PRIORIDADE_HORAS = 24
```

## Fluxo de pré-venda

```
1. Liderança cria produto em RASCUNHO com:
   - cota_pre_venda = 50
   - preco_pre_venda = 39.90 (preco normal 49.90)
   - datas: pre_venda_inicio = 2026-07-01, pre_venda_fim = 2026-07-15
   - producao_estimada_dias = 30

2. Em 2026-07-01, status muda para PRE_VENDA (manual ou cron)
   - Produto aparece no catálogo com badge "Pré-venda" e preço promocional
   - Contador regressivo: "Pré-venda encerra em XX:XX:XX"
   - Contador de cota: "Restam 32 de 50 unidades"

3. Usuário compra normalmente. Pedido é criado com:
   - eh_pre_venda = True
   - status = AGUARDANDO_PAGAMENTO
   - data_producao_estimada = pre_venda_fim + producao_estimada_dias

4. Após pagamento confirmado pelo webhook:
   - status muda para AGUARDANDO_PRODUCAO (não para PAGO direto)
   - variacao.vendido_pre_venda += quantidade
   - E-mail: "Pedido confirmado. Produto chegará por volta de DD/MM/YYYY"

5. Em 2026-07-15, pré-venda encerra:
   - Liderança vê relatório de produção: total por variação
   - Status muda para VENDA_NORMAL (ou ESGOTADO se cota esgotou e não houver estoque normal)

6. Produção chega (ex.: 2026-08-14):
   - Liderança adiciona estoque normal (Etapa 06)
   - Para cada pedido com eh_pre_venda=True e status=AGUARDANDO_PRODUCAO:
     - Status muda para PRONTO (em lote)
     - E-mail: "Seu produto chegou! Pronto para retirada/envio"

7. Daí segue fluxo normal de retirada/envio (Etapa 05)
```

## Modificação no handler `confirmar_pedido_pago`

```python
# Após validar valor e marcar como pago, verificar se é pré-venda
if pedido.eh_pre_venda:
    pedido.status = constants.PEDIDO_AGUARDANDO_PRODUCAO
    # Calcula data estimada
    data_base = pedido.itens.first().variacao.produto.pre_venda_fim or timezone.now()
    dias = pedido.itens.first().variacao.produto.producao_estimada_dias
    pedido.data_producao_estimada = (data_base + timedelta(days=dias)).date()
    # Incrementa contador de pré-venda
    for item in pedido.itens.all():
        VariacaoProduto.objects.filter(pk=item.variacao_id).update(
            vendido_pre_venda=F('vendido_pre_venda') + item.quantidade
        )
else:
    pedido.status = constants.PEDIDO_PAGO

pedido.save()
emails.enviar_pedido_pago(pedido)
```

## Comandos novos

### `transicionar_fases_produtos`

```python
class Command(BaseCommand):
    help = 'Transiciona produtos entre fases automaticamente baseado nas datas.'

    def handle(self, *args, **opts):
        agora = timezone.now()
        # EM_BREVE → PRE_VENDA
        Produto.objects.filter(
            status=constants.PRODUTO_EM_BREVE,
            pre_venda_inicio__lte=agora,
        ).update(status=constants.PRODUTO_PRE_VENDA)

        # PRE_VENDA → VENDA_NORMAL (ou ESGOTADO se cota esgotou)
        for p in Produto.objects.filter(status=constants.PRODUTO_PRE_VENDA, pre_venda_fim__lte=agora):
            if p.estoque_total == 0:
                p.status = constants.PRODUTO_ESGOTADO
            else:
                p.status = constants.PRODUTO_VENDA_NORMAL
            p.save()

        # VENDA_NORMAL → ENCERRADO
        Produto.objects.filter(
            status=constants.PRODUTO_VENDA_NORMAL,
            venda_normal_fim__lte=agora,
        ).update(status=constants.PRODUTO_ENCERRADO)
```

Rodar manualmente quando necessário (ou colocar em cron caso o usuário queira no futuro — não é crítico).

### `liberar_pedidos_pre_venda <produto_id>`

Para liderança chamar quando produção chegou:

```python
class Command(BaseCommand):
    help = 'Marca todos os pedidos de pré-venda de um produto como PRONTO.'

    def add_arguments(self, parser):
        parser.add_argument('produto_id', type=int)

    def handle(self, *args, produto_id, **opts):
        pedidos = Pedido.objects.filter(
            eh_pre_venda=True,
            status=constants.PEDIDO_AGUARDANDO_PRODUCAO,
            itens__variacao__produto_id=produto_id,
        ).distinct()
        for p in pedidos:
            p.status = constants.PEDIDO_PRONTO
            p.data_disponivel_retirada = timezone.now()
            p.save()
            emails.enviar_pedido_pronto(p)
        self.stdout.write(f'Liberados: {pedidos.count()}')
```

Botão "Liberar pré-venda" no detalhe do produto no backoffice.

### `notificar_lista_espera <produto_id>`

```python
class Command(BaseCommand):
    help = 'Envia e-mail para usuários da lista de espera de um produto.'

    def handle(self, *args, produto_id, **opts):
        from .models import ListaEspera
        agora = timezone.now()
        esperando = ListaEspera.objects.filter(
            produto_id=produto_id, notificado_em__isnull=True
        )
        for le in esperando:
            emails.enviar_disponivel_lista_espera(le)
            le.notificado_em = agora
            le.save()
```

Botão "Notificar lista de espera" no backoffice.

## Views/URLs novas

```python
urlpatterns += [
    path('produto/<slug:slug>/lista-espera/', catalogo.entrar_lista_espera, name='entrar_lista_espera'),
    path('produto/<slug:slug>/lista-espera/sair/', catalogo.sair_lista_espera, name='sair_lista_espera'),

    # Backoffice
    path('gestao/produtos/<int:id>/relatorio-producao/', gestao.relatorio_producao, name='gestao_relatorio_producao'),
    path('gestao/produtos/<int:id>/liberar-pre-venda/', gestao.liberar_pre_venda, name='gestao_liberar_pre_venda'),
    path('gestao/produtos/<int:id>/notificar-lista-espera/', gestao.notificar_lista_espera, name='gestao_notificar_lista_espera'),
]
```

### `gestao.relatorio_producao(request, id)`

Mostra para um produto específico:

| Variação | Cota pré-venda | Vendido pré-venda | Restante na cota |
|---|---|---|---|
| P / Preto | 10 | 7 | 3 |
| M / Preto | 15 | 15 | 0 (esgotado) |
| G / Preto | 15 | 12 | 3 |
| ... | | | |
| **TOTAL** | **50** | **39** | **11** |

Botão "Exportar CSV" para enviar à gráfica.

## Templates novos / alterados

```
templates/loja/
├── catalogo/
│   └── detalhe_produto.html      # adicionar:
│                                  # - Contador regressivo (JS simples)
│                                  # - Badge "Pré-venda" / "Em breve"
│                                  # - Preço promocional riscado
│                                  # - Contador de unidades restantes na cota
│                                  # - Botão "Entrar na lista de espera" se ESGOTADO
└── gestao/
    └── produtos/
        ├── relatorio_producao.html
        └── _form_fases.html      # Datas de fases no editar produto
```

## Critérios de aceite

- [ ] Produto pode ser criado com fases configuradas
- [ ] Comando `transicionar_fases_produtos` move produtos pelas fases nas datas certas
- [ ] Catálogo mostra badge correta (Em breve / Pré-venda / À venda / Esgotado)
- [ ] Detalhe do produto em pré-venda mostra:
  - [ ] Preço promocional + preço normal riscado
  - [ ] Contador regressivo até fim da pré-venda
  - [ ] Contador de cota restante
- [ ] Comprar produto em pré-venda gera pedido com `eh_pre_venda=True`
- [ ] Pedido pago em pré-venda fica em `AGUARDANDO_PRODUCAO` (não `PAGO` direto)
- [ ] E-mail de confirmação inclui data estimada de chegada
- [ ] Relatório de produção mostra total pedido por variação
- [ ] Botão "Liberar pré-venda" muda todos os pedidos relacionados para `PRONTO` e envia e-mail
- [ ] Cota não pode ser excedida (estoque pré-venda checado no checkout via `vendido_pre_venda < cota_pre_venda`)
- [ ] Produto esgotado mostra botão "Entrar na lista de espera"
- [ ] Usuário consegue entrar e sair da lista de espera
- [ ] Comando `notificar_lista_espera` envia e-mail para todos não-notificados
- [ ] Pedido misto (pré-venda + venda normal) é bloqueado no checkout com mensagem clara

## Casos de uso cobertos

- CU-01 completo (camiseta de evento em pré-venda)
- CU-05 completo (esgotado + lista de espera)
- CU-06 completo (liderança gerencia produção)

## Estimativa

2 dias (16 horas com Claude Code).

## Pontos de atenção

1. **Contador regressivo** em JS puro (sem libs). Atualiza a cada segundo usando `setInterval`.
2. **`vendido_pre_venda` é F-expression**: `update(vendido_pre_venda=F(...)+1)` para atomicidade.
3. **Cota esgotada ≠ produto esgotado**: cota pré-venda pode esgotar mesmo com estoque normal cheio (raro, mas possível).
4. **Lista de espera de variação específica**: se usuário entra na lista de "P / Preto", só recebe e-mail quando essa variação específica voltar.
5. **Pedido misto bloqueado**: detectar no checkout. Se carrinho tem itens com `produto.status == PRE_VENDA` e outros com `VENDA_NORMAL`, exigir que finalize separadamente.
6. **`liberar_pre_venda` é manual** — liderança decide quando rodar (não automatize por data).
