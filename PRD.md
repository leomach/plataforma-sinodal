# Product Requirements Document (PRD) - Módulo de Eventos (Plataforma Sinodal)

## 1. Visão Geral
O módulo de eventos é o coração da Plataforma Sinodal, permitindo que a liderança organize encontros de comunhão e reuniões administrativas (Congressos e Comissões Executivas), e que a juventude se inscreva e participe de forma organizada e engajada.

## 2. Objetivos
- Facilitar a criação e gestão de eventos pela liderança sinodal e local.
- Simplificar o processo de inscrição para a juventude.
- Eliminar o uso de papel na "Verificação de Poderes", digitalizando a validação de credenciais de delegados via link em nuvem (Google Drive).
- Criar o "Hub do Evento", uma área restrita para leitura de documentos oficiais e relatórios, agilizando as plenárias.
- Integrar elementos de gamificação (badges/medalhas) à participação e engajamento.

## 3. Público-Alvo
- **Juventude (Sócios/Visitantes):** Jovens que se inscrevem para participar dos eventos, seja para comunhão ou representação.
- **Liderança (Diretoria/Secretarias):** Organizadores que gerenciam as inscrições, validam credenciais e sobem os documentos oficiais.

## 4. Requisitos Funcionais

### 4.1. Gestão de Eventos (Liderança)
- **Criação de Eventos:** Título, descrição (Rich Text/Markdown), data de início e fim, local, imagem de capa (banner).
- **Categorização:** O sistema deve diferenciar eventos `ADMINISTRATIVOS` (exigem controle de delegados e plenárias) de eventos de `COMUNHAO` (inscrição livre).
- **Tipos de Inscrição (Cargos no Evento):** Em eventos administrativos, limitar a escolha a: Delegado (Efetivo), Ex-Officio, Correspondente e Visitante.
- **Painel de Validação:** Visualizar lista de inscritos, acessar o link da credencial enviada pelo usuário e alterar o status (Aprovar/Rejeitar).

### 4.2. Inscrições (Juventude)
- **Fluxo de Inscrição:** Escolher o tipo de participação. Se escolher `Delegado`, o sistema exigirá obrigatoriamente um link (URL) do Google Drive contendo a foto/PDF da credencial assinada pela autoridade competente.
- **Meus Eventos:** Espaço no perfil do usuário para ver eventos em que está inscrito e o status da inscrição.

### 4.3. Hub do Delegado e Plenárias (Eventos Administrativos)
- **Acesso Restrito:** Apenas usuários com inscrição aprovada como "Delegado" ou "Ex-Officio" têm acesso à aba "Documentos" do evento.
- **Acervo Digital:** Visualização e download de Relatórios da Diretoria, Livro de Relatórios e Propostas.
- **Controle de Presença:** Registro de presença do delegado por Sessão/Plenária (Sessão 1, Sessão 2), para geração de atas precisas.

### 4.4. Gamificação
- **Medalhas:** Atribuição automática (via triggers do banco) ou manual de badges ao concluir a participação em eventos chave (Ex: Badge "Fiel Representante" para delegados presentes em todas as sessões).

## 5. Requisitos Não Funcionais
- **Stack Tecnológica:** Python, Django 5, PostgreSQL (via psycopg3).
- **Arquitetura Modular:** O módulo de eventos deve ficar isolado dentro da pasta `apps/eventos`.
- **Interface Mobile-First:** Essencial, pois as inscrições e a leitura do Hub serão feitas predominantemente via smartphone.
- **Storage Otimizado:** Não faremos upload de arquivos pesados no servidor para credenciais; usaremos campos de URL apontando para a nuvem do próprio usuário (Drive).

## 6. User Stories

| ID | Ator | Story |
| :--- | :--- | :--- |
| US01 | Liderança | Eu quero criar a "1ª CE da Sinodal", definindo-a como evento administrativo, para que as UMPs enviem seus representantes. |
| US02 | Sócio | Eu quero me inscrever como delegado na CE e colar o link do Drive da minha credencial para não precisar levar papel. |
| US03 | Liderança (1º Sec) | Eu quero visualizar a lista de pendentes, clicar no link da credencial e aprovar a inscrição, validando o delegado no sistema. |
| US04 | Delegado | Eu quero acessar o Hub da CE pelo celular antes do evento para ler os relatórios das secretarias, pois eles não serão lidos em plenário. |
| US05 | Sócio | Eu quero ver no meu perfil as medalhas que ganhei por comparecer aos eventos da Sinodal. |

## 7. Modelo de Dados (Django ORM - Proposta)

### Evento (`apps/eventos/models.py`)
- `titulo` (CharField)
- `slug` (SlugField)
- `descricao` (TextField)
- `categoria` (CharField/Choices - 'ADMINISTRATIVO', 'COMUNHAO')
- `data_inicio` (DateTimeField)
- `data_fim` (DateTimeField)
- `local` (CharField)
- `banner` (ImageField - armazenado em nuvem como AWS S3 ou Whitenoise)
- `ativo` (BooleanField)

### Inscricao
- `usuario` (ForeignKey para User)
- `evento` (ForeignKey para Evento)
- `papel_evento` (CharField/Choices - 'DELEGADO', 'EX_OFFICIO', 'CORRESPONDENTE', 'VISITANTE')
- `status` (CharField/Choices - 'PENDENTE', 'APROVADO', 'REJEITADO')
- `credential_url` (URLField - Link do Google Drive para validação)
- `data_inscricao` (DateTimeField)

### Sessao (Para controle de Plenárias)
- `evento` (ForeignKey para Evento)
- `nome` (CharField - Ex: "Sessão de Verificação de Poderes", "Plenária 2")
- `data_hora` (DateTimeField)

### Presenca
- `sessao` (ForeignKey para Sessao)
- `inscricao` (ForeignKey para Inscricao - Apenas delegados aprovados)
- `presente` (BooleanField)

### DocumentoEvento
- `evento` (ForeignKey para Evento)
- `titulo` (CharField - Ex: "Livro de Relatórios")
- `arquivo_url` (URLField)
- `restrito_delegados` (BooleanField - Se true, visitantes não veem)

## 8. Design & UX
- A interface deve seguir rigorosamente as regras do arquivo `DESIGN.md` na raiz do projeto.
- Uso de componentes com estilo "Flat 2.0", cantos arredondados e sombras leves para modais e cards.
- **Cores Semânticas:** Botões de ação principal usam a cor oficial `primary` (Azul UMP). Status de inscrição "Aprovado" deve usar a cor semântica `success` (Verde), e "Pendente" a cor `warning` (Amarelo/Laranja). A cor `tertiary` (Verde IPB) será usada para os ícones e cabeçalhos dos documentos oficiais no Hub da CE.
## 9. Formulários Dinâmicos (Estilo Google Forms)
Para tornar as inscrições flexíveis, cada evento poderá ter campos personalizados.

### 9.1. Modelos Adicionais
#### CampoEvento (As perguntas)
- `evento` (ForeignKey)
- `label` (CharField - Ex: "Tamanho da Camisa")
- `tipo_campo` (CharField - Texto, Inteiro, Seleção, Checkbox)
- `obrigatorio` (BooleanField)
- `opcoes` (TextField - Para campos de seleção, separados por vírgula)

#### RespostaInscricao (As respostas)
- `inscricao` (ForeignKey)
- `campo` (ForeignKey)
- `valor` (TextField)

### 9.2. Fluxo de Trabalho
1. **Liderança:** Ao criar/editar evento, adiciona "Perguntas Extras".
2. **Sócio:** Ao se inscrever, o formulário gera automaticamente os campos definidos.
3. **Validação:** O sistema garante que campos obrigatórios sejam preenchidos.
