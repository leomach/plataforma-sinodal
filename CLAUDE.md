# Plataforma Sinodal — Guia para Claude Code

## Convenções de código

### Constantes e choices

Todas as constantes reutilizáveis (status, tipos, papéis, cargos, choices de `models.IntegerField`) devem ser definidas em **`core/constants.py`**, nunca diretamente nos modelos.

- Use prefixo do domínio: `SESSAO_`, `VOTACAO_`, `CARGO_`, `LOG_`, etc.
- Nos modelos, crie aliases de classe apontando para as constantes:

```python
from core import constants as _c

class Sessao(models.Model):
    STATUS_ABERTA = _c.SESSAO_ABERTA
    STATUS_CHOICES = _c.SESSAO_STATUS_CHOICES
```

Isso preserva a API `Sessao.STATUS_ABERTA` e permite importar de `core.constants` em qualquer app sem acoplar a `apps.sessoes.models`.

## Stack

- Django 5.1+, PostgreSQL, Poetry
- HTMX para interações sem page-reload (polling, swaps parciais)
- Tailwind CSS (via CDN/Play CDN) para estilização
- `html5-qrcode` (CDN) para leitura de QR Code

## Mobile / responsividade

### Zoom em inputs no iOS Safari

iOS Safari dá zoom automático em qualquer `input`, `select` ou `textarea` com `font-size < 16px`. A correção global está em `templates/base.html` dentro do `@layer base`:

```html
<style>
    @media (max-width: 767px) {
        input, select, textarea { font-size: 16px !important; }
    }
</style>
```

A regra fica em um `<style>` normal (não dentro do bloco `text/tailwindcss`), com `!important`, porque classes utilitárias Tailwind como `text-sm` têm prioridade maior que `@layer base` e sobrescreveriam sem o `!important`. Aplica apenas em telas móveis, preservando o tamanho visual no desktop. **Nunca use `maximum-scale=1` no viewport** — isso desabilita zoom de acessibilidade do usuário.

## Estrutura de apps

| App | Responsabilidade |
|---|---|
| `core` | Constantes globais, settings, URLs raiz |
| `usuarios` | Model User customizado |
| `eventos` | Eventos, inscrições, campos dinâmicos |
| `sessoes` | Sessões, presença, votações, mesa diretora, logs |
| `hub` | Portal do participante (view pública por evento) |
