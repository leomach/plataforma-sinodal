# PRD — Módulo de Sessões (Plataforma Sinodal)

**Versão:** 1.0  
**Data:** 2026-05-18  
**Autor:** Leandro Machado  
**Status:** Aprovado para implementação

---

## 1. Visão Geral

O módulo de Sessões é o coração operacional de um congresso ou Concílio Extraordinário (CE) na Plataforma Sinodal. Ele transforma o evento em um plenário digital com controle de presença por QR Code, votações em tempo real e geração automatizada da linha do tempo para composição da ata oficial.

### 1.1 Problema a Resolver

Hoje a plataforma possui um model `Sessao` rudimentar (nome + data_hora) e um model `Presenca` (booleano simples). Faltam: ciclo de vida da sessão, controle de quórum, leitor QR de presença toggle, votações vinculadas à sessão ativa, e a linha do tempo auditável necessária para a ata formal exigida pelo GTSI.

### 1.2 Objetivos

| Objetivo | Métrica de Sucesso |
|---|---|
| Controle de presença por QR sem hardware dedicado | 0 leitores físicos necessários |
| Quórum calculado automaticamente | Exibição em tempo real no painel da liderança |
| Votações com resultado em tempo real | Resultado disponível em < 5s após último voto |
| Geração de linha do tempo auditável | Cada sessão produz log com timestamps precisos |
| Conformidade com exigências do GTSI | Sessão de Verificação de Poderes identificada |

### 1.3 Escopo

**Dentro do escopo:**
- Ciclo de vida de uma Sessão (status)
- Marcação de Sessão de Verificação de Poderes
- Geração e exibição de QR Code do delegado
- Leitor de QR por câmera (mobile-first)
- Lógica de toggle entrada/saída
- Cálculo de quórum em tempo real
- Criação e condução de votações
- Voto de Minerva (desempate)
- Linha do tempo (Event Log) com entradas automáticas e manuais
- Exportação da linha do tempo como texto para ata

**Fora do escopo (fase futura):**
- Transmissão ao vivo / streaming
- Integração com sistema de atas externas (Word, PDF automático)
- Controle de microfone / fila de oradores
- Notificações push para delegados

---

## 2. Personas e Casos de Uso Principais

### 2.1 Personas

| Persona | Papel no Sistema | Necessidade Principal |
|---|---|---|
| **Secretário / Liderança** | `tipo=LIDERANCA` | Gerenciar sessões, criar votações, inserir registros manuais na linha do tempo |
| **Voluntário de Recepção** | Usuário com permissão especial de leitor | Escanear QR Codes na porta do plenário |
| **Delegado Efetivo / Ex-Officio** | `papel_evento IN (1, 2)` | Visualizar QR próprio, votar em propostas, acompanhar agenda |
| **Correspondente / Visitante** | `papel_evento IN (3, 4)` | Visualizar sessões e votações (somente leitura) |

### 2.2 Jornadas de Uso Críticas

#### Jornada A — Abertura de Sessão
```
Liderança acessa painel da sessão →
Inicia "Chamada" (presença sendo coletada) →
Voluntários leem QR na porta →
Quórum atingido → sistema exibe alerta verde →
Liderança altera status para "Aberta" →
Log automático registrado com hora e quórum
```

#### Jornada B — Votação
```
Liderança cria Nova Votação na sessão ativa →
Delegados recebem votação no hub →
Delegados votam (A Favor / Contra / Abster-se) →
Sistema exibe resultado em tempo real →
[Se empate] Liderança registra Voto de Minerva →
Resultado final registrado no Event Log
```

#### Jornada C — Registro de Presença por QR
```
Delegado abre Hub no celular →
QR Code aparece no card de credencial →
Voluntário aponta câmera do celular (Leitor de Presença) →
1ª leitura: presente=True + log "entrou no plenário" + flash verde →
2ª leitura: presente=False + log "retirou-se do plenário" + flash amarelo
```

---

## 3. Requisitos Funcionais Detalhados

### RF01 — Ciclo de Vida da Sessão

A sessão possui quatro status sequenciais:

| Status | Valor | Descrição | Transição Permitida |
|---|---|---|---|
| `EM_BREVE` | 1 | Sessão agendada, ainda não iniciada | → CHAMADA |
| `CHAMADA` | 2 | Chamada de presença em andamento | → ABERTA, → EM_BREVE |
| `ABERTA` | 3 | Sessão oficialmente em curso | → ENCERRADA |
| `ENCERRADA` | 4 | Sessão finalizada | (terminal) |

**Regras de negócio:**
- Apenas uma sessão por evento pode estar no status `ABERTA` ou `CHAMADA` simultaneamente.
- A transição para `ABERTA` deve registrar automaticamente no Event Log: `"HH:MM — Sessão [nome] aberta com X delegados presentes (Quórum [atingido|não atingido])."`.
- A transição para `ENCERRADA` registra: `"HH:MM — Sessão [nome] encerrada."`.
- Apenas usuários com `tipo=LIDERANCA` podem alterar o status.

### RF02 — Sessão de Verificação de Poderes

- Campo booleano `is_verificacao_poderes` na Sessão.
- Apenas uma sessão por evento pode ter `is_verificacao_poderes=True`.
- O sistema deve exibir um badge distinto (ex: "Verificação de Poderes") na listagem e no painel.
- Regra de negócio: esta sessão deve obrigatoriamente ser a de `data_hora` mais antiga do evento (validação no save ou form).

### RF03 — QR Code do Delegado

- O QR Code é gerado automaticamente quando `Inscricao.status` passa para `STATUS_APROVADO` E `Inscricao.papel_evento IN (DELEGADO, EX_OFFICIO)`.
- O conteúdo codificado é um token único e não-sequencial baseado no UUID da inscrição (não o ID numérico) para evitar enumeração.
- O QR Code é renderizado inline no Hub do delegado como imagem SVG (sem depender de serviços externos em runtime).
- A liderança pode regenerar o QR Code de um delegado individualmente (invalida o anterior).
- O token tem formato: `SINODAL-{uuid4_hex}` para facilitar validação server-side.

### RF04 — Leitor de Presença (Câmera Mobile)

- Página acessível apenas por usuários com `tipo=LIDERANCA` ou com permissão `pode_ler_presenca`.
- URL: `/hub/<slug>/sessao/<sessao_id>/leitor/`
- Utiliza biblioteca `html5-qrcode` (carregada via CDN ou bundled).
- Exibe qual sessão está ativa e contagem de presentes em tempo real.
- Após leitura bem-sucedida, exibe feedback visual imediato (verde = entrada, amarelo = saída) por 2 segundos antes de voltar ao modo de leitura.
- Envia POST via AJAX para endpoint de toggle; não recarrega a página.
- Fallback de entrada manual: campo de texto para digitar o token caso a câmera falhe.

### RF05 — Toggle Entrada/Saída

Endpoint: `POST /hub/<slug>/sessao/<sessao_id>/presenca/toggle/`

**Lógica:**
```
token recebido → busca CredencialToken onde token=token
→ busca Inscricao vinculada
→ verifica se inscricao.status == APROVADO
→ busca ou cria Presenca(sessao=sessao_ativa, inscricao=inscricao)
→ se presente=False (ou inexistente): presente=True + log "entrou"
→ se presente=True: presente=False + log "retirou-se"
→ retorna JSON {status, nome_delegado, presente, quorum_info}
```

**Restrições:**
- Só funciona se a sessão estiver com status `CHAMADA` ou `ABERTA`.
- Retorna erro 400 se token inválido ou sessão não está aceitando presenças.

### RF06 — Cálculo de Quórum

- **Delegação esperada:** total de `Inscricao` com `status=APROVADO` e `papel_evento IN (DELEGADO, EX_OFFICIO)` para o evento.
- **Presentes:** total de `Presenca` com `presente=True` para a sessão atual.
- **Quórum legal:** `presentes > delegacao_esperada / 2` (maioria simples, mais da metade).
- O status do quórum é exibido:
  - No painel da liderança (badge verde "Quórum Atingido" ou vermelho "Sem Quórum").
  - No leitor de presença em tempo real.
- Quando o quórum é atingido pela primeira vez na sessão, gera log automático: `"HH:MM — Quórum legal atingido: X de Y delegados presentes."`.

### RF07 — Votações

**Model `Votacao`:**
- Vinculada a uma `Sessao`.
- Status: `ABERTA`, `ENCERRADA`, `EMPATADA_AGUARDANDO_MINERVA`.
- Apenas uma votação pode estar `ABERTA` por sessão por vez.

**Criação:**
- Liderança informa apenas o Título/Proposta.
- Votação criada com status `ABERTA`.
- Log automático: `"HH:MM — Votação aberta: '[titulo]'."`.

**Votação pelo Delegado:**
- Aparece no Hub do delegado quando status=`ABERTA`.
- Três botões: "A Favor", "Contra", "Abster-se".
- Cada delegado (papel DELEGADO ou EX_OFFICIO) vota uma única vez (unique_together: votacao + inscricao).
- A contagem é exibida em tempo real no painel da liderança via polling HTMX (a cada 3s).

**Encerramento:**
- Liderança encerra a votação manualmente.
- Se `votos_favor == votos_contra`: status → `EMPATADA_AGUARDANDO_MINERVA`.
  - Liderança registra o Voto de Minerva (A Favor ou Contra).
  - Log: `"HH:MM — Voto de Minerva registrado por [nome]: [A Favor|Contra]."`.
- Resultado final: log `"HH:MM — Votação '[titulo]' encerrada: X a favor, Y contra, Z abstenções. [Aprovada|Rejeitada]."`.

### RF08 — Linha do Tempo (Event Log)

**Entradas automáticas geradas pelo sistema:**
| Gatilho | Template de Log |
|---|---|
| Sessão → ABERTA | `"Sessão [nome] aberta. Presentes: X delegados (Quórum [atingido\|não atingido])."` |
| Sessão → ENCERRADA | `"Sessão [nome] encerrada."` |
| Quórum atingido | `"Quórum legal atingido: X de Y delegados."` |
| Delegado entra | `"Delegado [nome completo] entrou no plenário."` |
| Delegado sai | `"Delegado [nome completo] retirou-se do plenário."` |
| Votação aberta | `"Votação aberta: '[titulo]'."` |
| Votação encerrada | `"Votação '[titulo]' encerrada: X a favor, Y contra, Z abstenções. [Aprovada\|Rejeitada]."` |
| Voto de Minerva | `"Voto de Minerva por [nome]: [A Favor\|Contra]. Resultado final: [Aprovada\|Rejeitada]."` |

**Entradas manuais (pelo Secretário):**
- Campo de texto livre + botão "Adicionar Registro".
- Exemplo: `"Oração feita pelo Rev. Carlos Mendes."`.
- Identificado por `tipo=MANUAL` e `usuario` de quem inseriu.

**Visualização:**
- Exibida cronologicamente na página da sessão (mais recente no topo).
- Badge de tipo (automático vs manual) para distinguir visualmente.
- Exportação como texto plano formatado para colagem em documento de ata.

---

## 4. Requisitos Não-Funcionais

| Requisito | Especificação |
|---|---|
| **Performance** | Toggle de presença < 500ms (P95). Atualização de quórum em tempo real sem WebSockets (HTMX polling cada 3s é aceitável). |
| **Segurança** | Tokens QR Code são UUID v4 hex (128 bits de entropia). Endpoint de toggle valida CSRF + autenticação. Não expõe ID numérico de inscrição. |
| **Mobile-first** | Leitor de presença e Hub do delegado devem funcionar em telas 375px+. |
| **Offline resilience** | QR Code renderizado inline no Hub (SVG), não depende de chamada externa em tempo de exibição. |
| **Auditabilidade** | Toda entrada no Event Log tem timestamp imutável (auto_now_add). Entradas automáticas não podem ser deletadas pela interface. Apenas entradas manuais podem ser excluídas pela liderança. |
| **Modularidade** | O módulo de sessões deve ser isolado em um novo app Django `apps.sessoes` para não inflar o `apps.hub`. O hub passa a consumir dados do app sessoes via FK/importação direta. |

---

## 5. Arquitetura Técnica

### 5.1 Novo App: `apps.sessoes`

```
apps/sessoes/
├── __init__.py
├── models.py          # Sessao (estendida), CredencialQRCode, Votacao, VotoParticipante, EventoLog
├── views/
│   ├── __init__.py
│   ├── painel.py      # Painel da liderança (gerenciar sessão, votações, log)
│   ├── leitor.py      # Leitor QR de presença
│   ├── presenca.py    # Endpoint toggle presença
│   ├── votacao.py     # Criar, votar, encerrar, minerva
│   └── log.py         # Adicionar registro manual, exportar log
├── forms.py           # SessaoForm, VotacaoForm, EventoLogManualForm
├── services/
│   ├── __init__.py
│   ├── qrcode.py      # Geração e invalidação de tokens QR
│   ├── quorum.py      # Cálculo de quórum
│   └── eventlog.py    # Fábrica de entradas automáticas no log
├── urls.py
├── admin.py
├── signals.py         # Gerar QR ao aprovar inscrição; log automático ao mudar status
├── apps.py
└── migrations/
```

### 5.2 Mudanças no App Existente `apps.hub`

- O model `Sessao` e `Presenca` existentes em `apps/hub/models.py` serão **migrados** para `apps/sessoes/models.py`.
- `apps/hub` passa a importar de `apps.sessoes` para manter compatibilidade.
- O template `hub/index.html` exibe dados vindos do contexto enriquecido pela sessão ativa.

### 5.3 Modelo de Dados

#### Model: `Sessao` (substitui o existente)

```python
class Sessao(models.Model):
    STATUS_EM_BREVE = 1
    STATUS_CHAMADA = 2
    STATUS_ABERTA = 3
    STATUS_ENCERRADA = 4

    STATUS_CHOICES = [
        (STATUS_EM_BREVE, "Em Breve"),
        (STATUS_CHAMADA, "Chamada"),
        (STATUS_ABERTA, "Aberta"),
        (STATUS_ENCERRADA, "Encerrada"),
    ]

    evento = models.ForeignKey("eventos.Evento", on_delete=models.CASCADE, related_name="sessoes")
    nome = models.CharField(max_length=200)
    data_hora = models.DateTimeField()
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=STATUS_EM_BREVE)
    is_verificacao_poderes = models.BooleanField(default=False)

    class Meta:
        ordering = ["data_hora"]
        constraints = [
            # Apenas uma sessão ativa por evento (aplicado via clean())
        ]
```

#### Model: `CredencialQRCode`

```python
class CredencialQRCode(models.Model):
    inscricao = models.OneToOneField("eventos.Inscricao", on_delete=models.CASCADE, related_name="qr_code")
    token = models.CharField(max_length=64, unique=True, db_index=True)
    gerado_em = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)

    def gerar_token(self):
        import uuid
        return f"SINODAL-{uuid.uuid4().hex}"
```

#### Model: `Votacao`

```python
class Votacao(models.Model):
    STATUS_ABERTA = 1
    STATUS_EMPATADA = 2
    STATUS_ENCERRADA = 3

    STATUS_CHOICES = [
        (STATUS_ABERTA, "Aberta"),
        (STATUS_EMPATADA, "Aguardando Voto de Minerva"),
        (STATUS_ENCERRADA, "Encerrada"),
    ]

    RESULTADO_APROVADA = 1
    RESULTADO_REJEITADA = 2

    sessao = models.ForeignKey(Sessao, on_delete=models.CASCADE, related_name="votacoes")
    titulo = models.CharField(max_length=500)
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=STATUS_ABERTA)
    resultado = models.PositiveSmallIntegerField(choices=[(1, "Aprovada"), (2, "Rejeitada")], null=True, blank=True)
    voto_minerva_favor = models.BooleanField(null=True, blank=True)  # True=Favor, False=Contra
    minerva_por = models.ForeignKey("usuarios.User", null=True, blank=True, on_delete=models.SET_NULL)
    criada_em = models.DateTimeField(auto_now_add=True)
    encerrada_em = models.DateTimeField(null=True, blank=True)
```

#### Model: `VotoParticipante`

```python
class VotoParticipante(models.Model):
    VOTO_FAVOR = 1
    VOTO_CONTRA = 2
    VOTO_ABSTER = 3

    VOTO_CHOICES = [
        (VOTO_FAVOR, "A Favor"),
        (VOTO_CONTRA, "Contra"),
        (VOTO_ABSTER, "Abster-se"),
    ]

    votacao = models.ForeignKey(Votacao, on_delete=models.CASCADE, related_name="votos")
    inscricao = models.ForeignKey("eventos.Inscricao", on_delete=models.CASCADE)
    voto = models.PositiveSmallIntegerField(choices=VOTO_CHOICES)
    votado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("votacao", "inscricao")]
```

#### Model: `EventoLog`

```python
class EventoLog(models.Model):
    TIPO_AUTO = 1
    TIPO_MANUAL = 2

    TIPO_CHOICES = [
        (TIPO_AUTO, "Automático"),
        (TIPO_MANUAL, "Manual"),
    ]

    sessao = models.ForeignKey(Sessao, on_delete=models.CASCADE, related_name="logs")
    tipo = models.PositiveSmallIntegerField(choices=TIPO_CHOICES, default=TIPO_AUTO)
    descricao = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey("usuarios.User", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["timestamp"]
```

#### Model: `Presenca` (migrado, sem alteração estrutural)

```python
class Presenca(models.Model):
    sessao = models.ForeignKey(Sessao, on_delete=models.CASCADE, related_name="presencas")
    inscricao = models.ForeignKey("eventos.Inscricao", on_delete=models.CASCADE)
    presente = models.BooleanField(default=False)
    ultima_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("sessao", "inscricao")]
```

### 5.4 URLs do Módulo

```
/hub/<slug>/sessoes/                            → lista_sessoes (liderança)
/hub/<slug>/sessoes/nova/                       → criar_sessao (liderança)
/hub/<slug>/sessoes/<sessao_id>/                → painel_sessao (liderança)
/hub/<slug>/sessoes/<sessao_id>/editar/         → editar_sessao (liderança)
/hub/<slug>/sessoes/<sessao_id>/status/         → alterar_status (POST, liderança)
/hub/<slug>/sessoes/<sessao_id>/leitor/         → leitor_presenca (liderança + permissão leitor)
/hub/<slug>/sessoes/<sessao_id>/presenca/toggle/ → toggle_presenca (POST, liderança + permissão leitor)
/hub/<slug>/sessoes/<sessao_id>/presenca/contagem/ → contagem_presenca (GET, HTMX polling)
/hub/<slug>/sessoes/<sessao_id>/votacoes/nova/  → criar_votacao (liderança)
/hub/<slug>/sessoes/<sessao_id>/votacoes/<vid>/ → painel_votacao (liderança)
/hub/<slug>/sessoes/<sessao_id>/votacoes/<vid>/encerrar/ → encerrar_votacao (POST, liderança)
/hub/<slug>/sessoes/<sessao_id>/votacoes/<vid>/minerva/  → voto_minerva (POST, liderança)
/hub/<slug>/sessoes/<sessao_id>/votacoes/<vid>/resultado/ → resultado_votacao (GET, HTMX polling)
/hub/<slug>/votacoes/<vid>/votar/              → registrar_voto (POST, delegado autenticado)
/hub/<slug>/sessoes/<sessao_id>/log/adicionar/ → adicionar_log_manual (POST, liderança)
/hub/<slug>/sessoes/<sessao_id>/log/exportar/  → exportar_log (GET, liderança)
/hub/<slug>/sessoes/<sessao_id>/log/excluir/<log_id>/ → excluir_log_manual (POST, liderança)
```

### 5.5 Signals

```python
# signals.py

# 1. Ao aprovar inscrição de delegado/ex-officio → gerar CredencialQRCode
@receiver(post_save, sender=Inscricao)
def gerar_qrcode_ao_aprovar(sender, instance, **kwargs):
    papeis_com_qr = [PAPEL_DELEGADO, PAPEL_EX_OFFICIO]
    if instance.status == STATUS_APROVADO and instance.papel_evento in papeis_com_qr:
        CredencialQRCode.objects.get_or_create(inscricao=instance, defaults={"token": gerar_token()})

# 2. Ao mudar status da sessão → gerar EventoLog automático
@receiver(pre_save, sender=Sessao)
def log_mudanca_status(sender, instance, **kwargs):
    # compara status anterior com novo e cria EventoLog adequado
```

### 5.6 Services

#### `services/qrcode.py`
```python
def gerar_token() -> str
def gerar_qrcode_svg(token: str) -> str  # retorna SVG inline
def invalidar_token(inscricao_id: int) -> CredencialQRCode  # ativo=False + novo token
```

#### `services/quorum.py`
```python
def calcular_delegacao_esperada(evento_id: int) -> int
def calcular_presentes(sessao_id: int) -> int
def quorum_atingido(sessao_id: int) -> bool
def info_quorum(sessao_id: int) -> dict  # {presentes, esperados, atingido, percentual}
```

#### `services/eventlog.py`
```python
def log_sessao_aberta(sessao: Sessao) -> EventoLog
def log_sessao_encerrada(sessao: Sessao) -> EventoLog
def log_quorum_atingido(sessao: Sessao) -> EventoLog
def log_entrada(sessao: Sessao, inscricao) -> EventoLog
def log_saida(sessao: Sessao, inscricao) -> EventoLog
def log_votacao_aberta(votacao: Votacao) -> EventoLog
def log_votacao_encerrada(votacao: Votacao) -> EventoLog
def log_voto_minerva(votacao: Votacao) -> EventoLog
def log_manual(sessao: Sessao, descricao: str, usuario) -> EventoLog
```

---

## 6. Interface do Usuário — Telas

### 6.1 Painel da Sessão (Liderança)

Layout em três colunas (desktop) / stack vertical (mobile):

**Coluna Esquerda: Controles da Sessão**
- Badge de status com cor (cinza=Em Breve, azul=Chamada, verde=Aberta, preto=Encerrada)
- Botão de transição de status (único, contextual ao status atual)
- Badge "Verificação de Poderes" quando aplicável
- Indicador de quórum (verde/vermelho, atualizado por HTMX polling)
- Contagem: "X de Y delegados presentes (Z%)"

**Coluna Central: Votações**
- Botão "Nova Votação" (desabilitado se sessão não está Aberta)
- Lista de votações da sessão com status
- Votação ativa em destaque com contagem em tempo real
- Botões: Encerrar Votação / Voto de Minerva (quando empate)

**Coluna Direita: Linha do Tempo**
- Feed cronológico de EventoLog
- Campo + botão para inserir registro manual
- Botão "Exportar para Ata" (abre modal com texto formatado)

### 6.2 Leitor de Presença (Câmera)

- Tela full-width mobile-first
- Viewfinder centralizado (html5-qrcode)
- Exibição do status da sessão e contagem de presentes
- Feedback: overlay verde (entrada) ou amarelo (saída) com nome do delegado
- Campo de entrada manual de token (fallback)
- Botão "Fechar Leitor" (retorna ao painel)

### 6.3 Hub do Delegado (Atualização)

- **Card de Credencial:** QR Code inline (SVG), nome, papel no evento
- **Sessão Atual:** badge de status, pauta (se informada)
- **Votação Ativa:** três botões estilizados (A Favor=verde, Contra=vermelho, Abster-se=cinza)
- **Meu Voto:** após votar, exibe o voto registrado (sem poder alterar)
- Delegados sem papel de voto (Correspondente/Visitante) veem as votações em modo somente leitura

### 6.4 Lista de Sessões (Liderança, Painel do Evento)

- Tabela/cards com: Nome, Data/Hora, Status, Quórum, Nº de votações, Ações
- Botão "Nova Sessão"
- Link para "Leitor de Presença" da sessão ativa

---

## 7. Requisitos de Segurança

| Risco | Mitigação |
|---|---|
| Enumeração de tokens QR | UUID v4 hex (não-sequencial, 128 bits) |
| Votar por outro delegado | `VotoParticipante` vinculado à `inscricao` do request.user, verificado server-side |
| CSRF no toggle de presença | Django CSRF token obrigatório em todos os POSTs |
| Acesso não autorizado ao leitor | Decorador `@user_passes_test(is_lideranca)` + verificação futura de permissão granular |
| Manipulação de contagem de votos | Contagem calculada via `COUNT()` do banco, não campo cacheado |
| Replay attack no QR | Token invalidado e regenerado ao reemitir; cada token é de uso contínuo (não de uso único) pois é o crachá persistente |

---

## 8. Etapas de Implementação

O módulo é dividido em 5 etapas independentes mas sequencialmente dependentes. Cada etapa é deployável e testável isoladamente.

---

### ETAPA 1 — Fundação: Models e Migração (Estimativa: 1 dia)

**Objetivo:** Estrutura de dados completa no banco, sem quebrar o que existe.

**Tarefas:**

1. **Criar app `apps.sessoes`**
   - `python manage.py startapp sessoes apps/sessoes`
   - Adicionar `apps.sessoes` em `INSTALLED_APPS`
   - Criar `apps/sessoes/apps.py` com `AppConfig`

2. **Criar models em `apps/sessoes/models.py`**
   - `Sessao` com campo `status` e `is_verificacao_poderes`
   - `CredencialQRCode` com campo `token` e `ativo`
   - `Presenca` (mover de `apps.hub`)
   - `Votacao` com campos de status e minerva
   - `VotoParticipante` com unique_together
   - `EventoLog` com tipo e timestamp

3. **Migration e compatibilidade com hub**
   - Criar migration que replica `Sessao` e `Presenca` de `hub` para `sessoes`
   - Atualizar `apps/hub/models.py` para importar `Sessao` e `Presenca` de `apps.sessoes` (mantendo retrocompatibilidade)
   - Criar migration em hub que remove os models migrados

4. **Registrar models no admin de `sessoes`**

5. **Criar `apps/sessoes/signals.py`** com geração automática de QR Code ao aprovar inscrição.

**Critério de aceite:** `python manage.py migrate` sem erros. Admin exibe todos os novos models. Inscrição aprovada gera `CredencialQRCode`.

---

### ETAPA 2 — Gestão de Sessões pela Liderança (Estimativa: 1 dia)

**Objetivo:** CRUD completo de sessões e controle de status via interface.

**Tarefas:**

1. **Criar `apps/sessoes/forms.py`**
   - `SessaoForm`: nome, data_hora, is_verificacao_poderes
   - Validação: impede duas sessões com `is_verificacao_poderes=True` no mesmo evento
   - Validação: impede duas sessões com status ABERTA/CHAMADA simultâneas

2. **Criar views em `apps/sessoes/views/painel.py`**
   - `lista_sessoes(request, slug)`: lista todas as sessões do evento
   - `criar_sessao(request, slug)`: form de criação
   - `editar_sessao(request, slug, sessao_id)`: form de edição
   - `alterar_status(request, slug, sessao_id)`: POST que avança o status com validações e dispara `services/eventlog.py`

3. **Criar `apps/sessoes/services/eventlog.py`** com funções de log automático para mudanças de status.

4. **Criar `apps/sessoes/urls.py`** com as rotas de painel.

5. **Criar templates:**
   - `templates/sessoes/lista.html`
   - `templates/sessoes/form.html`
   - `templates/sessoes/painel.html` (estrutura básica, sem votações ainda)

6. **Atualizar `core/urls.py`** para incluir `apps.sessoes.urls`.

7. **Atualizar template do painel do evento** (em hub) para linkar para lista de sessões.

**Critério de aceite:** Liderança consegue criar sessões, avançar status, e ver logs automáticos de abertura/encerramento na página da sessão.

---

### ETAPA 3 — QR Code e Leitor de Presença (Estimativa: 1-2 dias)

**Objetivo:** Delegados veem QR Code no Hub; liderança/voluntário escaneia pela câmera.

**Tarefas:**

1. **Criar `apps/sessoes/services/qrcode.py`**
   - `gerar_token()`: uuid4 hex prefixado
   - `gerar_qrcode_svg(token)`: usa biblioteca `qrcode[svg]` ou `segno` para SVG inline
   - `invalidar_e_regenerar(inscricao)`: marca atual como `ativo=False`, cria novo
   - Instalar dependência: `segno` (mais leve que qrcode para SVG)

2. **Criar `apps/sessoes/views/presenca.py`**
   - `leitor_presenca(request, slug, sessao_id)`: renderiza página com html5-qrcode
   - `toggle_presenca(request, slug, sessao_id)`: endpoint POST AJAX
     - Valida token, busca inscricao, faz toggle em `Presenca`, cria `EventoLog`
     - Retorna JSON: `{ok, nome, presente, quorum}`
   - `contagem_presenca(request, slug, sessao_id)`: GET que retorna partial HTML (HTMX)

3. **Atualizar `hub/index.html`** para exibir QR Code do delegado
   - Renderizar SVG inline no card de credencial
   - Visível apenas para DELEGADO e EX_OFFICIO aprovados

4. **Criar `templates/sessoes/leitor.html`**
   - Integração html5-qrcode via CDN
   - JS fetch para endpoint toggle
   - Feedback visual (overlay colorido 2s)
   - Input manual de token como fallback

5. **Adicionar botão "Regenerar QR Code"** na lista de inscrições do evento (liderança)
   - View: `regenerar_qrcode(request, inscricao_id)` em `views/presenca.py`
   - URL: `/hub/<slug>/inscricoes/<inscricao_id>/regenerar-qr/`

6. **Criar `apps/sessoes/services/quorum.py`** e integrar no endpoint de contagem.

**Critério de aceite:**
- Hub do delegado exibe QR Code
- Ao escanear: presença toggled, log criado, feedback visual exibido
- Indicador de quórum atualiza automaticamente via HTMX polling

---

### ETAPA 4 — Votações em Tempo Real (Estimativa: 1-2 dias)

**Objetivo:** Liderança cria votações; delegados votam pelo hub; resultado em tempo real.

**Tarefas:**

1. **Criar `apps/sessoes/forms.py`** (adicionar):
   - `VotacaoForm`: apenas `titulo`

2. **Criar `apps/sessoes/views/votacao.py`**
   - `criar_votacao(request, slug, sessao_id)`: valida sessão ABERTA, cria votação, log automático
   - `painel_votacao(request, slug, sessao_id, votacao_id)`: detalhe com contagem atual
   - `resultado_votacao(request, slug, sessao_id, votacao_id)`: partial HTMX com contagem live
   - `encerrar_votacao(request, slug, sessao_id, votacao_id)`: lógica de encerramento + empate + log
   - `voto_minerva(request, slug, sessao_id, votacao_id)`: registra Voto de Minerva + log
   - `registrar_voto(request, slug, votacao_id)`: POST do delegado, unique_together enforced

3. **Atualizar `hub/index.html`** para exibir votação ativa com três botões
   - Delegados DELEGADO/EX_OFFICIO: botões ativos
   - Correspondentes/Visitantes: visualização somente leitura
   - Após votar: exibe o voto registrado

4. **Atualizar `templates/sessoes/painel.html`** com seção de votações
   - Lista de votações com status
   - Botão "Nova Votação" (condicional ao status ABERTA)
   - Contador de votos com HTMX polling (hx-trigger="every 3s")

5. **Adicionar entradas ao `services/eventlog.py`** para votações.

**Critério de aceite:**
- Votação criada aparece no Hub dos delegados
- Contagem atualiza a cada 3s no painel da liderança
- Empate dispara estado "Aguardando Voto de Minerva"
- Resultado correto registrado no Event Log

---

### ETAPA 5 — Linha do Tempo e Exportação (Estimativa: 0,5 dia)

**Objetivo:** Visualização completa do Event Log e exportação para ata.

**Tarefas:**

1. **Criar `apps/sessoes/views/log.py`**
   - `adicionar_log_manual(request, slug, sessao_id)`: POST com texto livre, cria `EventoLog(tipo=MANUAL)`
   - `exportar_log(request, slug, sessao_id)`: retorna texto formatado para ata
   - `excluir_log_manual(request, slug, sessao_id, log_id)`: permite excluir apenas tipo=MANUAL

2. **Criar `apps/sessoes/forms.py`** (adicionar):
   - `EventoLogManualForm`: campo `descricao` com textarea

3. **Atualizar `templates/sessoes/painel.html`** com seção de linha do tempo
   - Feed vertical cronológico
   - Badge: "Sistema" (azul) vs "Manual" (cinza)
   - Timestamps formatados em `pt-BR`
   - Formulário inline de registro manual
   - Botão "Excluir" apenas em registros manuais
   - Botão "Exportar Linha do Tempo"

4. **Criar modal ou nova página de exportação:**
   - Formato de texto:
     ```
     ATA DA [NOME DA SESSÃO]
     Evento: [Nome do Evento]
     Data: [data_hora formatada]
     
     LINHA DO TEMPO
     
     [HH:MM] — [descricao]
     [HH:MM] — [descricao]
     ...
     
     Gerado automaticamente pela Plataforma Sinodal em [data de exportação].
     ```

**Critério de aceite:**
- Secretário insere registro manual e aparece na linha do tempo
- Botão Exportar abre modal com texto copiável
- Entradas automáticas têm badge diferente das manuais

---

## 9. Plano de Migração dos Models Existentes

O `apps.hub` possui `Sessao` e `Presenca` atualmente. A migração deve ser:

### Passo 1 — Criar novos models em `apps.sessoes`
Sem alterar nada em `apps.hub` ainda.

### Passo 2 — Data migration
Copiar dados de `hub_sessao` → `sessoes_sessao` e `hub_presenca` → `sessoes_presenca`.

### Passo 3 — Atualizar referências em `apps.hub`
```python
# apps/hub/models.py
from apps.sessoes.models import Sessao, Presenca  # importação explícita

# As FK em DocumentoEvento e outras que referenciem Sessao precisam apontar para sessoes.Sessao
```

### Passo 4 — Remover models de `apps.hub`
Com migration que detecta que os models foram movidos (usando `state_operations` + `SeparateDatabaseAndState` se necessário para não perder dados).

### Passo 5 — Atualizar admin e views do hub
Todas as referências a `hub.Sessao` e `hub.Presenca` passam para `sessoes.Sessao` e `sessoes.Presenca`.

---

## 10. Dependências Técnicas Novas

| Biblioteca | Uso | Instalação |
|---|---|---|
| `segno` | Geração de QR Code em SVG (server-side, sem dependências pesadas) | `pip install segno` |
| `html5-qrcode` | Leitura de QR por câmera (CDN, client-side) | CDN no template do leitor |

Nenhuma mudança em banco de dados além das migrations descritas. Nenhum serviço de WebSocket necessário (HTMX polling suficiente para a escala esperada de um congresso sinodal).

---

## 11. Considerações Futuras (Fora do Escopo Atual)

- **Fila de Oradores:** model `Orador` vinculado a `Sessao`, com ordem e tempo falado.
- **Exportação PDF da Ata:** integração com `weasyprint` ou geração em LaTeX.
- **Notificações Push para Delegados:** via Service Worker quando votação é aberta.
- **WebSockets (Django Channels):** substituir HTMX polling por push real se a escala exigir (> 200 delegados simultâneos).
- **Múltiplos Leitores Simultâneos:** já funciona, mas sem coordenação de conflito explícita (PostgreSQL `SELECT FOR UPDATE` pode ser adicionado no toggle).
- **Permissão granular de Leitor:** hoje é `tipo=LIDERANCA`; futuramente, uma permissão customizada `pode_ler_presenca` para voluntários sem acesso total ao painel.
- **Relatório de Presença por Sessão:** exportação CSV com nome, papel e horários de entrada/saída de cada delegado.

---

## 12. Checklist de Aceite Final

- [ ] App `apps.sessoes` instalado e migrations aplicadas sem erros
- [ ] Models antigos de `apps.hub` removidos sem perda de dados
- [ ] QR Code gerado automaticamente ao aprovar inscrição de delegado
- [ ] QR Code exibido no Hub do delegado (SVG inline)
- [ ] Leitor de câmera funciona em mobile (iOS Safari + Android Chrome)
- [ ] Toggle presença funciona: 1ª leitura = entrada, 2ª leitura = saída
- [ ] Logs automáticos gerados em cada toggle
- [ ] Indicador de quórum atualiza via HTMX polling no painel da liderança
- [ ] Sessão de Verificação de Poderes marcável e visível com badge
- [ ] Apenas uma sessão pode estar Aberta ou em Chamada por vez
- [ ] Votação criada aparece para delegados no Hub
- [ ] Cada delegado vota uma única vez (unique_together enforced)
- [ ] Empate dispara estado Minerva; Voto de Minerva registrado no log
- [ ] Resultado da votação exibido em tempo real no painel (polling 3s)
- [ ] Secretário adiciona registro manual na linha do tempo
- [ ] Exportação da linha do tempo produz texto copiável para ata
- [ ] Entradas automáticas NÃO podem ser excluídas via interface
- [ ] Entradas manuais PODEM ser excluídas pela liderança
- [ ] Todas as views da liderança bloqueadas para usuários não-LIDERANCA
- [ ] Delegados sem papel de voto veem votações em somente leitura
