# Etapa 10 — Integrações (emblemas, perfil)

## Objetivo

Costurar a loja com o restante da plataforma:

1. Conceder emblema automaticamente ao comprar produto específico
2. Mostrar histórico de compras, bilhetes de rifa e contribuições no perfil do usuário
3. Conectar pedidos a eventos no painel de relatórios de eventos

## Pré-requisitos

- Etapa 04 concluída (pedidos)
- Etapa 09 concluída (rifas e contribuições) — se quiser histórico completo no perfil
- App `apps.emblemas` já existente

---

## 10.1 — Emblema automático por compra

### Modelo: `RegraEmblema`

| Campo | Tipo | Notas |
|---|---|---|
| `produto` | FK(Produto, null=True, blank=True, on_delete=CASCADE) | Se preenchido, regra atrelada a esse produto |
| `categoria` | FK(Categoria, null=True, blank=True, on_delete=CASCADE) | Ou a uma categoria inteira |
| `evento` | FK(Evento, null=True, blank=True, on_delete=CASCADE) | Ou a qualquer compra de evento |
| `emblema` | FK(Emblema, on_delete=PROTECT) | Emblema a conceder |
| `valor_minimo` | DecimalField(10, 2, default=0) | Apenas pedidos acima desse valor |
| `quantidade_minima` | PositiveIntegerField(default=1) | Quantidade mínima do produto |
| `ativa` | BooleanField(default=True) | |
| `criado_em` | DateTimeField(auto_now_add=True) | |

> Pelo menos um de `produto`, `categoria` ou `evento` deve estar preenchido.

### Hook no handler `confirmar_pedido_pago`

Após marcar pedido como `PAGO`:

```python
def _conceder_emblemas_pedido(pedido):
    from apps.loja.models import RegraEmblema
    from apps.emblemas.models import EmblemaUsuario

    regras = RegraEmblema.objects.filter(ativa=True)
    emblemas_concedidos = set()

    for item in pedido.itens.select_related('variacao__produto__categoria'):
        produto = item.variacao.produto
        for regra in regras:
            if regra.produto_id and regra.produto_id != produto.id:
                continue
            if regra.categoria_id and regra.categoria_id != produto.categoria_id:
                continue
            if regra.evento_id and regra.evento_id != produto.evento_id:
                continue
            if item.quantidade < regra.quantidade_minima:
                continue
            if item.subtotal < regra.valor_minimo:
                continue

            # Evita duplicidade no mesmo pedido
            if regra.emblema_id in emblemas_concedidos:
                continue

            EmblemaUsuario.objects.get_or_create(
                emblema=regra.emblema,
                usuario=pedido.usuario,
                defaults={'concedido_por': regra.emblema.criado_por},
            )
            emblemas_concedidos.add(regra.emblema_id)
```

Chamar essa função no handler logo após `emails.enviar_pedido_pago(pedido)`.

### URLs no backoffice

```python
urlpatterns += [
    path('gestao/regras-emblema/', gestao.regras_emblema_lista, name='gestao_regras_emblema'),
    path('gestao/regras-emblema/nova/', gestao.regra_emblema_criar, name='gestao_regra_emblema_criar'),
]
```

### Critérios de aceite

- [ ] Liderança cria regra: "Quem comprar produto X ganha emblema Y"
- [ ] Liderança cria regra: "Quem comprar qualquer produto da categoria 'Livros UMP' ganha emblema 'Leitor'"
- [ ] Após pagamento confirmado, sistema concede emblema sem duplicar (idempotente)
- [ ] Notificação de emblema pendente já existente (`apps.emblemas.context_processors.emblemas_pendentes`) aparece para o usuário

---

## 10.2 — Histórico no perfil do usuário

### Nova aba/seção no perfil

No template do perfil (provavelmente `templates/usuarios/perfil.html`), adicionar abas/seções:

- **Inscrições** (já existe)
- **Pedidos** (novo)
- **Bilhetes de rifa** (novo — depende de Etapa 09)
- **Contribuições** (novo — depende de Etapa 09)
- **Emblemas** (já existe)

### Views novas

```python
# Em apps/loja/views/pedido.py
def historico_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-criado_em')
    return render(request, 'loja/perfil/pedidos.html', {'pedidos': pedidos})

# Em apps/loja/views/modalidades.py (Etapa 09)
def historico_bilhetes(request):
    bilhetes = BilheteRifa.objects.filter(usuario=request.user).select_related('rifa').order_by('-criado_em')
    return render(request, 'loja/perfil/bilhetes.html', {'bilhetes': bilhetes})

def historico_contribuicoes(request):
    contribs = ContribuicaoCampanha.objects.filter(usuario=request.user).select_related('campanha').order_by('-criado_em')
    return render(request, 'loja/perfil/contribuicoes.html', {'contribs': contribs})
```

### URLs

```python
urlpatterns += [
    path('perfil/pedidos/', pedido.historico_pedidos, name='perfil_pedidos'),
    path('perfil/bilhetes/', modalidades.historico_bilhetes, name='perfil_bilhetes'),
    path('perfil/contribuicoes/', modalidades.historico_contribuicoes, name='perfil_contribuicoes'),
]
```

### Alternativa (mais elegante): tabs HTMX

Em vez de páginas separadas, criar abas dinâmicas no perfil que carregam o conteúdo via HTMX:

```html
<nav class="border-b flex gap-4">
  <a hx-get="{% url 'perfil_inscricoes' %}" hx-target="#perfil-content" class="tab">Inscrições</a>
  <a hx-get="{% url 'perfil_pedidos' %}" hx-target="#perfil-content" class="tab">Pedidos</a>
  <a hx-get="{% url 'perfil_bilhetes' %}" hx-target="#perfil-content" class="tab">Bilhetes</a>
  <a hx-get="{% url 'perfil_contribuicoes' %}" hx-target="#perfil-content" class="tab">Contribuições</a>
  <a hx-get="{% url 'perfil_emblemas' %}" hx-target="#perfil-content" class="tab">Emblemas</a>
</nav>
<div id="perfil-content">
  {# Conteúdo carregado via HTMX #}
</div>
```

### Critérios de aceite

- [ ] Usuário acessa `/perfil/` e vê todas as seções (inscrições, pedidos, bilhetes, contribuições, emblemas)
- [ ] Em "Pedidos", lista com número, data, status, valor e link para detalhe
- [ ] Em "Bilhetes", lista com rifa, número (se pago), status
- [ ] Em "Contribuições", lista com campanha, valor, status
- [ ] Lista vazia mostra mensagem amigável ("Você ainda não fez nenhum pedido")
- [ ] Performance: cada query usa `select_related` apropriado

---

## 10.3 — Relatório de produtos por evento

No painel de gestão do **evento** (não da loja), adicionar uma seção:

- Lista de produtos vinculados a esse evento (`produto.evento == evento`)
- Estatística: quantos pedidos, valor total arrecadado em produtos do evento
- Link para `/loja/gestao/relatorios/por-evento/<slug>/` (Etapa 06)

### Onde implementar

Em `apps/eventos/views.py`, na view `gerenciar_eventos` ou `detalhe_evento` (admin), adicionar bloco que importa de `apps.loja`:

```python
from apps.loja.models import Produto, Pedido

def gerenciar_evento(request, slug):
    # ... lógica existente ...
    produtos_evento = Produto.objects.filter(evento=evento).count()
    pedidos_evento = Pedido.objects.filter(
        evento=evento, status=constants.PEDIDO_PAGO
    ).count()
    valor_evento = Pedido.objects.filter(
        evento=evento, status__in=[constants.PEDIDO_PAGO, ...]
    ).aggregate(total=Sum('valor_total'))['total'] or 0
    # ...
```

### Critérios de aceite

- [ ] Liderança no detalhe do evento vê quantos produtos estão vinculados
- [ ] Vê total arrecadado em produtos desse evento
- [ ] Link para o relatório completo da loja

---

## Critérios de aceite globais (Etapa 10)

- [ ] Comprar produto X concede emblema Y automaticamente
- [ ] Emblema não é concedido em duplicidade (mesmo se comprar produto várias vezes)
- [ ] Perfil mostra todos os históricos relevantes ao usuário
- [ ] Painel do evento mostra dados da loja relacionados àquele evento

## Casos de uso cobertos

- CU-07 (comprador de produto X ganha emblema)
- Histórico unificado do usuário

## Estimativa

0,5 dia (4 horas com Claude Code).

## Pontos de atenção

1. **`get_or_create` para emblemas**: evita duplicação se o handler rodar 2x por algum motivo.
2. **`concedido_por` no emblema**: precisa de um User. Usar `regra.emblema.criado_por` ou criar um usuário "Sistema" dedicado.
3. **Conflito de regras**: se 2 regras se aplicam ao mesmo pedido, ambas concedem (intencional). Liderança gerencia.
4. **Não criar dependência circular**: `apps.loja` importa de `apps.emblemas`, mas `apps.emblemas` **não** deve importar de `apps.loja`.
5. **Performance no perfil**: se tabs forem HTMX, lazy-load por aba evita queries desnecessárias.
6. **Notificação de emblema** já está implementada (`apps.emblemas.context_processors`). Reaproveitar.
