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

## Estrutura de apps

| App | Responsabilidade |
|---|---|
| `core` | Constantes globais, settings, URLs raiz |
| `usuarios` | Model User customizado |
| `eventos` | Eventos, inscrições, campos dinâmicos |
| `sessoes` | Sessões, presença, votações, mesa diretora, logs |
| `hub` | Portal do participante (view pública por evento) |
