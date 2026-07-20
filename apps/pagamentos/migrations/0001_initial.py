from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='TransacaoInfinitePay',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_nsu', models.CharField(db_index=True, max_length=100, unique=True, verbose_name='Transaction NSU')),
                ('invoice_slug', models.CharField(blank=True, db_index=True, max_length=100, verbose_name='Invoice Slug')),
                ('order_nsu', models.CharField(db_index=True, max_length=100, verbose_name='Order NSU')),
                ('amount_centavos', models.PositiveIntegerField(verbose_name='Valor em centavos')),
                ('paid_amount_centavos', models.PositiveIntegerField(verbose_name='Valor pago em centavos')),
                ('capture_method', models.CharField(blank=True, max_length=20, verbose_name='Método')),
                ('installments', models.PositiveSmallIntegerField(default=1, verbose_name='Parcelas')),
                ('receipt_url', models.URLField(blank=True, max_length=500, verbose_name='URL do comprovante')),
                ('payload_completo', models.JSONField(blank=True, default=dict, verbose_name='Payload completo')),
                ('valor_validado', models.BooleanField(default=False, verbose_name='Valor validado pelo handler')),
                ('payment_check_validado', models.BooleanField(default=False, verbose_name='Confirmado via payment_check')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Transação InfinitePay',
                'verbose_name_plural': 'Transações InfinitePay',
                'ordering': ['-criado_em'],
            },
        ),
    ]
