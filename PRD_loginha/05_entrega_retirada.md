# Etapa 05 — Entrega e retirada

## Objetivo

Permitir que cada produto especifique se aceita retirada presencial, envio pelos Correios, ou ambos. No checkout, usuário escolhe o modo e (se for envio) informa endereço. Implementa cálculo de frete via Melhor Envio. Adiciona QR Code de retirada para confirmação presencial.

## Pré-requisitos

- Etapa 04 concluída

## Modelos novos

### `EnderecoEntrega`

| Campo | Tipo | Notas |
|---|---|---|
| `pedido` | OneToOneField(Pedido, on_delete=CASCADE, related_name='endereco') | |
| `cep` | CharField(9) | Formato `00000-000` |
| `logradouro` | CharField(200) | |
| `numero` | CharField(20) | |
| `complemento` | CharField(100, blank=True) | |
| `bairro` | CharField(100) | |
| `cidade` | CharField(100) | |
| `uf` | CharField(2) | |
| `referencia` | CharField(255, blank=True) | |

### `PontoRetirada`

Locais cadastrados onde pedidos podem ser retirados. Liderança gerencia.

| Campo | Tipo | Notas |
|---|---|---|
| `nome` | CharField(150) | Ex.: "Igreja Central — Garanhuns" |
| `endereco_completo` | TextField | Endereço para mostrar ao usuário |
| `instrucoes` | TextField(blank=True) | "Falar com fulano" |
| `dias_funcionamento` | CharField(100, blank=True) | "Seg a Sex 14h–18h" |
| `evento` | FK(Evento, null=True, blank=True, on_delete=SET_NULL) | Se for retirada no evento |
| `ativo` | BooleanField(default=True) | |

### Campos novos em `Pedido` (alterar via migration)

| Campo | Tipo | Notas |
|---|---|---|
| `ponto_retirada` | FK(PontoRetirada, null=True, blank=True, on_delete=SET_NULL) | |
| `codigo_rastreio` | CharField(50, blank=True) | Correios |
| `data_envio` | DateTimeField(null=True, blank=True) | |
| `data_entrega` | DateTimeField(null=True, blank=True) | |
| `qr_code_retirada` | CharField(50, blank=True, unique=True, db_index=True, null=True) | Token único |

### Campos novos em `Produto`

| Campo | Tipo | Notas |
|---|---|---|
| `aceita_retirada` | BooleanField(default=True) | |
| `aceita_envio` | BooleanField(default=False) | |
| `peso_gramas` | PositiveIntegerField(default=200) | Para frete |
| `dimensoes_cm` | CharField(20, blank=True) | Ex.: "20x30x5" |

## Constantes

Já cobertas: `ENTREGA_RETIRADA`, `ENTREGA_CORREIOS` (Etapa 03).

Adicionar:

```python
# Tamanho máximo do pacote para Correios
FRETE_PESO_MAX_GRAMAS = 30000  # 30 kg

# Provedores de frete (extensível)
FRETE_PROVEDOR_MELHOR_ENVIO = 'melhor_envio'
FRETE_PROVEDOR_FIXO = 'fixo'
FRETE_PROVEDOR_GRATIS = 'gratis'
```

## Service: `apps/loja/services/frete.py`

```python
def calcular_frete(cep_destino: str, itens: list) -> list[dict]:
    """Retorna lista de opções de frete:
       [{'servico': 'PAC', 'prazo_dias': 7, 'preco': Decimal('15.50')}, ...]

    Cada item da lista de entrada: {'peso': int, 'dimensoes': str, 'quantidade': int, 'valor': Decimal}.
    """
```

**Decisão técnica:** começar com integração **Melhor Envio** (mais simples que API direta Correios). Cadastro gratuito, e oferece tabela de preços ABF + Correios + Jadlog.

Alternativa de fallback (se Melhor Envio for complexo): **frete fixo configurável por região** (uma tabela CEP → valor).

## Cálculo de frete no checkout

No `iniciar.html` do checkout (Etapa 03), adicionar:

- Campo CEP com máscara
- Botão "Calcular frete" (HTMX) → atualiza fragmento com opções
- Radio para escolher serviço (PAC, SEDEX, etc.)
- Valor do frete soma no total

## Geração do QR Code de retirada

Quando pedido muda para `PRONTO` e `modo_entrega == RETIRADA`:

```python
import secrets

def gerar_qr_retirada(pedido):
    if pedido.qr_code_retirada:
        return pedido.qr_code_retirada
    pedido.qr_code_retirada = secrets.token_urlsafe(16)
    pedido.save(update_fields=['qr_code_retirada'])
    return pedido.qr_code_retirada
```

QR Code é exibido no `pedido/detalhe.html` quando `status == PRONTO`. Liderança escaneia com leitor de QR para confirmar entrega.

## Reaproveitar leitor de QR já existente

O projeto já usa `html5-qrcode` para credenciais de sessão. Reutilizar a mesma página/leitor com novo endpoint:

```python
path('gestao/retirada/scan/<str:token>/', gestao.validar_retirada_qr, name='validar_retirada_qr'),
```

Validação:
- Busca pedido por `qr_code_retirada`
- Se encontrado e `status == PRONTO`: marca como `ENTREGUE`, salva `data_entrega = now`
- Senão: retorna erro

## Templates novos

```
templates/loja/
├── checkout/
│   └── _opcoes_frete.html     # Fragmento HTMX com opções
├── pedido/
│   └── _qr_retirada.html      # QR para o usuário mostrar na retirada
└── gestao/
    └── retirada_scan.html     # Leitor de QR para liderança
```

## Views novas

```python
# apps/loja/urls.py (adicionar)
urlpatterns += [
    path('checkout/calcular-frete/', checkout.calcular_frete, name='checkout_calcular_frete'),
    path('gestao/retirada/scan/', gestao.scan_retirada, name='scan_retirada'),
    path('gestao/retirada/scan/<str:token>/validar/', gestao.validar_retirada_qr, name='validar_retirada_qr'),
    path('gestao/pedido/<int:pedido_id>/marcar-pronto/', gestao.marcar_pronto, name='marcar_pronto'),
    path('gestao/pedido/<int:pedido_id>/marcar-enviado/', gestao.marcar_enviado, name='marcar_enviado'),
]
```

## Variáveis de ambiente

```env
# Melhor Envio
MELHOR_ENVIO_TOKEN=seu_token_aqui
MELHOR_ENVIO_SANDBOX=True
```

Documentação: https://docs.melhorenvio.com.br

## Critérios de aceite

- [ ] Liderança configura por produto se aceita retirada, envio, ou ambos
- [ ] Liderança cadastra pontos de retirada
- [ ] No checkout, se todos os produtos aceitam retirada, mostra opções de ponto de retirada
- [ ] No checkout, se todos os produtos aceitam envio, mostra campo de CEP
- [ ] Se produtos do carrinho são incompatíveis (ex.: um só retirada, outro só envio), exibe aviso
- [ ] Cálculo de frete via HTMX retorna lista de opções
- [ ] Frete escolhido aparece no total
- [ ] Pedido pago + retirada: liderança consegue marcar `PRONTO`, sistema gera QR Code
- [ ] Usuário vê QR Code em `/loja/pedido/<id>/`
- [ ] Liderança consegue scanear QR no `/loja/gestao/retirada/scan/` → pedido vai para `ENTREGUE`
- [ ] Pedido pago + envio: liderança consegue marcar `ENVIADO` informando código de rastreio
- [ ] E-mail de notificação para cada mudança de status (pronto, enviado, entregue)
- [ ] Mobile: QR Code legível, scanner funciona

## Casos de uso cobertos

- CU-02 completo (retirada presencial)
- Compras com envio para fora da cidade

## Estimativa

1 dia (8 horas com Claude Code) — usando Melhor Envio. Mais 0,5 dia se a integração de frete vier com complicações.

## Pontos de atenção

1. **Melhor Envio token** vem de cadastro gratuito em melhorenvio.com.br. Cliente sandbox separado para testes.
2. **QR Code de retirada**: token aleatório (`secrets.token_urlsafe(16)`) — 22 caracteres seguros.
3. **Frete grátis para retirada**: se modo for `RETIRADA`, `valor_frete = 0` sempre.
4. **Endereço editável após pedido**: NÃO permitir editar depois de pago. Permitir até `AGUARDANDO_PAGAMENTO`.
5. **Status `PRONTO` exige produto físico em mãos** — não é automático. Liderança marca manualmente.
6. **Pacotes acima de 30 kg**: bloquear envio pelos Correios (mostrar mensagem).
