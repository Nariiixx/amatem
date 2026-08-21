from django.core.management.base import BaseCommand

from triagem.ml import treinar


class Command(BaseCommand):
    help = "Treina o classificador local de triagem (pedidos codcob=DEP) com os exemplos já corrigidos manualmente."

    def handle(self, *args, **options):
        resultado = treinar()
        if resultado["ok"]:
            self.stdout.write(self.style.SUCCESS(resultado["motivo"]))
            self.stdout.write(f"Exemplos usados: {resultado['contagem']}")
        else:
            self.stdout.write(self.style.WARNING(resultado["motivo"]))
            self.stdout.write(f"Exemplos disponíveis hoje: {resultado['contagem']}")
