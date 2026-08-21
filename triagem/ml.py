"""
Classificador local para a triagem dos pedidos com codcob=DEP.
Não depende de nenhuma API paga: treina um modelo pequeno (TF-IDF + Regressão
Logística) usando os próprios pedidos que já foram classificados manualmente
no sistema (categoria_manual=True), e usa esse modelo pra sugerir a categoria
dos pedidos novos.

Requer: scikit-learn e joblib (pip install scikit-learn joblib)
"""
import os

from django.conf import settings

MODELO_PATH = os.path.join(settings.BASE_DIR, "triagem", "modelo_triagem.joblib")

CATEGORIAS_TREINAVEIS = ["prazo", "recomposicao", "tratar"]

MIN_EXEMPLOS_POR_CLASSE = 5  # abaixo disso o modelo tende a "chutar"


def _texto_pedido(pedido):
    return f"{pedido.obs or ''} {pedido.obs2 or ''}".strip()


def modelo_existe():
    return os.path.exists(MODELO_PATH)


def treinar():
    """Treina o modelo com os pedidos DEP já classificados manualmente.
    Retorna um dict com o resultado (ok, motivo, quantidade por classe)."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    import joblib

    from .models import Pedido

    exemplos = Pedido.objects.filter(
        categoria_manual=True, codcob__iexact="dep", categoria__in=CATEGORIAS_TREINAVEIS
    )

    contagem = {c: exemplos.filter(categoria=c).count() for c in CATEGORIAS_TREINAVEIS}
    classes_prontas = [c for c, n in contagem.items() if n >= MIN_EXEMPLOS_POR_CLASSE]

    if len(classes_prontas) < 2:
        return {
            "ok": False,
            "motivo": (
                "Ainda não há exemplos manuais suficientes pra treinar. "
                f"Corrija manualmente ao menos {MIN_EXEMPLOS_POR_CLASSE} pedidos DEP "
                "em pelo menos 2 categorias diferentes (prazo / recomposição / tratar) "
                "e tente treinar de novo."
            ),
            "contagem": contagem,
        }

    textos = [_texto_pedido(p) for p in exemplos]
    rotulos = [p.categoria for p in exemplos]

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(min_df=1, ngram_range=(1, 2), lowercase=True)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    pipeline.fit(textos, rotulos)
    joblib.dump(pipeline, MODELO_PATH)

    return {"ok": True, "motivo": "Modelo treinado com sucesso.", "contagem": contagem, "total": len(textos)}


def prever(pedidos):
    """Recebe uma lista de Pedido e devolve {pedido_id: categoria_prevista}."""
    import joblib

    if not modelo_existe():
        return {}

    pipeline = joblib.load(MODELO_PATH)
    textos = [_texto_pedido(p) for p in pedidos]
    if not textos:
        return {}

    previstos = pipeline.predict(textos)
    return {p.id: cat for p, cat in zip(pedidos, previstos)}
