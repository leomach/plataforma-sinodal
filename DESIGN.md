colors:
  # Cores Oficiais UMP e IPB
  primary: '#1D4ED8' # Azul UMP (Representa a Tocha/Organização)
  secondary: '#DC2626' # Vermelho UMP (Representa a chama/Alegria)
  tertiary: '#00703C' # Verde IPB (Sarça Ardente/Institucional)
  
  # Tons Neutros (Fundo, Texto e Bordas do Dashboard)
  background: '#F8FAFC'
  surface: '#FFFFFF'
  surface-hover: '#F1F5F9'
  text-main: '#0F172A'
  text-muted: '#64748B'
  border: '#E2E8F0'

  # Cores Semânticas (Status de Inscrições, Protocolos, Badges)
  success: '#10B981' # Inscrição Aprovada / Delegado
  warning: '#F59E0B' # Ofício Pendente
  error: '#EF4444' # Rejeitado / Erro
  badge-gold: '#F59E0B'
  badge-silver: '#94A3B8'

typography:
  fontFamily:
    sans: 'Inter, system-ui, sans-serif'
    serif: 'Merriweather, "Times New Roman", serif'
  fontSize:
    xs: '0.75rem'
    sm: '0.875rem'
    base: '1rem'
    lg: '1.125rem'
    xl: '1.25rem'
    2xl: '1.5rem'
    3xl: '1.875rem'
    4xl: '2.25rem'
  fontWeight:
    normal: 400
    medium: 500
    semibold: 600
    bold: 700
  lineHeight:
    tight: 1.25
    normal: 1.5
    relaxed: 1.625

spacing:
  1: '0.25rem'
  2: '0.5rem'
  3: '0.75rem'
  4: '1rem'
  6: '1.5rem'
  8: '2rem'
  12: '3rem'
  16: '4rem'

elevation:
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)'
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'

radii:
  sm: '0.25rem'
  md: '0.375rem'
  lg: '0.5rem'
  full: '9999px'
---

# 1. Overview (Brand & Style)
A plataforma da **Confederação Sinodal de Mocidade (UMP) Garanhuns** é um sistema web projetado para a juventude presbiteriana. A interface deve equilibrar dois mundos:
1. **Juventude e Engajamento:** Acessível, amigável e gamificada (sistema de badges, perfis de usuários, eventos).
2. **Seriedade Institucional:** Como lida com processos burocráticos (Hub da CE, atas, credenciais de delegados), precisa transmitir segurança, transparência e organização.

**Moto Oficial:** "Alegres na esperança, fortes na fé, dedicados no amor, unidos no trabalho."
**A Vibe:** Limpa, moderna, rápida (carregamento ágil) e mobile-first, já que a maioria dos jovens acessará via smartphone.

# 2. Colors
O design utiliza as cores oficiais da UMP (Azul e Vermelho) e da Igreja Presbiteriana do Brasil (Verde).
*   **Primary ({colors.primary}):** Usada para botões de ação principal, links ativos, navegação e destaque de liderança.
*   **Secondary ({colors.secondary}):** Usada para badges de conquista, notificações e alertas visuais de importância.
*   **Tertiary ({colors.tertiary}):** Usada em áreas de documentação eclesiástica oficial, como Atas e Livros de Relatórios, remetendo à autoridade do concílio.
*   **Neutrals:** O fundo da aplicação é um cinza bem claro ({colors.background}), com os cards e componentes em branco puro ({colors.surface}) para garantir respiro visual e leitura confortável.

# 3. Typography
A tipografia deve ser altamente legível, visando a leitura de textos longos (como revistas digitais e ofícios).
*   **Sans-serif ({typography.fontFamily.sans}):** Usada em 90% da interface (dashboards, botões, formulários de inscrição, menus).
*   **Serif ({typography.fontFamily.serif}):** Usada estritamente para títulos de documentos oficiais (Ex: "Ata da 1ª CE", "Guia de Trabalho das Sociedades Internas") e citações bíblicas, trazendo o peso da tradição.

# 4. Layout & Spacing
A plataforma utiliza um sistema de grid de 8px para garantir consistência.
*   **Mobile-First:** Formulários de inscrição, upload de links de credenciais e visualização de Kanban devem funcionar perfeitamente em telas pequenas, empilhando colunas (flex-col).
*   **Dashboard Layout:** Menu lateral (Sidebar) expansível no desktop e menu inferior (Bottom Bar) ou sanduíche no mobile. A área de conteúdo principal deve ter um padding máximo de `{spacing.8}` no desktop e `{spacing.4}` no mobile.

# 5. Elevation & Depth
O sistema usa um design "Flat 2.0". As superfícies flutuam levemente sobre o fundo para indicar hierarquia e clicabilidade.
*   **Cards (Eventos, Perfis):** Sombra leve `{elevation.sm}` no estado padrão.
*   **Hover States:** Elevação para `{elevation.md}` e transformação de transição suave (-translate-y-1) para indicar interatividade.
*   **Modais e Diálogos:** Sombra forte `{elevation.lg}` para focar a atenção do usuário no centro da tela.

# 6. Shapes
Os cantos da interface são levemente arredondados (`{radii.md}` ou `{radii.lg}`) para quebrar a rigidez de um software corporativo tradicional, tornando-o mais acolhedor para a juventude, sem parecer infantil. Botões de ação rápida (como "Ganhar Medalha") podem usar `{radii.full}` (formato pílula).

# 7. Components

## Buttons
*   **Primary:** Fundo `{colors.primary}`, texto branco `{colors.surface}`. Hover escurece 10%. Arredondamento `{radii.md}`.
*   **Secondary/Outline:** Fundo transparente, borda `{colors.border}`, texto `{colors.text-main}`. Usado para "Cancelar" ou "Baixar Livro de Relatórios".
*   **Disabled:** Opacidade 50%, cursor-not-allowed.

## Cards de Inscrição / Eventos
*   Fundo `{colors.surface}`, borda sutil `{colors.border}`, padding `{spacing.6}`.
*   Devem exibir de forma clara uma tag de status: "Visitante", "Delegado", "Em Análise", usando as cores semânticas apropriadas.

## Badges (Gamificação)
*   Formato circular ou pílula. Usam cores vibrantes com gradientes leves e ícones (Ex: Ícone de Raio para "Entrega Relâmpago", Ícone de Livro para "Estatístico Capacitado").

## Kanban (Protocolo Sinodal)
*   Colunas com fundo `{colors.surface-hover}`. Cards de ofícios com fundo `{colors.surface}` e indicador visual de prioridade ou status.

# 8. Do's and Don'ts

### Do's (O que fazer)
*   **Faça** com que a "Área do Delegado" e o "Hub da CE" sejam visualmente distintos da área pública do evento (adicione um banner superior azul ou verde escuro para indicar ambiente restrito).
*   **Faça** forte uso de espaços em branco (whitespace) nas listagens de relatórios para evitar fadiga visual.
*   **Faça** o contraste adequado (Acessibilidade WCAG) para textos sobre fundos coloridos.

### Don'ts (O que não fazer)
*   **Não use** jargões informais ("e aí galera") em modais de aprovação de delegados ou atas. Mantenha a alegria, mas com respeito institucional.
*   **Não modifique** as proporções do Símbolo Oficial da UMP (Tocha) ou da IPB (Sarça). Se for usá-los, mantenha a proporção original conforme o manual de identidade visual.
*   **Não polua** as tabelas do Painel Administrativo. Use ícones ao invés de textos repetitivos para ações repetitivas (Aprovar/Rejeitar).