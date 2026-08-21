from django.db import models
from django.utils import timezone


class SuporteMembro(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Membro de suporte"
        verbose_name_plural = "Equipe de suporte"

    def __str__(self):
        return self.nome


class Pedido(models.Model):
    CATEGORIA_CHOICES = [
        ("liberar", "Liberar"),
        ("tratar", "Tratar"),
        ("recomposicao", "Recomposição"),
        ("prazo", "Prazo"),
        ("sem_categoria", "Sem categoria"),
    ]

    # chave usada para o merge entre importações (posicao, ou fallback)
    chave = models.CharField(max_length=150, unique=True)

    posicao = models.CharField(max_length=50, blank=True, null=True)
    cod_rca = models.CharField(max_length=20, blank=True, null=True)
    vendedor = models.CharField(max_length=150, blank=True, null=True)
    cod_sup = models.CharField(max_length=20, blank=True, null=True)
    nome_supervisor = models.CharField(max_length=150, blank=True, null=True)
    codcli = models.CharField(max_length=20, blank=True, null=True)
    fantasia = models.CharField(max_length=150, blank=True, null=True)
    data_pedido = models.DateField(blank=True, null=True)
    hora_pedido = models.CharField(max_length=20, blank=True, null=True)
    vlatend = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    codcob = models.CharField(max_length=10, blank=True, null=True)
    obs = models.TextField(blank=True, null=True)
    obs2 = models.TextField(blank=True, null=True)

    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default="sem_categoria")
    categoria_manual = models.BooleanField(default=False)
    motivo_categoria = models.CharField(max_length=200, blank=True, null=True)
    classificado_ia = models.BooleanField(default=False)

    atribuido = models.ForeignKey(
        SuporteMembro, null=True, blank=True, on_delete=models.SET_NULL, related_name="pedidos"
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data_pedido"]

    def __str__(self):
        return f"{self.fantasia or self.codcli} (pos. {self.posicao})"

    def dias_em_aberto(self):
        if not self.data_pedido:
            return None
        return (timezone.localdate() - self.data_pedido).days

    def atrasado(self):
        dias = self.dias_em_aberto()
        return dias is not None and dias > 2
