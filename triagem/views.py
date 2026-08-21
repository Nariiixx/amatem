from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Pedido, SuporteMembro
from .utils import categorizar, gerar_chave, ler_planilha, parse_data

CATEGORIAS_VALIDAS = {"liberar", "tratar", "recomposicao", "prazo", "sem_categoria"}


@login_required
def dashboard(request):
    pedidos = Pedido.objects.select_related("atribuido").all()

    categoria = request.GET.get("categoria", "todos")
    busca = request.GET.get("q", "").strip()
    so_atrasados = request.GET.get("atrasados") == "1"

    if categoria != "todos" and categoria in CATEGORIAS_VALIDAS:
        pedidos = pedidos.filter(categoria=categoria)

    if busca:
        pedidos = pedidos.filter(
            Q(fantasia__icontains=busca)
            | Q(codcli__icontains=busca)
            | Q(vendedor__icontains=busca)
            | Q(nome_supervisor__icontains=busca)
        )

    hoje = timezone.localdate()
    limite = hoje - timezone.timedelta(days=2)

    if so_atrasados:
        pedidos = pedidos.filter(data_pedido__lt=limite)

    todos = Pedido.objects.all()
    contagens = {
        "todos": todos.count(),
        "liberar": todos.filter(categoria="liberar").count(),
        "tratar": todos.filter(categoria="tratar").count(),
        "recomposicao": todos.filter(categoria="recomposicao").count(),
        "prazo": todos.filter(categoria="prazo").count(),
        "sem_categoria": todos.filter(categoria="sem_categoria").count(),
    }
    atrasados_count = todos.filter(data_pedido__lt=limite).count()

    contexto = {
        "pedidos": pedidos,
        "contagens": contagens,
        "atrasados_count": atrasados_count,
        "suportes": SuporteMembro.objects.all(),
        "categoria_atual": categoria,
        "busca": busca,
        "so_atrasados": so_atrasados,
        "hoje": hoje,
    }
    return render(request, "triagem/dashboard.html", contexto)


@login_required
@require_POST
def importar_planilha(request):
    arquivo = request.FILES.get("arquivo")
    if not arquivo:
        messages.error(request, "Selecione um arquivo antes de enviar.")
        return redirect("triagem_dashboard")

    try:
        linhas = ler_planilha(arquivo)
    except Exception:
        messages.error(request, "Não foi possível ler essa planilha. Confirme se é um arquivo .xlsx válido.")
        return redirect("triagem_dashboard")

    suporte_infra = (
        SuporteMembro.objects.filter(nome__icontains="ívea").first()
        or SuporteMembro.objects.filter(nome__icontains="ivea").first()
    )

    chaves_do_arquivo = set()

    for row in linhas:
        chave = gerar_chave(row)
        chaves_do_arquivo.add(chave)

        categoria, motivo, sugestao = categorizar(row, suporte_infra.nome if suporte_infra else None)

        campos = {
            "posicao": row.get("posicao"),
            "cod_rca": row.get("cod_rca"),
            "vendedor": row.get("vendedor"),
            "cod_sup": row.get("cod_sup"),
            "nome_supervisor": row.get("nome_supervisor"),
            "codcli": row.get("codcli"),
            "fantasia": row.get("fantasia"),
            "data_pedido": parse_data(row.get("data_pedido")),
            "hora_pedido": str(row.get("hora_pedido") or ""),
            "vlatend": row.get("vlatend") or None,
            "codcob": row.get("codcob"),
            "obs": row.get("obs"),
            "obs2": row.get("obs2"),
            "motivo_categoria": motivo,
        }

        existente = Pedido.objects.filter(chave=chave).first()

        if existente:
            # se o usuário já classificou manualmente, não sobrescreve a categoria
            if not existente.categoria_manual:
                campos["categoria"] = categoria
            for campo, valor in campos.items():
                setattr(existente, campo, valor)
            if not existente.atribuido and sugestao:
                membro = SuporteMembro.objects.filter(nome=sugestao).first()
                if membro:
                    existente.atribuido = membro
            existente.save()
        else:
            campos["chave"] = chave
            campos["categoria"] = categoria
            novo = Pedido.objects.create(**campos)
            if sugestao:
                membro = SuporteMembro.objects.filter(nome=sugestao).first()
                if membro:
                    novo.atribuido = membro
                    novo.save()

    # remove da base quem não veio mais no arquivo novo
    removidos, _ = Pedido.objects.exclude(chave__in=chaves_do_arquivo).delete()

    messages.success(
        request,
        f"{len(linhas)} pedido(s) processado(s). {removidos} removido(s) por não constarem mais na planilha.",
    )
    return redirect("triagem_dashboard")


@login_required
@require_POST
def atualizar_pedido(request, pedido_id):
    pedido = Pedido.objects.filter(id=pedido_id).first()
    if not pedido:
        return JsonResponse({"ok": False, "erro": "Pedido não encontrado."}, status=404)

    categoria = request.POST.get("categoria")
    if categoria:
        if categoria not in CATEGORIAS_VALIDAS:
            return JsonResponse({"ok": False, "erro": "Categoria inválida."}, status=400)
        pedido.categoria = categoria
        pedido.categoria_manual = True

    if "atribuido_id" in request.POST:
        atribuido_id = request.POST.get("atribuido_id")
        pedido.atribuido = SuporteMembro.objects.filter(id=atribuido_id).first() if atribuido_id else None

    pedido.save()
    return JsonResponse({"ok": True})


@login_required
@require_POST
def treinar_modelo_local(request):
    """Treina o classificador local com os pedidos DEP já corrigidos manualmente.
    Gratuito — não chama nenhuma API externa."""
    from .ml import treinar

    resultado = treinar()
    return JsonResponse(resultado)


@login_required
@require_POST
def classificar_modelo_local(request):
    """Classifica os pedidos DEP pendentes usando o modelo local treinado
    (scikit-learn). Gratuito e roda offline. Se o modelo ainda não foi
    treinado, não faz nada e avisa."""
    from .ml import modelo_existe, prever

    if not modelo_existe():
        return JsonResponse(
            {
                "ok": False,
                "erro": "O modelo local ainda não foi treinado. Corrija manualmente alguns pedidos "
                "DEP e use o botão 'Treinar modelo' antes.",
            },
            status=400,
        )

    pendentes = list(
        Pedido.objects.filter(categoria_manual=False, classificado_ia=False, codcob__iexact="dep")
    )
    if not pendentes:
        return JsonResponse({"ok": True, "atualizados": 0})

    previsoes = prever(pendentes)
    atualizados = 0
    for pedido_id, categoria in previsoes.items():
        Pedido.objects.filter(id=pedido_id).update(
            categoria=categoria,
            classificado_ia=True,
            motivo_categoria="codcob = DEP (classificado pelo modelo local)",
        )
        atualizados += 1

    return JsonResponse({"ok": True, "atualizados": atualizados})
