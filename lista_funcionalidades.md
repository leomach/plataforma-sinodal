# Lista de Funcionalidades — Loja da Plataforma Sinodal

> Lista de requisitos possíveis para planejamento. Não é um roadmap — é um inventário do que pode ser construído.

---

## Catálogo de Produtos

- Produto com nome, descrição, imagens e preço
- Variações de produto (tamanho, cor, modelo)
- Estoque por variação (com alerta de baixo estoque)
- Produtos vinculados a evento (camiseta do acampamento X)
- Produto visível só para inscritos em determinado evento
- Produto visível só para sócios / liderança
- Ordenação e destaque no catálogo
- Categoria de produto (vestuário, livros, materiais, outros)

---

## Carrinho e Checkout

- Adicionar/remover itens sem recarregar a página (HTMX)
- Carrinho persistido por usuário logado
- Resumo do pedido com valor total
- Campo de observação no pedido (ex.: número de uniforme, dedicatória)
- Finalizar pedido com PIX (0% de taxa) ou cartão via InfinitePay
- Comprovante de pedido por e-mail
- Histórico de pedidos do usuário

---

## Pré-venda

### Fases do produto
- Produto passa por fases: **Em breve → Pré-venda → Venda normal → Encerrado**
- Cada fase tem data de início e fim configurável
- Transição de fase automática por data ou manual pela liderança
- Preço de pré-venda pode ser diferente do preço de venda normal (desconto early bird)

### Estoque e reserva
- Pré-venda tem cota própria separada do estoque de venda normal
  - Ex.: 50 unidades disponíveis na pré-venda; quando esgotar, abre venda normal com o restante
- Pedidos de pré-venda reservam unidades imediatamente (não são confirmados após a produção)
- Ao encerrar a pré-venda, liderança vê total exato de pedidos por variação para definir quantidade de produção
- Estoque de venda normal é alimentado manualmente após chegada do produto

### Pagamento na pré-venda
- Usuário paga no ato da pré-venda (reserva garantida com pagamento)
- Pedido fica com status **"Aguardando produção"** até produto estar disponível
- Quando produto chega, status muda para **"Pronto para retirada/envio"** e usuário recebe notificação
- Em caso de cancelamento da pré-venda (produto não produzido), reembolso manual registrado no sistema

### Visibilidade
- Contador regressivo até abertura da pré-venda
- Contador de unidades restantes na pré-venda
- Produto aparece como "Em breve" no catálogo antes da pré-venda abrir
- Lista de espera quando pré-venda esgota (usuário é notificado se abrir nova cota)

---

## Anúncios e Comunicação

- Banner/destaque de produto na página inicial e no hub
- Aviso de lançamento de produto novo para todos os usuários
- Produto "em breve" com lista de espera (usuário cadastra interesse)
- Notificação para usuários na lista de espera quando produto disponível
- Painel de anúncios da loja visível em todas as páginas da plataforma
- E-mail marketing para inscritos em evento sobre produtos relacionados

---

## Modalidades específicas da UMP

- **Rifa**: produto do tipo "número de rifa" com geração de bilhetes e sorteio
- **Vaquinha / arrecadação**: meta de valor com progresso visível (ex.: missão, reforma)
- **Doação livre**: valor definido pelo próprio usuário

---

## Gestão (Backoffice — Liderança)

- Criar, editar e arquivar produtos
- Gerenciar fases do produto (Em breve / Pré-venda / Venda normal / Encerrado)
- Ver todos os pedidos com filtros (status, fase, evento, data, usuário)
- Atualizar status do pedido (aguardando produção, pronto, retirado/enviado)
- Relatório de pré-venda: total pedido por variação (base para produção)
- Confirmação manual de pagamento (para casos de erro)
- Exportar pedidos para planilha (CSV)
- Controle de estoque: entrada, saída, ajuste manual
- Histórico de vendas com total arrecadado por produto/período
- Relatório de pedidos por evento

---

## Entrega e Retirada

- Produto para retirada presencial (no evento ou sede)
- Produto com envio pelos Correios (com cálculo de frete via CEP)
- Agendamento de retirada (usuário escolhe dia/turno)
- QR Code de retirada (funcionário escaneia para confirmar entrega)

---

## Funcionalidades de Plataforma

- Emblema automático para quem compra produto específico (integração com app emblemas)
- Histórico de compras visível no perfil do usuário
