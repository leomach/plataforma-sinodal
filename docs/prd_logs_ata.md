# PRD — Logs para Elaboração de Ata
**Versão:** 1.0  
**Autor:** Equipe Plataforma Sinodal  
**Data:** 2026-05-23  
**Status:** Aprovado para implementação

---

## 1. Contexto e Problema

O módulo `apps.sessoes` já registra eventos automaticamente (abertura, fechamento, entradas, votações, etc.) via `apps/sessoes/services/eventlog.py`. O texto atual desses logs tem linguagem operacional e informal (ex.: "Sessão X encerrada.", "Delegado João entrou no plenário."), adequada para o monitoramento interno da sessão, mas inadequada para compor a ata oficial.

A ata eclesiástica da IPB exige linguagem **expositiva, formal, no presente do indicativo**, sem debates ou opiniões, e deve formar **um único parágrafo contínuo**. O secretário hoje precisa reescrever manualmente todo o conteúdo gerado pelo sistema, perdendo o benefício da automatização.

---

## 2. Objetivo

Reformatar o texto dos **logs automáticos** para que cada frase já esteja pronta para ser inserida diretamente no corpo da ata, sem reescrita. Aprimorar a exportação para fornecer:

1. **Rascunho do Corpo da Ata** — parágrafo único, sem horários, pronto para colar no documento oficial.
2. **Notas de Rodapé Sugeridas** — índice numerado com horários, conforme exige o Manual de Atas Eletrônicas da IPB.
3. **Linha do Tempo Operacional** — mantida para controle interno (formato atual com `[HH:MM]`).

---

## 3. Escopo

### 3.1 O que será automatizado (logs do sistema)

| Evento | Texto atual | Texto proposto (ata) |
|--------|-------------|----------------------|
| Sessão aberta | `Sessão "X" aberta. Presentes: N delegados (Quórum atingido).` | `Às HH:MM, o Presidente declara aberta a sessão. Encontram-se presentes N delegados credenciados, sendo declarado atingido o quórum regimental.` |
| Sessão encerrada | `Sessão "X" encerrada.` | `Nada mais havendo a tratar, o Presidente declara encerrada a sessão às HH:MM.` |
| Chamada iniciada | `Chamada de presença iniciada para a sessão "X".` | `Procede-se à chamada nominal dos delegados credenciados.` |
| Chamada cancelada | `Chamada cancelada. Sessão "X" retornou a Em Breve.` | `A chamada de presença é interrompida e a sessão suspensa.` |
| Quórum atingido | `Quórum legal atingido: N de M delegados presentes.` | `Declara-se atingido o quórum regimental, com N delegados presentes de um total de M credenciados.` |
| Entrada de delegado | `Delegado Nome entrou no plenário.` | `Às HH:MM, o(a) delegado(a) {Nome Completo} ingressa no recinto do plenário.` |
| Saída de delegado | `Delegado Nome retirou-se do plenário.` | `Às HH:MM, o(a) delegado(a) {Nome Completo} retira-se do recinto do plenário, com anuência da presidência.` |
| Votação aberta | `Votação aberta: "Título".` | `Submete-se ao plenário a seguinte proposta: "{Título}".` |
| Votação encerrada | `Votação "X" encerrada: N a favor, N contra, N abs. Resultado.` | `Encerrada a votação da proposta "{Título}", apura-se: N voto(s) a favor, N voto(s) contra e N abstenção(ões). O plenário resolve {aprovar/rejeitar} a matéria.` |
| Voto de Minerva | `Voto de Minerva por Nome: A Favor. Resultado final: X.` | `Verificado empate na votação, o Presidente {Nome} exerce o Voto de Qualidade (Voto de Minerva), manifestando-se {a favor/contra} a proposta. Em consequência, o plenário resolve {aprovar/rejeitar} a matéria em votação.` |
| Mesa composta | `Mesa Diretora composta: Nome (Cargo), ...` | `Procede-se à composição da Mesa Diretora, ficando assim constituída: {Cargo}: {Nome}; {Cargo}: {Nome}; (…).` |
| Transferência presidência | `Presidência transferida de X para Y.` | `O Presidente {Nome} transfere a condução dos trabalhos ao {Cargo} {Nome}, que assume a presidência da sessão.` |

### 3.2 O que NÃO será automatizado (registro manual do secretário)

Por serem eventos não capturáveis pelo sistema e que exigem julgamento do secretário, os itens abaixo devem ser inseridos via **campo de registro manual** do painel, seguindo os modelos sugeridos na seção 5.

---

## 4. Checklist do Secretário (Registros Manuais Obrigatórios)

O secretário deve adicionar manualmente, na ordem em que ocorrem:

| # | Momento | Modelo de texto sugerido |
|---|---------|--------------------------|
| 1 | **Oração de abertura** | `O Rev./Presb. {Nome Completo} conduz o exercício espiritual de abertura.` |
| 2 | **Aprovação da ata anterior** | `O Presidente coloca em discussão a ata da sessão anterior. A ata é aprovada sem ressalvas.` OU `A leitura e aprovação da ata anterior é adiada para a próxima sessão.` |
| 3 | **Recebimento de documentos/relatórios** | `O plenário recebe o relatório {da Tesouraria / da Secretaria Executiva / (nome da comissão)}, que é encaminhado para análise.` |
| 4 | **Credenciamento especial / comunicados** | `O Presidente informa ao plenário que (descrição do comunicado).` |
| 5 | **Proposta rejeitada a pedido de registro** | `O(A) delegado(a) {Nome} solicita que conste em ata a proposta rejeitada: "(texto da proposta)". O plenário concede a solicitação.` |
| 6 | **Oração de encerramento** | `O Rev./Presb. {Nome Completo} conduz o exercício espiritual de encerramento dos trabalhos.` |

### 4.1 Tom e forma para registros manuais

- Sempre no **presente do indicativo** (ex.: "O plenário resolve…", não "Foi resolvido que…").
- Sem opiniões ou descrição de debates.
- Primeira menção de qualquer pessoa: **nome completo por extenso**.
- Usar abreviaturas consagradas: Rev., Presb., UMP, SC/IPB, CE.

---

## 5. Formato de Exportação Aprimorado

### 5.1 Seção A — Rascunho do Corpo da Ata

Concatenação de **todos** os `log.descricao` em ordem cronológica, separados por um único espaço, sem quebras de linha nem timestamps. Pronto para colar como parágrafo único na ata oficial.

Exemplo:
> Procede-se à composição da Mesa Diretora, ficando assim constituída: Presidente: João Silva; Vice-Presidente: Maria Souza. O Rev. Carlos Lima conduz o exercício espiritual de abertura. Procede-se à chamada nominal dos delegados credenciados. Declara-se atingido o quórum regimental, com 32 delegados presentes de um total de 45 credenciados. Às 14:05, o Presidente declara aberta a sessão. (…) Nada mais havendo a tratar, o Presidente declara encerrada a sessão às 17:42.

### 5.2 Seção B — Notas de Rodapé Sugeridas

Conforme o Manual de Atas Eletrônicas da IPB, atas digitais obrigam o uso de notas de rodapé numeradas sequencialmente (fonte 10) como índice. O sistema gerará automaticamente as notas a partir dos logs **automáticos** (TIPO_AUTO), usando o número de sequência na ordem em que cada evento ocorreu.

Formato:
```
1. HH:MM — Composição da Mesa Diretora
2. HH:MM — Chamada de presença
3. HH:MM — Quórum atingido
4. HH:MM — Abertura da sessão
5. HH:MM — Votação: "Título da proposta" (Aprovada)
6. HH:MM — Encerramento da sessão
```

### 5.3 Seção C — Linha do Tempo Operacional (mantida)

Formato atual com `[HH:MM] — tipo — descrição`, para uso interno e auditoria.

---

## 6. Regras Tipográficas a Observar na Exportação

Conforme o Manual IPB para atas eletrônicas:

- **Papel:** A4, retrato, somente frente.
- **Margens:** 3 cm em todos os lados.
- **Fonte:** Times New Roman, Arial ou Courier, tamanho 12 ou 14, cor preta.
- **Negrito/caixa-alta:** apenas para títulos e termos de destaque no corpo.
- **Notas de rodapé:** numeradas sequencialmente, fonte 10.
- **Paginação:** número em negrito no canto direito (superior ou inferior).
- **Espaços em branco:** inutilizados com hífens contínuos até a linha de assinatura.

> **Nota de implementação:** A geração de PDF seguindo essas especificações tipográficas está **fora do escopo desta versão**. O sistema entregará o texto já formatado para que o secretário cole em seu processador de texto (Word, LibreOffice) e aplique a formatação final. A geração de PDF tipograficamente conforme é escopo de uma versão futura.

---

## 7. Implementação Técnica

### 7.1 `apps/sessoes/services/eventlog.py`

- Adicionar helper interno `_hora_agora() → str` retornando `timezone.localtime(timezone.now()).strftime('%H:%M')`.
- Reescrever o texto de cada função de log conforme a tabela da seção 3.1.
- Funções `log_entrada` e `log_saida` passam a incluir o horário no corpo do texto (obrigação da IPB para entradas/saídas fora do momento da chamada).
- Funções `log_sessao_aberta` e `log_sessao_encerrada` passam a incluir o horário no texto.

### 7.2 `apps/sessoes/views/log.py` — `exportar_log`

- Gerar três blocos de conteúdo: `rascunho_ata`, `notas_rodape`, `linha_tempo`.
- `rascunho_ata`: join de todos `log.descricao` com `" "`.
- `notas_rodape`: enumerate de logs `TIPO_AUTO` com timestamp e descrição curta (primeiros 60 chars).
- `linha_tempo`: formato atual `[HH:MM] — {tipo} — {descricao}`.

### 7.3 `templates/sessoes/exportar_log.html`

- Três textareas separadas com labels claros.
- Botão de cópia individual para cada seção.
- Colapsar "Linha do Tempo Operacional" por padrão (details/summary).

---

## 8. Fora do Escopo

- Geração de PDF tipograficamente conforme o Manual IPB (versão futura).
- Inutilização automática de espaços em branco com hífens (responsabilidade do secretário no processador de texto).
- Múltiplos membros "Outros" na Mesa (versão futura, se necessário).
- Versionamento ou histórico de edição de logs manuais.
- Assinatura eletrônica integrada ao sistema.
