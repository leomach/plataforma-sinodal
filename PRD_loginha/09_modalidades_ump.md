# Etapa 09 — Modalidades específicas da UMP

## Objetivo

Implementar 3 modalidades não-comuns em e-commerce genérico, mas comuns em organizações religiosas:

1. **Rifa** — bilhetes numerados com sorteio
2. **Vaquinha (Campanha de arrecadação)** — meta de valor com progresso
3. **Doação livre** — usuário escolhe quanto contribuir

Todas usam o pipeline de pagamento do app `apps.pagamentos`, com handlers próprios.

## Pré-requisitos

- Etapa 04 concluída (pagamento via InfinitePay)

---

## 9.1 — Rifa

### Conceito

Liderança cria uma rifa com:
- Quantidade total de bilhetes (ex.: 100)
- Preço por bilhete (ex.: R$ 10)
- Prêmio (texto descritivo)
- Data do sorteio

Usuários compram um ou mais bilhetes. Sistema atribui número único automaticamente após pagamento confirmado. Quando todos os bilhetes são vendidos (ou na data), liderança roda o sorteio.

### Modelos

#### `Rifa`

| Campo | Tipo | Notas |
|---|---|---|
| `titulo` | CharField(150) | |
| `slug` | SlugField(unique=True) | |
| `descricao` | TextField | |
| `imagem` | ImageField(blank=True) | |
| `quantidade_total` | PositiveIntegerField | Ex.: 100 |
| `preco_bilhete` | DecimalField(10, 2) | |
| `premio` | TextField | Descrição do prêmio |
| `data_sorteio` | DateTimeField | |
| `status` | IntegerField(choices=RIFA_STATUS_CHOICES, default=ABERTA) | |
| `evento` | FK(Evento, null=True, blank=True, on_delete=SET_NULL) | |
| `criado_por` | FK(User, on_delete=PROTECT) | |
| `criado_em` | DateTimeField(auto_now_add=True) | |
| `sorteado_em` | DateTimeField(null=True, blank=True) | |
| `bilhete_vencedor` | OneToOneField(BilheteRifa, null=True, blank=True, on_delete=SET_NULL, related_name='rifa_vencida') | |

Properties:
- `bilhetes_vendidos` → count de `BilheteRifa.status == PAGO`
- `disponivel` → `quantidade_total - bilhetes_vendidos`
- `valor_arrecadado` → soma

#### `BilheteRifa`

| Campo | Tipo | Notas |
|---|---|---|
| `rifa` | FK(Rifa, on_delete=CASCADE, related_name='bilhetes') | |
| `numero` | PositiveIntegerField(null=True) | Atribuído após pagamento. Null = ainda não pago |
| `usuario` | FK(User, on_delete=PROTECT) | |
| `status` | IntegerField(choices=BILHETE_STATUS_CHOICES, default=AGUARDANDO_PAGAMENTO) | |
| `infinitepay_url` | URLField(500, blank=True) | |
| `infinitepay_invoice_slug` | CharField(100, blank=True) | |
| `transacao` | FK(TransacaoInfinitePay, null=True, on_delete=SET_NULL) | |
| `criado_em` | DateTimeField(auto_now_add=True) | |
| `data_pagamento` | DateTimeField(null=True, blank=True) | |

`Meta.constraints = [UniqueConstraint(fields=['rifa', 'numero'], name='unique_numero_por_rifa')]`

### Atribuição de número

**Decisão:** atribuir número **apenas após pagamento confirmado**. Evita "bilhetes fantasma" de quem nunca pagou.

No handler:
```python
@register_payment_handler('bilhete')
def confirmar_bilhete_pago(*, order_nsu, transacao, payload):
    bilhete_id = int(order_nsu.split('-', 1)[1])
    bilhete = BilheteRifa.objects.select_for_update().get(pk=bilhete_id)
    # ... valida valor ...
    with transaction.atomic():
        rifa = Rifa.objects.select_for_update().get(pk=bilhete.rifa_id)
        proximo = _proximo_numero_disponivel(rifa)
        if proximo is None:
            # Rifa esgotou enquanto este bilhete estava pendente
            # Cancela e marca para reembolso manual
            bilhete.status = BILHETE_REEMBOLSAR
            bilhete.save()
            return
        bilhete.numero = proximo
        bilhete.status = BILHETE_PAGO
        bilhete.transacao = transacao
        bilhete.data_pagamento = timezone.now()
        bilhete.save()
    emails.enviar_bilhete_confirmado(bilhete)
```

`_proximo_numero_disponivel(rifa)`:
- Pega todos os números já atribuídos
- Retorna o menor número de 1 a `quantidade_total` que não está usado
- Retorna `None` se todos estão usados

### Sorteio

```python
import secrets

def sortear(rifa, executado_por):
    bilhetes_pagos = rifa.bilhetes.filter(status=BILHETE_PAGO)
    if not bilhetes_pagos.exists():
        raise ValueError('Rifa sem bilhetes pagos')
    vencedor = secrets.choice(list(bilhetes_pagos))
    rifa.bilhete_vencedor = vencedor
    rifa.status = RIFA_SORTEADA
    rifa.sorteado_em = timezone.now()
    rifa.save()
    emails.notificar_vencedor(vencedor)
    emails.notificar_participantes_sorteio(rifa)
```

Botão "Sortear" no backoffice. Usa `secrets.choice` (criptograficamente seguro).

### Constantes

```python
RIFA_ABERTA = 1
RIFA_ESGOTADA = 2
RIFA_AGUARDANDO_SORTEIO = 3
RIFA_SORTEADA = 4
RIFA_CANCELADA = 5

RIFA_STATUS_CHOICES = [...]

BILHETE_AGUARDANDO_PAGAMENTO = 1
BILHETE_PAGO = 2
BILHETE_CANCELADO = 3
BILHETE_REEMBOLSAR = 4   # Pagou mas rifa esgotou primeiro

BILHETE_STATUS_CHOICES = [...]
```

### URLs

```python
urlpatterns += [
    path('rifa/<slug:slug>/', modalidades.rifa_detalhe, name='rifa_detalhe'),
    path('rifa/<slug:slug>/comprar/', modalidades.rifa_comprar, name='rifa_comprar'),
    path('bilhete/<int:bilhete_id>/', modalidades.bilhete_detalhe, name='bilhete_detalhe'),
    path('bilhete/<int:bilhete_id>/pagar/', modalidades.bilhete_pagar, name='bilhete_pagar'),

    path('gestao/rifas/', gestao.rifas_lista, name='gestao_rifas'),
    path('gestao/rifas/nova/', gestao.rifa_criar, name='gestao_rifa_criar'),
    path('gestao/rifas/<int:id>/sortear/', gestao.rifa_sortear, name='gestao_rifa_sortear'),
]
```

### Templates

```
templates/loja/rifa/
├── detalhe.html        # Página pública da rifa
├── comprar.html        # Form: quantos bilhetes
└── bilhete.html        # Detalhe do bilhete (com número após pagar)
```

### Critérios de aceite (Rifa)

- [ ] Liderança cria rifa com quantidade, preço e prêmio
- [ ] Página pública mostra rifa, bilhetes vendidos/total, valor arrecadado
- [ ] Usuário compra X bilhetes (cria X `BilheteRifa` com status `AGUARDANDO_PAGAMENTO`)
- [ ] Link InfinitePay gerado (1 link por bilhete OU 1 link para o pacote — escolher: pacote é mais simples)
- [ ] Após pagamento, handler atribui número único atomicamente
- [ ] Se rifa esgotar enquanto pagamento estava pendente, bilhete fica `REEMBOLSAR` (liderança trata manualmente)
- [ ] Usuário vê seu(s) número(s) em `/loja/bilhete/<id>/`
- [ ] Quando todos os bilhetes pagos: status muda para `AGUARDANDO_SORTEIO`
- [ ] Liderança clica "Sortear" → vencedor escolhido aleatoriamente
- [ ] E-mail para vencedor + e-mail para participantes anunciando

---

## 9.2 — Vaquinha (Campanha de arrecadação)

### Conceito

Liderança cria campanha com meta de valor (ex.: R$ 15.000 para reforma). Usuários contribuem com valor à escolha. Barra de progresso visível.

### Modelos

#### `Campanha`

| Campo | Tipo | Notas |
|---|---|---|
| `titulo` | CharField(150) | |
| `slug` | SlugField(unique=True) | |
| `descricao` | TextField | |
| `imagem` | ImageField(blank=True) | |
| `meta_valor` | DecimalField(10, 2) | Ex.: 15000.00 |
| `valor_minimo_contribuicao` | DecimalField(10, 2, default=10) | |
| `data_inicio` | DateTimeField | |
| `data_fim` | DateTimeField(null=True, blank=True) | Pode ser permanente |
| `status` | IntegerField(choices=CAMPANHA_STATUS_CHOICES, default=ABERTA) | |
| `evento` | FK(Evento, null=True, blank=True, on_delete=SET_NULL) | |
| `mostrar_contribuintes` | BooleanField(default=True) | Lista pública de contribuintes |
| `permitir_anonimo` | BooleanField(default=True) | |
| `criado_por` | FK(User, on_delete=PROTECT) | |
| `criado_em` | DateTimeField(auto_now_add=True) | |

Properties:
- `valor_arrecadado` → soma de `contribuicoes.status=PAGO`
- `percentual` → `valor_arrecadado / meta_valor * 100`
- `total_contribuintes` → count distinct de usuários

#### `ContribuicaoCampanha`

| Campo | Tipo | Notas |
|---|---|---|
| `campanha` | FK(Campanha, on_delete=CASCADE, related_name='contribuicoes') | |
| `usuario` | FK(User, on_delete=PROTECT) | |
| `valor` | DecimalField(10, 2) | |
| `anonimo` | BooleanField(default=False) | Não mostra nome na lista |
| `mensagem` | CharField(255, blank=True) | "Que Deus abençoe" |
| `status` | IntegerField(choices=PEDIDO_STATUS_CHOICES_INICIAL) | |
| `infinitepay_url` | URLField(500, blank=True) | |
| `infinitepay_invoice_slug` | CharField(100, blank=True) | |
| `transacao` | FK(TransacaoInfinitePay, null=True, on_delete=SET_NULL) | |
| `criado_em` | DateTimeField(auto_now_add=True) | |
| `data_pagamento` | DateTimeField(null=True, blank=True) | |

### Handler

```python
@register_payment_handler('contribuicao')
def confirmar_contribuicao_paga(*, order_nsu, transacao, payload):
    contribuicao_id = int(order_nsu.split('-', 1)[1])
    # ... mesma lógica de validação ...
    # Marca como PAGO, envia e-mail de agradecimento
```

### Constantes

```python
CAMPANHA_ABERTA = 1
CAMPANHA_META_ATINGIDA = 2
CAMPANHA_ENCERRADA = 3
CAMPANHA_CANCELADA = 4

CAMPANHA_STATUS_CHOICES = [...]
```

### URLs

```python
urlpatterns += [
    path('campanha/<slug:slug>/', modalidades.campanha_detalhe, name='campanha_detalhe'),
    path('campanha/<slug:slug>/contribuir/', modalidades.campanha_contribuir, name='campanha_contribuir'),
    path('contribuicao/<int:id>/pagar/', modalidades.contribuicao_pagar, name='contribuicao_pagar'),

    path('gestao/campanhas-arrecadacao/', gestao.campanhas_arrec_lista, name='gestao_campanhas_arrec'),
    path('gestao/campanhas-arrecadacao/nova/', gestao.campanha_arrec_criar, name='gestao_campanha_arrec_criar'),
]
```

### Templates

```
templates/loja/campanha/
├── detalhe.html        # Página pública (barra, contribuintes, descrição)
└── contribuir.html     # Form: valor, mensagem, anônimo?
```

### Critérios de aceite (Vaquinha)

- [ ] Liderança cria campanha com meta e descrição
- [ ] Página pública mostra:
  - [ ] Barra de progresso (% da meta)
  - [ ] Valor arrecadado / meta
  - [ ] Lista de últimos contribuintes (respeitando anônimos)
  - [ ] Botão "Contribuir"
- [ ] Usuário escolhe valor (≥ mínimo)
- [ ] Pagamento via InfinitePay
- [ ] Após pago, contribuição aparece na lista
- [ ] Quando meta atingida, banner especial e e-mail para liderança
- [ ] Pode contribuir múltiplas vezes
- [ ] Histórico de contribuições no perfil do usuário

---

## 9.3 — Doação livre

### Conceito

É uma **vaquinha simplificada sem meta**. Reutiliza `Campanha` com `meta_valor=0` e UI ligeiramente diferente.

**Decisão de design:** **não criar modelo separado**. Adicionar campo `tipo` em `Campanha`:

```python
CAMPANHA_TIPO_META = 1     # Vaquinha clássica
CAMPANHA_TIPO_LIVRE = 2    # Doação livre

class Campanha(models.Model):
    tipo = models.IntegerField(choices=CAMPANHA_TIPO_CHOICES, default=CAMPANHA_TIPO_META)
    # ...
```

Quando `tipo == LIVRE`, oculta barra de progresso, oculta meta, mostra apenas "Total arrecadado".

### Critérios de aceite (Doação livre)

- [ ] Liderança cria doação livre (sem informar meta)
- [ ] Página pública não mostra barra/meta
- [ ] Demais funcionalidades idênticas à vaquinha

---

## Critérios de aceite globais (Etapa 09)

- [ ] 3 handlers registrados em `apps.pagamentos.handlers.get_registered_prefixes()` → `['inscricao', 'pedido', 'bilhete', 'contribuicao']`
- [ ] Sorteio de rifa é reproducível com `secrets.choice` (não usar `random` padrão)
- [ ] Validação de valor mínimo na contribuição
- [ ] Bilhetes não recebem número se rifa esgotar antes do pagamento confirmar (fica como `REEMBOLSAR`)
- [ ] E-mails específicos para cada modalidade

## Casos de uso cobertos

- CU-03 (rifa) completo
- CU-04 (vaquinha) completo
- Doação livre

## Estimativa

2–3 dias (16–24 horas com Claude Code).

- Rifa: 1 dia
- Vaquinha: 1 dia
- Doação livre (em cima da vaquinha): 0,5 dia
- Backoffice das 3: 0,5 dia

## Pontos de atenção

1. **Atomicidade na atribuição de número**: usar `select_for_update` na `Rifa` + verificação se ainda há disponibilidade. Cenário de corrida real.
2. **Sorteio cripto-seguro**: `secrets.choice` em vez de `random.choice`. Auditável.
3. **Anônimo respeitado em queries**: ao listar contribuintes, sempre filtrar para esconder nome dos anônimos no lado do servidor (não confiar no frontend).
4. **Bilhetes pagos não podem ser reembolsados via sistema** — só via marcação manual da liderança (não tocar em InfinitePay programaticamente).
5. **Notificação do sorteio**: enviar antes do horário marcado e logo após o resultado.
6. **Histórico no perfil**: novas seções "Meus bilhetes", "Minhas contribuições" — coordenar com Etapa 10.
