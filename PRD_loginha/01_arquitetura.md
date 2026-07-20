# Etapa 01 — Arquitetura e fundação técnica

## Objetivo

Criar o esqueleto do app `apps.loja` com configuração de URLs, settings, context processor de carrinho e handler de pagamento. Ao final desta etapa, o app existe vazio, é importável, e está pronto para receber modelos.

## Pré-requisitos

- Nenhum (primeira etapa)
- App `apps.pagamentos` já existente (já implementado)

## Decisões técnicas

### Nome do app
`apps.loja`

### Models divididos ou um arquivo só?

**Recomendação:** começar com `models.py` único. Quando passar de ~600 linhas, dividir em pacote `models/`.

### Carrinho: sessão vs banco?

**Híbrido:**
- Usuário **anônimo**: carrinho na sessão (`request.session['carrinho']`)
- Usuário **logado**: carrinho persistido no banco (`Carrinho` model)
- No login, faz **merge** do carrinho de sessão para o banco

Justificativa: usuário pode comprar sem cadastro até o checkout, e o carrinho não se perde se ele fechar o navegador depois de logar.

### Estoque: como evitar overselling?

- Decremento de estoque sob `transaction.atomic` + `select_for_update()` no momento da criação do pedido
- Reserva temporária NO momento do checkout (não no carrinho) — duração de **15 minutos**
- Após 15 minutos sem pagamento confirmado, a reserva expira e o estoque volta

### Pagamento

- Reutiliza `apps.pagamentos`
- `order_nsu` da loja: `pedido-<id>`
- Handler registrado em `apps/loja/handlers.py` com `@register_payment_handler('pedido')`
- Importado no `LojaConfig.ready()`

## Estrutura de diretórios a criar

```
apps/loja/
├── __init__.py
├── apps.py
├── admin.py                      # vazio inicialmente
├── handlers.py                   # @register_payment_handler('pedido') placeholder
├── models.py                     # vazio inicialmente
├── forms.py                      # vazio inicialmente
├── urls.py                       # urlpatterns = []
├── views/
│   ├── __init__.py
│   └── catalogo.py               # def index(request): ...
├── services/
│   └── __init__.py
├── templatetags/
│   ├── __init__.py
│   └── loja.py                   # filtro `moeda`
├── context_processors.py         # carrinho_resumo(request)
├── management/
│   ├── __init__.py
│   └── commands/
│       └── __init__.py
└── migrations/
    └── __init__.py

templates/loja/
└── base.html                     # extends 'base.html', com sidebar/header
```

## Configurações a alterar

### `core/settings.py`

1. Adicionar `'apps.loja'` em `INSTALLED_APPS` (após `apps.pagamentos`)
2. Adicionar context processor:
   ```python
   TEMPLATES[0]['OPTIONS']['context_processors'].append(
       'apps.loja.context_processors.carrinho_resumo'
   )
   ```

### `core/urls.py`

Adicionar:
```python
path('loja/', include('apps.loja.urls')),
```

### `core/constants.py`

Adicionar bloco (vazio por enquanto, será preenchido nas próximas etapas):
```python
# ============================================================
# Loja
# ============================================================
```

## Arquivos iniciais

### `apps/loja/apps.py`

```python
from django.apps import AppConfig


class LojaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.loja'
    verbose_name = 'Loja'

    def ready(self):
        from . import handlers  # noqa: F401
```

### `apps/loja/handlers.py`

```python
"""Handlers de pagamento da loja.

Será preenchido na Etapa 04. Por enquanto, registro vazio.
"""
import logging

from apps.pagamentos.handlers import register_payment_handler

logger = logging.getLogger(__name__)


@register_payment_handler('pedido')
def confirmar_pedido_pago(*, order_nsu, transacao, payload):
    # Implementação real na Etapa 04
    logger.info('loja.handler.placeholder', extra={'order_nsu': order_nsu})
```

### `apps/loja/urls.py`

```python
from django.urls import path

from .views import catalogo

app_name = 'loja'

urlpatterns = [
    path('', catalogo.index, name='index'),
]
```

### `apps/loja/views/catalogo.py`

```python
from django.shortcuts import render


def index(request):
    return render(request, 'loja/index.html', {})
```

### `apps/loja/context_processors.py`

```python
def carrinho_resumo(request):
    """Disponibiliza um resumo do carrinho em todas as templates.

    Será preenchido na Etapa 03. Por enquanto retorna vazio.
    """
    return {
        'carrinho_qtd': 0,
        'carrinho_total': 0,
    }
```

### `apps/loja/templatetags/loja.py`

```python
from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def moeda(valor):
    """Formata número em moeda brasileira: 1234.5 → R$ 1.234,50."""
    if valor is None:
        return 'R$ 0,00'
    try:
        d = Decimal(str(valor))
    except (TypeError, ValueError):
        return 'R$ 0,00'
    inteiro, _, centavos = f'{d:.2f}'.partition('.')
    # Insere separador de milhar
    inteiro_com_pontos = ''
    for i, c in enumerate(reversed(inteiro.lstrip('-'))):
        if i and i % 3 == 0:
            inteiro_com_pontos = '.' + inteiro_com_pontos
        inteiro_com_pontos = c + inteiro_com_pontos
    sinal = '-' if inteiro.startswith('-') else ''
    return f'R$ {sinal}{inteiro_com_pontos},{centavos}'


@register.filter
def centavos_para_reais(valor_centavos):
    if not valor_centavos:
        return 'R$ 0,00'
    return moeda(Decimal(valor_centavos) / 100)
```

### `templates/loja/base.html`

```django
{% extends 'base.html' %}
{% load loja %}

{% block title %}Loja{% endblock %}

{% block content %}
<div class="max-w-6xl mx-auto px-4 py-6">
  {% block loja_content %}{% endblock %}
</div>
{% endblock %}
```

### `templates/loja/index.html`

```django
{% extends 'loja/base.html' %}

{% block loja_content %}
<h1 class="text-2xl font-bold">Loja</h1>
<p class="text-gray-600">Em construção.</p>
{% endblock %}
```

## Critérios de aceite

- [ ] Diretório `apps/loja/` criado com todos os arquivos acima
- [ ] `'apps.loja'` aparece em `INSTALLED_APPS`
- [ ] Context processor registrado em `TEMPLATES`
- [ ] URL `loja/` registrada em `core/urls.py`
- [ ] Acessar `http://localhost:8000/loja/` retorna 200 com o título "Loja"
- [ ] `python manage.py check` retorna 0 warnings novos
- [ ] `python manage.py makemigrations` retorna "No changes detected" (sem models ainda)
- [ ] Comando `python manage.py shell` permite `from apps.loja.handlers import confirmar_pedido_pago` sem erro
- [ ] `apps.pagamentos.handlers.get_registered_prefixes()` retorna `['inscricao', 'pedido']`
- [ ] Template tag `{% load loja %}{{ 1234.5|moeda }}` renderiza `R$ 1.234,50`

## Casos de uso cobertos

Nenhum diretamente. Esta etapa é fundação.

## Estimativa

0,5 dia (4 horas com Claude Code).
