# Requisitos Funcionais das Sessões dos Eventos

O GTSI estabelece que o congresso ou CE é composto por sessões.
RF01: O sistema deve permitir que o administrador crie blocos de horários chamados "Sessões" (Ex: Sessão 1, Sessão 2, Sessão de Encerramento).
RF02: O sistema deve ter uma marcação simples para identificar qual é a "Sessão de Verificação de Poderes" (que obrigatoriamente é a primeira do evento)

A regra exige que as votações não aconteçam sem quórum legal (mais da metade dos delegados)
RF03: Na página de cada Sessão, o sistema deve exibir a lista de todos os usuários com o status de "Delegado Aprovado". O Secretário (você) apenas clica em uma caixa de seleção (checkbox) para marcar quem está presente.
RF04: O sistema calcula automaticamente se os presentes representam mais da metade da delegação esperada e exibe um aviso visual verde: "Quórum Atingido"

Requisito Funcional (RF) para Votação:
A liderança deve poder criar uma "Nova Votação" vinculada à Sessão ativa, informando apenas o Título/Proposta (Ex: "Aprovação do Relatório da Tesouraria").
A votação aparece no celular/tela do Delegado com três botões simples: A Favor, Contra e Abster-se.
O sistema calcula o resultado em tempo real. Se houver empate, o sistema sinaliza para a Liderança dar o "Voto de Minerva" (desempate) e isso é registrado também no log descrito no próximo Requisito Funcional

Requisito Funcional (RF) para a Elaboração da Ata:
A sessão não terá apenas um campo de texto em branco. Ela terá uma "Linha do Tempo" (Event Log).
O sistema deve gerar "Movimentações" automáticas com a hora exata (timestamp) para:
Abertura e Quórum: "14:00 - Sessão iniciada com 45 delegados (Quórum atingido)".
Entrada/Saída: Se um delegado marca que precisou sair, gera o log: "14:30 - Delegado João saiu do plenário"
Resultado de Votações: "15:00 - Proposta X aprovada por 30 votos a favor e 15 contra".
O Secretário terá um campo para inserir "Registros Manuais" rápidos na linha do tempo (Ex: "15:15 - Oração feita pelo Rev. Carlos")

## Presenças integradas a sessão

1. O Crachá Digital (Geração do QR Code)
Em vez de imprimir crachás físicos com código de barras, vamos usar o celular do próprio jovem.
Como funciona: Assim que você aprova a inscrição do usuário para "Delegado Efetivo", o Django gera automaticamente um QR Code único para ele (baseado no ID da inscrição). Ou, para o caso de não ter sido gerado automaticamente, aperta um botão na lista de inscritos.
Na prática: Quando o delegado acessa a "Área do Delegado" (o Hub) pelo celular, o QR Code dele aparece no card da credencial.

1. O Leitor de Plenário (Câmera do Celular)
Você não precisa comprar equipamentos leitores de QR Code ou totens caros.
Como funciona: Você cria uma página oculta no painel de administração chamada "Leitor de Presença". Utilizando uma biblioteca simples de JavaScript (como o html5-qrcode), o sistema acessa a câmera do celular da própria liderança ou de um voluntário da recepção que ficará na porta do auditório.
Na prática: O delegado chega na porta, mostra a tela do celular dele, e o voluntário aponta a câmera.

1. A Lógica de Entrada e Saída (Otimização do Evento)
Para deixar o sistema inteligente e atender à exigência do GTSI de registrar entradas e saídas, o sistema fará uma lógica de "interruptor" (Toggle):
Primeira Leitura (Entrada): O sistema identifica o QR Code, marca presente = True na sessão atual e dispara um registro automático na Linha do Tempo da Ata: "14:15 - O Delegado João Silva entrou no plenário". O leitor na porta pisca em Verde.
Segunda Leitura (Saída): Se o delegado precisar ir ao banheiro ou sair mais cedo, ele passa o QR Code de novo na porta. O sistema entende que ele já estava lá, marca presente = False e gera outro log na ata: "15:30 - O Delegado João Silva retirou-se do plenário". O leitor pisca em Amarelo.
