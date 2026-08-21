import re
import unicodedata
from datetime import datetime

from openpyxl import load_workbook

HEADER_ALIASES = {
    "posicao": ["posicao", "posição"],
    "cod_rca": ["cod_rca", "codrca"],
    "vendedor": ["vendedor"],
    "cod_sup": ["cod_sup", "codsup"],
    "nome_supervisor": ["nome_supervisor", "supervisor", "nome_sup", "nomesupervisor"],
    "codcli": ["codcli", "cod_cli"],
    "fantasia": ["fantasia"],
    "data_pedido": ["data_pedido", "datapedido"],
    "hora_pedido": ["hora_pedido", "horapedido"],
    "vlatend": ["vlatend", "valor_atend", "vl_atend"],
    "codcob": ["codcob", "cod_cob"],
    "obs": ["obs", "observacao", "obs1"],
    "obs2": ["obs2", "observacao2"],
}


def normalizar_cabecalho(h):
    h = str(h or "")
    h = unicodedata.normalize("NFD", h).encode("ascii", "ignore").decode("utf-8")
    h = h.lower().strip()
    h = re.sub(r"[^a-z0-9]+", "_", h).strip("_")
    return h


def mapear_cabecalhos(cabecalhos_brutos):
    mapa = {}
    for bruto in cabecalhos_brutos:
        norm = normalizar_cabecalho(bruto)
        for campo, aliases in HEADER_ALIASES.items():
            if norm in aliases:
                mapa[bruto] = campo
    return mapa


def ler_planilha(arquivo):
    """Lê um arquivo .xlsx (InMemoryUploadedFile ou caminho) e retorna
    uma lista de dicts com as colunas já mapeadas para os nomes internos."""
    wb = load_workbook(arquivo, data_only=True)
    ws = wb.active
    linhas = list(ws.iter_rows(values_only=True))
    if not linhas:
        return []

    cabecalhos = linhas[0]
    mapa = mapear_cabecalhos(cabecalhos)

    resultado = []
    for linha in linhas[1:]:
        row = {}
        for i, valor in enumerate(linha):
            if i >= len(cabecalhos):
                continue
            campo = mapa.get(cabecalhos[i])
            if campo:
                row[campo] = valor
        if any(v not in (None, "") for v in row.values()):
            resultado.append(row)
    return resultado


def gerar_chave(row):
    posicao = row.get("posicao")
    if posicao not in (None, ""):
        return f"pos_{str(posicao).strip()}"
    return f"k_{row.get('codcli')}_{row.get('data_pedido')}_{row.get('hora_pedido')}"


def parse_data(valor):
    if valor in (None, ""):
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if hasattr(valor, "year") and hasattr(valor, "month"):  # já é date
        return valor
    if isinstance(valor, str):
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
            try:
                return datetime.strptime(valor.strip(), fmt).date()
            except ValueError:
                continue
    return None


def classificar_heuristico(obs_texto):
    t = (obs_texto or "").lower()
    if "recompo" in t:
        return "recomposicao"
    if "prazo" in t:
        return "prazo"
    return "tratar"


def categorizar(row, suporte_infra_nome=None):
    """Aplica a regra de negócio e devolve (categoria, motivo, sugestao_atribuicao)."""
    codcob = str(row.get("codcob") or "").strip().lower()
    obs2 = str(row.get("obs2") or "").strip().lower()
    obs_texto = f"{row.get('obs') or ''} {row.get('obs2') or ''}"

    if "infraecommerce" in obs2:
        return "tratar", "obs2 = infraecommerce", suporte_infra_nome
    if codcob == "bk":
        return "liberar", "codcob = BK", None
    if codcob == "dh":
        return "liberar", "codcob = DH", None
    if codcob == "bnf":
        return "tratar", "codcob = BNF", None
    if codcob == "dep":
        return classificar_heuristico(obs_texto), "codcob = DEP (heurística)", None
    return "sem_categoria", "codcob não mapeado", None
