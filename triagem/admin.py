from django.contrib import admin

from .models import Pedido, SuporteMembro


@admin.register(SuporteMembro)
class SuporteMembroAdmin(admin.ModelAdmin):
    list_display = ("nome",)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        "posicao", "fantasia", "codcli", "codcob", "categoria",
        "categoria_manual", "atribuido", "data_pedido",
    )
    list_filter = ("categoria", "codcob", "atribuido")
    search_fields = ("fantasia", "codcli", "vendedor", "nome_supervisor", "posicao")
