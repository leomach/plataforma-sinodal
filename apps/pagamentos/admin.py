from django.contrib import admin

from .models import TransacaoInfinitePay


@admin.register(TransacaoInfinitePay)
class TransacaoInfinitePayAdmin(admin.ModelAdmin):
    list_display = (
        'order_nsu',
        'transaction_nsu',
        'paid_amount_centavos',
        'capture_method',
        'payment_check_validado',
        'valor_validado',
        'criado_em',
    )
    list_filter = ('capture_method', 'payment_check_validado', 'valor_validado', 'criado_em')
    search_fields = ('order_nsu', 'transaction_nsu', 'invoice_slug')
    readonly_fields = (
        'transaction_nsu',
        'invoice_slug',
        'order_nsu',
        'amount_centavos',
        'paid_amount_centavos',
        'capture_method',
        'installments',
        'receipt_url',
        'payload_completo',
        'valor_validado',
        'payment_check_validado',
        'criado_em',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
