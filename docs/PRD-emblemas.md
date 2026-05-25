# PRD — Sistema de Emblemas
**Plataforma Sinodal · CSMSGA**
**Versão:** 3.0 · **Data:** Maio 2026 · **Status:** Proposta

---

## Resumo Executivo

Este documento define o sistema de Emblemas da Plataforma Sinodal — premiações digitais concedidas **manualmente pela liderança** para reconhecer participantes por suas contribuições, comportamentos e características observadas durante eventos.

A inspiração vem diretamente da tradição dos acampamentos da Organização Palavra da Vida, onde prêmios como "Melhor Acampante", "Melhor Quarto" e "Mais Animado" são decididos por pessoas que observaram, conversaram e julgaram — não por um algoritmo. Essa curadoria humana é exatamente o que dá peso e significado ao reconhecimento.

**A tese central:** um emblema que alguém na liderança decidiu dar a você vale infinitamente mais do que um crachá que o sistema emitiu porque você clicou em algo 5 vezes. O esforço humano por trás da escolha é o que torna o prêmio especial.

**O que é:** um sistema de premiação gerenciado pela liderança, com ferramentas que tornam fácil **criar emblemas customizados**, **selecionar múltiplos destinatários** de forma ágil (busca, filtro por evento, seleção em massa), **revisar antes de publicar** e **notificar os premiados**. Os emblemas aparecem no perfil público do usuário e na página Explorar.

**O que não é:** um sistema automático, um ranking, ou pontuação. Nada é concedido sem que uma pessoa da liderança decida que aquele participante merece.

**Resultado esperado:** cultura de reconhecimento genuíno dentro da comunidade sinodal; participantes que se sentem vistos e valorizados pela liderança; histórico permanente de conquistas que conta a história de cada membro.

---

## Sumário

1. [Contexto e Problema](#1-contexto-e-problema)
2. [Filosofia do Sistema](#2-filosofia-do-sistema)
3. [Evidências de Engajamento](#3-evidências-de-engajamento)
4. [Objetivos e Métricas de Sucesso](#4-objetivos-e-métricas-de-sucesso)
5. [Fluxo da Liderança (Criação e Premiação)](#5-fluxo-da-liderança-criação-e-premiação)
6. [Catálogo de Emblemas Sugeridos](#6-catálogo-de-emblemas-sugeridos)
7. [Experiência do Participante](#7-experiência-do-participante)
8. [Arquitetura Técnica](#8-arquitetura-técnica)
9. [Fases de Implementação](#9-fases-de-implementação)
10. [Riscos e Mitigações](#10-riscos-e-mitigações)
11. [Fora do Escopo](#11-fora-do-escopo)

---

## 1. Contexto e Problema

### 1.1 Contexto da Plataforma

A Plataforma Sinodal gerencia eventos, inscrições, sessões plenárias e votações da CSMSGA. A liderança já tem visibilidade sobre quem participou, quem estava presente, quem se destacou. O que falta é uma **forma estruturada de formalizar e tornar público esse reconhecimento**.

Os emblemas podem ter dois escopos:

- **Vinculado a um evento** — "Melhor Acampante · CE Garanhuns 2026", concedido no contexto de um evento específico, visível no hub do evento e no perfil do membro.
- **Global (sem evento)** — "Servidor Fiel da CSMSGA", "Líder de Décadas", emblemas que reconhecem trajetória ou contribuição à comunidade como um todo, independente de qualquer evento.

### 1.2 O Problema com Sistemas Automáticos

Sistemas que concedem badges automaticamente (ex.: "você foi aprovado em 1 evento → ganha o badge Primeiro Passo") criam um problema sutil mas sério: **inflação de valor**. Quando todo mundo ganha, ninguém se sente especial. O badge vira um ruído de notificação, não um reconhecimento.

Além disso, um algoritmo não consegue capturar o que a liderança percebe ao vivo: quem ajudou a organizar sem ser obrigado, quem animou o grupo num momento difícil, quem demonstrou maturidade ao presidir uma votação acirrada.

### 1.3 A Inspiração: Palavra da Vida

Os acampamentos da Organização Palavra da Vida têm uma tradição de premiações ao final do evento: "Melhor Acampante", "Melhor Quarto", "Mais Animado", "Quem Mais Cresceu". Esses prêmios funcionam porque:

1. **São escassos** — nem todos ganham
2. **São observados** — a liderança acompanha e decide
3. **São surpreendentes** — o premiado não sabia que estava sendo notado
4. **Têm peso humano** — alguém escolheu você especificamente

O sistema de emblemas da Plataforma Sinodal segue exatamente essa lógica, com ferramentas digitais que tornam o processo prático para a liderança.

---

## 2. Filosofia do Sistema

### 2.1 Curadoria Humana como Diferencial

Cada emblema concedido representa uma **decisão humana consciente**. A liderança cria o emblema, define os critérios na descrição, observa os participantes durante o evento, e depois usa as ferramentas da plataforma para selecionar e premiá-los. O processo pode levar 10 minutos ou 10 dias — o tempo que a liderança precisar para fazer bem feito.

### 2.2 Escassez Intencional

Não existe um número mínimo ou máximo de emblemas por evento. A liderança decide quantos criar e para quantas pessoas. A recomendação é: **prefira conceder poucos emblemas que signifiquem muito a muitos que signifiquem pouco**.

### 2.3 Contexto Preservado

Emblemas com evento vinculado exibem esse contexto no perfil: "Melhor Acampante · CE Garanhuns 2026". Emblemas globais aparecem sem contexto de evento, mas com a data de concessão. Em ambos os casos, o histórico de um membro conta uma história ao longo dos anos.

### 2.4 Surpresa e Revelação

O sistema suporta um fluxo de **premiação coletiva**: a liderança prepara tudo antes (cria os emblemas, seleciona os destinatários), e publica todos de uma vez num momento especial — como numa cerimônia de encerramento, reunião de liderança, ou divulgação pós-evento.

---

## 3. Evidências de Engajamento

Pesquisas mostram que sistemas de reconhecimento em comunidades aumentam retenção em **22%** e engajamento em até **150%**. O que a literatura especificamente confirma sobre reconhecimento manual/humano:

- **Raridade** é o fator mais determinante de valor — badges que poucos têm valem mais (arXiv, 2024)
- Em comunidades religiosas, membros reconhecidos são **67% mais propensos** a dar o próximo passo de engajamento
- **Visibilidade pública** aumenta o impacto: ver o reconhecimento dos outros motiva quem ainda não foi premiado
- O momento de **surpresa da conquista** (não saber quando será premiado) mantém os níveis de engajamento mais altos por mais tempo do que recompensas previsíveis

---

## 4. Objetivos e Métricas de Sucesso

### 4.1 Objetivos

1. **Dar à liderança uma ferramenta prática** para reconhecer participantes sem burocracia
2. **Criar registro permanente e público** do histórico de conquistas de cada membro
3. **Fortalecer a cultura de reconhecimento** dentro da comunidade sinodal
4. **Aumentar o engajamento** na página Explorar e nos perfis de usuários

### 4.2 Métricas (após primeiro evento com o sistema)

| Métrica | Meta |
|---|---|
| % de participantes de um evento que receberam ao menos 1 emblema | Definido pela liderança por evento |
| Visitas à página de perfil após notificação de emblema | +80% vs. média |
| Visitas à página Explorar na semana de premiação | +60% vs. semana anterior |
| Tempo de criação de uma premiação completa (emblema + seleção + publicação) | < 10 minutos |

---

## 5. Fluxo da Liderança (Criação e Premiação)

Este é o coração do sistema. A liderança tem um **Painel de Premiações** acessível diretamente pelo menu administrativo da plataforma — independente de estar dentro ou fora de um evento.

**Navegação:** Menu principal → **Premiações** (área administrativa exclusiva para liderança)

### 5.1 Etapa 1 — Criar o Emblema

A liderança acessa **Premiações → Novo Emblema** (ou parte de um template do catálogo) e preenche:

| Campo | Descrição | Exemplo |
|---|---|---|
| **Nome** | Nome curto e memorável | "Melhor Acampante" |
| **Ícone** | Emoji ou ícone da biblioteca | 🏆 |
| **Descrição** | O que esse emblema representa | "Reconhece o participante que mais se destacou pela postura, animação e contribuição ao evento." |
| **Categoria** | Agrupamento temático | Comportamento / Liderança / Serviço / Especial |
| **Evento** | Contexto opcional — deixar vazio para emblemas globais | CE Garanhuns 2026 (ou vazio) |
| **Publicação** | Imediata ou agendada/manual | Rascunho |

A liderança pode criar vários emblemas de uma vez, todos em rascunho, antes de selecionar qualquer destinatário.

### 5.2 Etapa 2 — Selecionar Destinatários

Ao abrir um emblema em rascunho, a liderança vê a tela de seleção de destinatários:

**Ferramentas de seleção disponíveis:**

- **Busca por nome** — campo com busca instantânea (universo: inscritos no evento vinculado, ou todos os usuários da plataforma para emblemas globais)
- **Filtro por papel** — mostrar apenas Delegados, apenas Ex-Offício, etc. (disponível apenas quando há evento vinculado)
- **Filtro de presença** — mostrar apenas quem esteve presente em X% das sessões (disponível apenas quando há evento vinculado)
- **Seleção individual** — checkbox por participante
- **Seleção em massa** — "Selecionar todos os filtrados"
- **Contador em tempo real** — "12 participantes selecionados"
- **Preview dos selecionados** — chips com fotos/avatares antes de confirmar

A lista mostra: foto/avatar, nome completo, papel no evento (ou tipo de usuário para emblemas globais).

### 5.3 Etapa 3 — Revisar e Publicar

Antes de publicar, a liderança vê uma tela de confirmação:

```
┌─────────────────────────────────────────────────────┐
│  🏆 Melhor Acampante                                │
│  "Reconhece o participante que mais se destacou..." │
│                                                     │
│  Será concedido a:                                  │
│  [foto] João Silva   [foto] Maria Oliveira          │
│  [foto] Pedro Santos                                │
│                                                     │
│  3 participantes · CE Garanhuns 2026                │
│                                                     │
│  [Publicar Agora]  [Salvar Rascunho]  [Cancelar]   │
└─────────────────────────────────────────────────────┘
```

### 5.4 Publicação

Ao publicar:
1. Os registros de `EmblemaUsuario` são criados em batch
2. Cada premiado recebe uma **notificação in-app** no próximo acesso
3. Os emblemas aparecem imediatamente nos perfis públicos e na página Explorar
4. A liderança vê um resumo: "3 emblemas concedidos com sucesso"

### 5.5 Fluxo de Cerimônia (Publicação em Lote)

Para eventos que querem um momento especial de revelação:

1. Liderança cria todos os emblemas e seleciona todos os destinatários (tudo em rascunho)
2. No momento escolhido (cerimônia de encerramento, reunião de liderança), clica em **"Publicar Todos os Rascunhos"**
3. Todos os premiados recebem notificação simultaneamente
4. A liderança pode projetar a tela de perfil dos premiados ao vivo

---

## 6. Catálogo de Emblemas

O catálogo é um conjunto de **templates reutilizáveis** criados e gerenciados pela própria liderança no banco de dados — não são hardcoded no código. Isso significa que a liderança pode adicionar, editar e remover templates a qualquer momento sem necessidade de deploy.

**Fluxo de uso:** ao criar um novo emblema, a liderança pode partir de zero ou escolher um template do catálogo, que pré-preenche nome, ícone, descrição e categoria (tudo editável antes de salvar).

**Gestão do catálogo:** disponível em **Premiações → Catálogo de Templates**.

Os exemplos abaixo são **sugestões iniciais** para popular o catálogo na primeira instalação. A liderança decide quais manter, editar ou remover.

### Categoria: Comportamento e Postura

| Nome | Ícone | Descrição sugerida |
|---|---|---|
| Melhor Acampante | 🏆 | Destaque geral por postura, animação e contribuição ao evento |
| Espírito de Equipe | 🤝 | Colaboração e suporte aos colegas durante todo o evento |
| Mais Animado | 🎉 | Contagiou o grupo com energia positiva em todos os momentos |
| Líder Nato | ⭐ | Demonstrou liderança natural sem necessariamente ter cargo formal |
| Voz da Sabedoria | 🎤 | Contribuições nas discussões que elevaram o nível do debate |

### Categoria: Serviço e Dedicação

| Nome | Ícone | Descrição sugerida |
|---|---|---|
| Servente Fiel | 🛠️ | Ajudou na organização e infraestrutura além do esperado |
| Voluntário Exemplar | 🙋 | Sempre disposto a contribuir quando solicitado |
| Nos Bastidores | 🎭 | Trabalhou sem holofotes para que tudo funcionasse bem |

### Categoria: Participação Democrática

| Nome | Ícone | Descrição sugerida |
|---|---|---|
| Voz Ativa | 🗳️ | Participação consistente e qualificada nas votações e debates |
| Presidente Exemplar | ⚖️ | Conduziu sessões com imparcialidade e firmeza |
| Secretário Preciso | 📋 | Registros impecáveis e atenção ao rito processual |

### Categoria: Especiais por Evento

| Nome | Ícone | Descrição sugerida |
|---|---|---|
| Melhor Quarto | 🏠 | O quarto mais organizado e com melhor convivência |
| Veterano do CE | 🎖️ | Reconhecimento por múltiplas participações no Congresso Estadual |
| Revelação do Evento | 🌟 | Primeira participação marcada por destaque extraordinário |
| CE [Ano] | 📅 | Participou do Congresso Estadual de [Ano] — badge de memória |

---

## 7. Experiência do Participante

### 7.1 Notificação de Conquista

No próximo acesso após a premiação, o participante vê um toast no topo da tela:

> 🏆 **Você recebeu um emblema!**
> **Melhor Acampante** — CE Garanhuns 2026
> "Reconhece o participante que mais se destacou..."
> [Ver meu perfil]

### 7.2 Página de Perfil

Seção "Emblemas" exibe:
- Emblemas conquistados com ícone, nome e evento de origem
- Ao passar o mouse/tocar: descrição completa e data de concessão
- Emblemas agrupados por evento (linha do tempo visual)

### 7.3 Página Explorar

No card de cada usuário: até 3 emblemas mais recentes exibidos como ícones pequenos abaixo do nome.

No modal de perfil: lista completa de emblemas com evento de origem.

### 7.4 Hub do Evento

Na barra lateral do participante: emblemas recebidos naquele evento específico em destaque.

---

## 8. Arquitetura Técnica

### 8.1 Modelos

```python
# apps/emblemas/models.py

class CatalogoEmblema(models.Model):
    """Template reutilizável gerenciado pela liderança no banco."""
    nome        = CharField(max_length=60)
    icone       = CharField(max_length=10)        # emoji
    descricao   = CharField(max_length=200)
    categoria   = CharField(max_length=30, choices=_c.EMBLEMA_CATEGORIA_CHOICES)
    criado_por  = FK(User, related_name='catalogo_emblemas_criados')
    criado_em   = DateTimeField(auto_now_add=True)
    ativo       = BooleanField(default=True)

    class Meta:
        ordering = ['categoria', 'nome']


class Emblema(models.Model):
    # Aliases para core/constants.py
    STATUS_RASCUNHO  = _c.EMBLEMA_RASCUNHO
    STATUS_PUBLICADO = _c.EMBLEMA_PUBLICADO
    STATUS_CHOICES   = _c.EMBLEMA_STATUS_CHOICES

    # evento é OPCIONAL — null = emblema global (não vinculado a evento)
    evento      = FK(Evento, related_name='emblemas', null=True, blank=True,
                     on_delete=SET_NULL)
    nome        = CharField(max_length=60)
    icone       = CharField(max_length=10)        # emoji
    descricao   = CharField(max_length=200)
    categoria   = CharField(max_length=30, choices=_c.EMBLEMA_CATEGORIA_CHOICES)
    status      = PositiveSmallIntegerField(choices=STATUS_CHOICES,
                                            default=_c.EMBLEMA_RASCUNHO)
    criado_por  = FK(User, related_name='emblemas_criados')
    criado_em   = DateTimeField(auto_now_add=True)
    publicado_em = DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-criado_em']


class EmblemaUsuario(models.Model):
    emblema        = FK(Emblema, related_name='conquistas')
    usuario        = FK(User, related_name='emblemas')
    concedido_por  = FK(User, related_name='emblemas_concedidos')
    concedido_em   = DateTimeField(auto_now_add=True)
    notificado     = BooleanField(default=False)

    class Meta:
        unique_together = [('emblema', 'usuario')]
        indexes = [Index(fields=['usuario_id', 'concedido_em'])]
```

**Constantes em `core/constants.py` (prefixo `EMBLEMA_`):**

```python
EMBLEMA_RASCUNHO  = 1
EMBLEMA_PUBLICADO = 2
EMBLEMA_STATUS_CHOICES = [(1, 'Rascunho'), (2, 'Publicado')]

EMBLEMA_CAT_COMPORTAMENTO = 'comportamento'
EMBLEMA_CAT_SERVICO       = 'servico'
EMBLEMA_CAT_DEMOCRATICO   = 'democratico'
EMBLEMA_CAT_ESPECIAL      = 'especial'

EMBLEMA_CATEGORIA_CHOICES = [
    (EMBLEMA_CAT_COMPORTAMENTO, 'Comportamento e Postura'),
    (EMBLEMA_CAT_SERVICO,       'Serviço e Dedicação'),
    (EMBLEMA_CAT_DEMOCRATICO,   'Participação Democrática'),
    (EMBLEMA_CAT_ESPECIAL,      'Especial'),
]
```

### 8.2 Serviço de Concessão em Lote

```python
# apps/emblemas/services.py

def publicar_emblema(emblema, destinatarios_ids, concedido_por):
    """
    Recebe um Emblema em rascunho e uma lista de user IDs.
    Cria EmblemaUsuario em batch e marca o emblema como publicado.
    Retorna (criados, ja_tinham).
    """
    from django.utils import timezone

    ja_tinham = set(
        EmblemaUsuario.objects.filter(
            emblema=emblema, usuario_id__in=destinatarios_ids
        ).values_list('usuario_id', flat=True)
    )

    novos = [
        EmblemaUsuario(emblema=emblema, usuario_id=uid, concedido_por=concedido_por)
        for uid in destinatarios_ids
        if uid not in ja_tinham
    ]
    EmblemaUsuario.objects.bulk_create(novos)

    emblema.status = Emblema.STATUS_PUBLICADO
    emblema.publicado_em = timezone.now()
    emblema.save(update_fields=['status', 'publicado_em'])

    return len(novos), len(ja_tinham)


def publicar_todos_rascunhos(concedido_por, evento=None):
    """
    Publica todos os emblemas em rascunho.
    Se evento for passado, filtra apenas os daquele evento.
    Se evento=None, publica todos os rascunhos globais (sem evento).
    """
    qs = Emblema.objects.filter(status=Emblema.STATUS_RASCUNHO)
    if evento is not None:
        qs = qs.filter(evento=evento)
    else:
        qs = qs.filter(evento__isnull=True)

    total = 0
    for emblema in qs:
        ids = list(emblema.conquistas.values_list('usuario_id', flat=True))
        criados, _ = publicar_emblema(emblema, ids, concedido_por)
        total += criados
    return total
```

### 8.3 URLs do Módulo

O módulo `apps/emblemas` tem suas próprias URLs montadas em `core/urls.py`, **não** aninhadas em `apps/eventos`.

```
# Área administrativa — acessível por liderança

GET   /premiacoes/                              → painel: lista todos os emblemas
GET   /premiacoes/novo/                         → formulário criar emblema
POST  /premiacoes/novo/                         → salvar novo emblema
GET   /premiacoes/<id>/editar/                  → editar emblema em rascunho
GET   /premiacoes/<id>/selecionar/              → seleção de destinatários
POST  /premiacoes/<id>/publicar/                → publica emblema (recebe user_ids[])
POST  /premiacoes/publicar-rascunhos/           → publica todos os rascunhos (global)
POST  /premiacoes/publicar-rascunhos/<slug>/    → publica rascunhos de um evento

# Catálogo de templates
GET   /premiacoes/catalogo/                     → listar templates do catálogo
GET   /premiacoes/catalogo/novo/                → criar template
POST  /premiacoes/catalogo/novo/                → salvar template
GET   /premiacoes/catalogo/<id>/editar/         → editar template
POST  /premiacoes/catalogo/<id>/excluir/        → remover template

# Leitura pública (notificações)
POST  /premiacoes/notificacao/<conquista_id>/marcar-lida/   → marca notificado=True
```

**Navegação:** o link "Premiações" aparece no menu administrativo apenas para usuários com `tipo == LIDERANCA`.

### 8.4 Notificações In-App

A tabela `EmblemaUsuario` tem `notificado = BooleanField(default=False)`. Um **context processor** leve injeta as conquistas pendentes em toda resposta autenticada:

```python
# apps/emblemas/context_processors.py
def emblemas_pendentes(request):
    if not request.user.is_authenticated:
        return {}
    pendentes = (
        EmblemaUsuario.objects.filter(usuario=request.user, notificado=False)
        .select_related('emblema__evento')[:3]
    )
    return {'emblemas_pendentes': pendentes}
```

O `base.html` renderiza o toast se `emblemas_pendentes` não estiver vazio. Após exibir, um POST HTMX silencioso marca `notificado=True` em cada conquista.

### 8.5 Estrutura do App

```
apps/emblemas/
  __init__.py
  models.py              # Emblema, EmblemaUsuario, CatalogoEmblema
  services.py            # publicar_emblema(), publicar_todos_rascunhos()
  views.py               # painel, criação, seleção, publicação, catálogo
  context_processors.py  # inject emblemas_pendentes em todo request
  urls.py                # montado em core/urls.py com prefixo /premiacoes/
  admin.py
  apps.py
  migrations/
```

Registrar em `INSTALLED_APPS` e em `TEMPLATES[...]['OPTIONS']['context_processors']`.

---

## 9. Fases de Implementação

### Fase 1 — Fundação (Sprint 1, ~1 semana)

- [ ] Criar app `apps/emblemas/` com modelos `Emblema`, `EmblemaUsuario`, `CatalogoEmblema`
- [ ] Adicionar constantes em `core/constants.py` (prefixo `EMBLEMA_`)
- [ ] Serviço `publicar_emblema()` com `bulk_create`
- [ ] Painel administrativo: listar, criar e editar emblemas (com campo evento opcional)
- [ ] Exibir emblemas no perfil público do usuário

### Fase 2 — Seleção de Destinatários (Sprint 2, ~1 semana)

- [ ] View de seleção: busca por nome; filtros de papel/presença condicionados à existência de evento vinculado
- [ ] Checkboxes individuais + "Selecionar todos os filtrados"
- [ ] Contador em tempo real de selecionados (JS leve)
- [ ] Tela de revisão antes de publicar
- [ ] Publicação em lote: por evento e global (rascunhos sem evento)

### Fase 3 — Catálogo e UX do Participante (Sprint 3, ~1 semana)

- [ ] CRUD do `CatalogoEmblema` (área **Premiações → Catálogo**)
- [ ] Ao criar emblema: opção "Usar template do catálogo" que pré-preenche o formulário
- [ ] Context processor + toast de notificação in-app com marcação de lida
- [ ] Exibir emblemas no modal do Explorar e ícones no card
- [ ] Agrupamento por evento na página de perfil (linha do tempo)

### Fase 4 — Refinamento

- [ ] Histórico de premiações por evento no painel da liderança
- [ ] Analytics: quantos emblemas concedidos, quais usuários receberam mais

---

## 10. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Liderança não usa por ser trabalhoso | Média | Alto | UX deve ser < 10 min do zero à publicação; testar com usuário real antes de lançar |
| Favoritismo percebido pela comunidade | Média | Médio | Descrição clara dos critérios; histórico público de quem concedeu |
| Emblemas criados mas nunca publicados | Alta | Baixo | Lembrete no painel: "X emblemas em rascunho neste evento" |
| Participante não vê a notificação | Média | Baixo | Toast persiste até ser marcado como lido; também aparece na página de perfil |
| Emblema global sem contexto claro | Baixa | Médio | Campo descrição obrigatório; liderança define os critérios explicitamente na criação |

---

## 11. Fora do Escopo

- **Qualquer concessão automática** — 100% manual, 100% humano
- **Ranking ou pontuação** — nenhuma classificação por número de emblemas
- **Emblemas expiráveis** — permanentes após concedidos
- **Votação da comunidade para escolher premiados** — decisão exclusiva da liderança
- **Notificações por e-mail ou push** — apenas in-app no MVP

---

## Referências de Pesquisa

- [Badge Rarity Tiers Design Guide — EmoteShowcase](https://emoteshowcase.com/blog/badge-rarity-tiers/)
- [Badge System Analysis and Design — arXiv](https://arxiv.org/pdf/1607.00537)
- [Gamification in Religious Communities — FasterCapital](https://fastercapital.com/content/Religious-gamification--The-Role-of-Religious-Gamification-in-Building-a-Successful-Business.html)
- [Psychology of Gamification — CrustLab](https://crustlab.com/blog/psychology-of-gamification/)
- [Gamification Statistics 2026 — Visu Network](https://visu.network/blog/gamification-statistics/)
- [Digital Badges and Intrinsic Motivation — Frontiers in Education](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2024.1429452/full)
