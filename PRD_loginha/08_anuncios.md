# Etapa 08 — Anúncios e comunicação

## Objetivo

Permitir que liderança crie banners e destaques que apareçam em toda a plataforma (não só na loja). Enviar e-mail marketing segmentado para inscritos em evento sobre produtos relacionados. Reutilizar lista de espera (Etapa 07) como base para notificações.

## Pré-requisitos

- Etapa 02 concluída (catálogo)
- (Recomendado) Etapa 07 concluída para integrar lista de espera

## Modelo: `Anuncio`

| Campo | Tipo | Notas |
|---|---|---|
| `titulo` | CharField(100) | |
| `subtitulo` | CharField(200, blank=True) | |
| `imagem` | ImageField(blank=True, null=True) | |
| `cor_fundo` | CharField(7, default='#1e40af') | Hex |
| `cor_texto` | CharField(7, default='#ffffff') | Hex |
| `link_url` | CharField(500, blank=True) | URL externa OU produto/categoria interno |
| `produto` | FK(Produto, null=True, blank=True, on_delete=SET_NULL) | Se aponta para produto |
| `posicao` | IntegerField(choices=ANUNCIO_POSICAO_CHOICES) | onde aparece |
| `publico_alvo` | IntegerField(choices=ANUNCIO_PUBLICO_CHOICES, default=TODOS) | |
| `evento` | FK(Evento, null=True, blank=True, on_delete=SET_NULL) | Se `publico_alvo == INSCRITOS_EVENTO` |
| `inicio` | DateTimeField | |
| `fim` | DateTimeField | |
| `ativo` | BooleanField(default=True) | |
| `prioridade` | PositiveIntegerField(default=0) | Maior = aparece primeiro |
| `criado_por` | FK(User, on_delete=PROTECT) | |
| `criado_em` | DateTimeField(auto_now_add=True) | |

`Meta.ordering = ['-prioridade', '-inicio']`

## Constantes

```python
# Posições onde anúncios podem aparecer
ANUNCIO_POS_HOME_TOPO = 1          # Banner no topo da home
ANUNCIO_POS_HUB = 2                # Sidebar do hub
ANUNCIO_POS_LOJA = 3               # Topo do catálogo
ANUNCIO_POS_GLOBAL = 4             # Aparece em todas as páginas como faixa fina

ANUNCIO_POSICAO_CHOICES = [
    (ANUNCIO_POS_HOME_TOPO, _('Topo da home')),
    (ANUNCIO_POS_HUB, _('Sidebar do hub')),
    (ANUNCIO_POS_LOJA, _('Topo da loja')),
    (ANUNCIO_POS_GLOBAL, _('Faixa global')),
]

# Público-alvo
ANUNCIO_PUB_TODOS = 1
ANUNCIO_PUB_LOGADOS = 2
ANUNCIO_PUB_LIDERANCA = 3
ANUNCIO_PUB_SOCIOS = 4
ANUNCIO_PUB_INSCRITOS_EVENTO = 5

ANUNCIO_PUBLICO_CHOICES = [
    (ANUNCIO_PUB_TODOS, _('Todos (público)')),
    (ANUNCIO_PUB_LOGADOS, _('Logados')),
    (ANUNCIO_PUB_LIDERANCA, _('Liderança')),
    (ANUNCIO_PUB_SOCIOS, _('Sócios')),
    (ANUNCIO_PUB_INSCRITOS_EVENTO, _('Inscritos em evento')),
]
```

## Service: `apps/loja/services/anuncios.py`

```python
def anuncios_visiveis_para(request, posicao: int) -> list:
    """Retorna anúncios ativos para a posição e usuário atual."""
    agora = timezone.now()
    qs = Anuncio.objects.filter(
        ativo=True,
        posicao=posicao,
        inicio__lte=agora,
        fim__gte=agora,
    )

    user = request.user

    # Filtra por público-alvo
    publicos = [ANUNCIO_PUB_TODOS]
    if user.is_authenticated:
        publicos.append(ANUNCIO_PUB_LOGADOS)
        if user.tipo == constants.SOCIO:
            publicos.append(ANUNCIO_PUB_SOCIOS)
        if is_lideranca(user):
            publicos.append(ANUNCIO_PUB_LIDERANCA)

    qs = qs.filter(publico_alvo__in=publicos + [ANUNCIO_PUB_INSCRITOS_EVENTO])

    # Para INSCRITOS_EVENTO, valida que user tem inscrição aprovada
    visiveis = []
    for a in qs:
        if a.publico_alvo == ANUNCIO_PUB_INSCRITOS_EVENTO:
            if not user.is_authenticated:
                continue
            tem = user.inscricoes.filter(
                evento_id=a.evento_id,
                status=constants.STATUS_APROVADO,
            ).exists()
            if not tem:
                continue
        visiveis.append(a)
    return visiveis
```

## Context processor

Adicionar em `apps/loja/context_processors.py`:

```python
def anuncios_globais(request):
    from .services.anuncios import anuncios_visiveis_para
    return {
        'anuncios_globais': anuncios_visiveis_para(request, constants.ANUNCIO_POS_GLOBAL),
    }
```

Registrar em `core/settings.py`.

## Como exibir nas templates

### Faixa global em `base.html`

```django
{% if anuncios_globais %}
  {% for a in anuncios_globais %}
    <div class="text-center py-2 text-sm"
         style="background: {{ a.cor_fundo }}; color: {{ a.cor_texto }};">
      <strong>{{ a.titulo }}</strong>
      {% if a.subtitulo %} — {{ a.subtitulo }}{% endif %}
      {% if a.link_url or a.produto %}
        <a href="{% if a.produto %}{% url 'loja:detalhe_produto' a.produto.slug %}{% else %}{{ a.link_url }}{% endif %}"
           class="underline ml-2">Ver</a>
      {% endif %}
    </div>
  {% endfor %}
{% endif %}
```

### Topo da loja

Em `templates/loja/catalogo/index.html`, antes do grid:

```django
{% load loja %}
{% with anuncios=request|anuncios_loja %}
  {% for a in anuncios %}
    <a href="..." class="block rounded-lg overflow-hidden mb-4">
      ...
    </a>
  {% endfor %}
{% endwith %}
```

Criar template tag `anuncios_loja` em `templatetags/loja.py`.

## E-mail marketing segmentado

### Modelo `CampanhaEmail`

| Campo | Tipo | Notas |
|---|---|---|
| `nome` | CharField(150) | Nome interno (não enviado) |
| `assunto` | CharField(200) | Assunto do e-mail |
| `corpo_html` | TextField | Corpo (renderizado em template wrapper) |
| `produto` | FK(Produto, null=True, blank=True, on_delete=SET_NULL) | Para CTA |
| `publico_alvo` | IntegerField(choices=ANUNCIO_PUBLICO_CHOICES) | Reusa choices |
| `evento` | FK(Evento, null=True, blank=True, on_delete=SET_NULL) | |
| `enviado_em` | DateTimeField(null=True, blank=True) | Null = ainda não enviado |
| `total_enviados` | PositiveIntegerField(default=0) | Stats simples |
| `criado_por` | FK(User, on_delete=PROTECT) | |
| `criado_em` | DateTimeField(auto_now_add=True) | |

### Comando: `enviar_campanha_email <id>`

```python
class Command(BaseCommand):
    help = 'Envia uma campanha de e-mail para o público alvo.'

    def add_arguments(self, parser):
        parser.add_argument('campanha_id', type=int)

    def handle(self, *args, campanha_id, **opts):
        campanha = CampanhaEmail.objects.get(pk=campanha_id)
        usuarios = _resolver_publico(campanha)
        # Envia em lotes de 50 para não estourar SMTP
        enviados = 0
        for u in usuarios:
            try:
                _enviar_email_campanha(campanha, u)
                enviados += 1
            except Exception:
                logger.exception('campanha.email.failed', extra={'user': u.id})
        campanha.enviado_em = timezone.now()
        campanha.total_enviados = enviados
        campanha.save()
        self.stdout.write(f'Enviados: {enviados}')
```

`_resolver_publico` retorna queryset de Users baseado no `publico_alvo`:
- `TODOS` → todos os users com email
- `LOGADOS` → mesmo que TODOS (todo cadastrado tem login)
- `LIDERANCA` → `User.objects.filter(tipo=LIDERANCA)`
- `SOCIOS` → `User.objects.filter(tipo=SOCIO)`
- `INSCRITOS_EVENTO` → users com inscrição aprovada no evento

## Lista de espera como funcionalidade de comunicação

Reutilizar `ListaEspera` (Etapa 07) também para produtos que ainda **não** estão à venda (`EM_BREVE`). O botão muda de "Avise-me quando disponível" para "Entrar na lista de espera" conforme o status.

## Views/URLs do backoffice

```python
urlpatterns += [
    # Anúncios
    path('gestao/anuncios/', gestao.anuncios_lista, name='gestao_anuncios'),
    path('gestao/anuncios/novo/', gestao.anuncio_criar, name='gestao_anuncio_criar'),
    path('gestao/anuncios/<int:id>/', gestao.anuncio_editar, name='gestao_anuncio_editar'),
    path('gestao/anuncios/<int:id>/desativar/', gestao.anuncio_desativar, name='gestao_anuncio_desativar'),

    # Campanhas
    path('gestao/campanhas/', gestao.campanhas_lista, name='gestao_campanhas'),
    path('gestao/campanhas/nova/', gestao.campanha_criar, name='gestao_campanha_criar'),
    path('gestao/campanhas/<int:id>/preview/', gestao.campanha_preview, name='gestao_campanha_preview'),
    path('gestao/campanhas/<int:id>/enviar/', gestao.campanha_enviar, name='gestao_campanha_enviar'),
]
```

## Critérios de aceite

- [ ] Liderança cria anúncio com posição, público, datas, cores
- [ ] Anúncio aparece apenas nas datas configuradas (inicio ≤ now ≤ fim)
- [ ] Filtro por público-alvo respeitado (sócio não vê anúncio só para liderança)
- [ ] Faixa global aparece em todas as páginas
- [ ] Anúncio no topo da loja aparece só em `/loja/`
- [ ] Clique em anúncio com produto vinculado redireciona para o detalhe
- [ ] Lista de espera funciona para produtos `EM_BREVE` e `ESGOTADO`
- [ ] Liderança cria campanha de e-mail, faz preview, envia
- [ ] Comando `enviar_campanha_email` envia para todos do público-alvo
- [ ] Stats: campanha mostra `total_enviados` após envio
- [ ] Anúncio com `publico_alvo=INSCRITOS_EVENTO` só é visível para inscritos aprovados naquele evento
- [ ] Performance: contexto global de anúncios faz 1 query (cache via context processor)

## Casos de uso cobertos

- Anunciar produto novo na home para todos
- Avisar inscritos do "Congresso 2026" sobre camisetas disponíveis
- Notificar lista de espera quando produto X repõe estoque
- Promoção de produto exclusivo para sócios

## Estimativa

1 dia (8 horas com Claude Code).

## Pontos de atenção

1. **Performance**: anúncios são consultados em TODA requisição via context processor. Cachear via `cache_page` ou `cache.set` por 5 minutos.
2. **Imagens responsivas**: anúncio com imagem precisa de versão mobile (campo `imagem_mobile` opcional, ou usar `object-fit: cover`).
3. **Cores em hex**: validar com regex `^#[0-9a-fA-F]{6}$` no form.
4. **E-mail em lote**: limitar a 50/minuto para não exceder limite SMTP do Gmail (500/dia). Considerar SendGrid no futuro.
5. **Lista de espera com prioridade**: usuário da lista tem 24h de prioridade quando produto volta (definido em `LISTA_ESPERA_PRIORIDADE_HORAS`). Implementação simples: durante esse período, produto só aparece para quem está na lista.
6. **HTML em e-mail**: usar template wrapper único (`templates/emails/loja/campanha.html`) que recebe `{{ corpo_html|safe }}`. Adicionar header e footer padronizados.
