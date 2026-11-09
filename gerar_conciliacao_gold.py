"""Gera o gold fato_conciliacao_multi_kmm (Spark SQL, padrao datalake-glue) a partir de conciliacao_multi_kmm.sql (Athena/Trino).
Fonte da verdade continua sendo conciliacao_multi_kmm.sql; este script traduz e grava:
  gold_contab_manual/fato_conciliacao_multi_kmm.sql   (Spark, {env}_, com CAST nas 105 colunas)
  <scratchpad>/conciliacao_teste_athena.sql           (variante Trino so para teste: mesmas trocas, sem as funcoes Spark)
Uso: python gerar_conciliacao_gold.py [pasta_de_teste]
"""
import json, os, re, subprocess, sys, time, tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
FONTE = os.path.join(AQUI, "conciliacao_multi_kmm.sql")
SAIDA = os.path.join(AQUI, "gold_contab_manual", "fato_conciliacao_multi_kmm.sql")
TESTE = os.path.join(sys.argv[1] if len(sys.argv) > 1 else AQUI, "conciliacao_teste_athena.sql")
ENV = dict(os.environ, AWS_DEFAULT_OUTPUT="json", AWS_DEFAULT_REGION="us-east-1")


# ---------- utilidades de texto ----------
def strip_comments(s):
    out, i, n, q = [], 0, len(s), False
    while i < n:
        c = s[i]
        if q:
            out.append(c)
            if c == "'":
                if i + 1 < n and s[i + 1] == "'":
                    out.append("'"); i += 1
                else:
                    q = False
        elif c == "'":
            q = True; out.append(c)
        elif c == "-" and s.startswith("--", i):
            while i < n and s[i] != "\n":
                i += 1
            continue
        else:
            out.append(c)
        i += 1
    txt = "".join(out)
    return re.sub(r"[ \t]+\n", "\n", re.sub(r"\n\s*\n+", "\n", txt))


def scan(s):
    """gera (indice, char, profundidade, dentro_de_string) ignorando conteudo de strings"""
    d, q, i, n = 0, False, 0, len(s)
    while i < n:
        c = s[i]
        if q:
            if c == "'":
                if i + 1 < n and s[i + 1] == "'":
                    i += 2; continue
                q = False
            yield i, c, d, True
        elif c == "'":
            q = True
            yield i, c, d, True
        else:
            if c == "(":
                yield i, c, d, False
                d += 1
            elif c == ")":
                d -= 1
                yield i, c, d, False
            else:
                yield i, c, d, False
        i += 1


def split_args(s):
    """separa por virgulas de profundidade 0 (s = texto dentro dos parenteses)"""
    args, last = [], 0
    for i, c, d, qs in scan(s):
        if c == "," and d == 0 and not qs:
            args.append(s[last:i]); last = i + 1
    args.append(s[last:])
    return args


def close_paren(s, start):
    """indice do ')' que fecha o '(' em s[start]"""
    for i, c, d, qs in scan(s[start:]):
        if c == ")" and d == 0 and not qs:
            return start + i
    raise ValueError("parenteses sem fechar")


def replace_call(s, name, fn, flags=re.I):
    """substitui chamadas name(args) por fn(args_list) (nao aninhadas no proprio nome, trata uma por vez)"""
    pat = re.compile(r"(?<![A-Za-z0-9_])" + name + r"\s*\(", flags)
    pos = 0
    while True:
        m = pat.search(s, pos)
        if not m:
            return s
        op = m.end() - 1
        cl = close_paren(s, op)
        novo = fn(split_args(s[op + 1:cl]))
        s = s[:m.start()] + novo + s[cl + 1:]
        pos = m.start() + 1


# ---------- trocas comuns (Trino e Spark) ----------
PAINEL_VIEW = """painel_view AS (
    SELECT sk_cliente, sk_documento, sk_cooperado, sk_filial, sk_tipo_operacao, con_codigo, car_codigo_carga_embarcador, cte, data_emissao,
           vlr_receita_bruta, vlr_receita_liquida, vlr_prest_servico, vlr_a_receber, vlr_total_merc, vlr_adv, vlr_gris, vei_placa,
           inicio_da_prestacao, fim_da_prestacao, ccv_descricao, ccv_codigo, codfil,
           CASE WHEN tipo_operacao_anulacao LIKE '%ANULA%' THEN 'S' ELSE 'N' END AS operacao_anulacao,
           dt_min_entrega, con_status, car_situacao, ped_situacao, custo_bruto, tipo_documento, cooperado, tipo_operacao, custo_descarga,
           custo_estadia_rateio, custo_carga, custo_pedagio_extra, custo_loggi, grupo_pessoa_tratado, tipo_cooperado, filial
    FROM ENV_gold.fato_operacional
    WHERE con_status IN ('A') AND car_situacao NOT IN (18, 13) AND ped_situacao <> 2
      AND NOT (tipo_operacao_anulacao LIKE '%CIOT CANCELADO%')
      AND NOT (tipo_operacao_anulacao LIKE '%TRANSBORDO%' OR tipo_operacao_anulacao LIKE '%REUTILIZACAO%'
               OR (tipo_operacao_anulacao LIKE '%REPASSE%' AND tipo_documento = 'CT-e'))
      AND (oco_anulacao IS NULL OR oco_anulacao = 0) AND mod_abreviacao IS NOT NULL
      AND mod_abreviacao NOT IN ('DV', 'OST') AND tipo_documento IS NOT NULL AND tipo_documento NOT IN ('CV', 'OST', 'NDA', 'DV')
      AND ((has_true = 1 AND flag_anulacao = true AND con_codigo = max_con_anulacao)
           OR (has_true = 0 AND (flag_anulacao = false OR flag_anulacao IS NULL)))
),"""


def comum(s, env):
    s = strip_comments(s)
    # a view do painel nao pode ser lida pelo job Spark: a regra dela vira CTE (mesma regra da ponte lancamento x documento x carga)
    assert s.lstrip().upper().startswith("WITH")
    i = s.upper().index("WITH") + 4
    s = s[:i] + "\n" + PAINEL_VIEW.replace("ENV_gold", env + "_gold") + s[i:]
    s = s.replace("prd_gold.vw_fato_operacional_painel_filial", "painel_view")
    for sch in ("gold", "bronze", "silver"):
        s = s.replace("prd_" + sch + ".", env + "_" + sch + ".")
    # ORDER BY: Spark ordena NULL primeiro no ASC, o Trino por ultimo; explicita NULLS LAST
    # (a ultima ORDER BY da consulta, global, e removida)
    ult = [m.start() for m in re.finditer(r"\bORDER\s+BY\b", s, re.I)][-1]
    assert s[ult:].upper().count("(") == 0 or True
    s = s[:ult].rstrip()
    pos = 0
    while True:
        m = re.compile(r"\bORDER\s+BY\b", re.I).search(s, pos)
        if not m:
            break
        ini = m.end()
        fim = None
        for i, c, d, qs in scan(s[ini:]):
            if c == ")" and d < 0 and not qs:
                fim = ini + i; break
        if fim is None:
            fim = len(s)
        itens = split_args(s[ini:fim])
        novos = []
        for it in itens:
            t = it.strip()
            if re.search(r"\bNULLS\s+(FIRST|LAST)\b", t, re.I) or re.search(r"\bDESC$", t, re.I):
                novos.append(t)
            else:
                novos.append(re.sub(r"\s+ASC$", "", t, flags=re.I) + " NULLS LAST")
        s = s[:ini] + " " + ", ".join(novos) + s[fim:]
        pos = ini + 1
    return s


# ---------- Spark ----------
def spark(s):
    s = re.sub(r"CAST\(ARRAY\[\]\s+AS\s+ARRAY\(varchar\)\)", "CAST(array() AS ARRAY<STRING>)", s, flags=re.I)
    s = re.sub(r"ARRAY\[(.*?)\]", r"array(\1)", s)
    s = re.sub(r"(?<![A-Za-z0-9_])try_cast\s*\(", "CAST(", s, flags=re.I)
    s = re.sub(r"\bAS\s+varchar\b", "AS STRING", s, flags=re.I)

    def dd(a):
        assert a[0].strip().lower() == "'day'", a[0]
        return "datediff(%s, %s)" % (a[2].strip(), a[1].strip())
    s = replace_call(s, "date_diff", dd)
    s = replace_call(s, "array_agg", lambda a: "array_sort(collect_set(%s))" % re.sub(r"^\s*DISTINCT\s+", "", a[0], flags=re.I) if re.match(r"\s*DISTINCT\s", a[0], re.I) else (_ for _ in ()).throw(ValueError("array_agg sem DISTINCT")))
    s = replace_call(s, "contains", lambda a: "array_contains(%s, %s)" % (a[0].strip(), a[1].strip()))
    # split_part so existe no Spark >= 3.3: usa split()[n-1] (o separador aqui e um caractere simples, sem regex)
    def sp(a):
        assert re.fullmatch(r"\d+", a[2].strip()) and re.fullmatch(r"'[-_,;|]'", a[1].strip()), a
        return "split(%s, %s)[%d]" % (a[0].strip(), a[1].strip(), int(a[2]) - 1)
    s = replace_call(s, "split_part", sp)
    # GREATEST: o Trino devolve NULL se algum argumento for NULL; o Spark ignora os NULL. Preserva o comportamento do Trino.
    def gr(a):
        cond = " OR ".join("(%s) IS NULL" % x.strip() for x in a)
        return "CASE WHEN %s THEN NULL ELSE greatest_ok(%s) END" % (cond, ", ".join(x.strip() for x in a))
    s = replace_call(s, "greatest", gr).replace("greatest_ok(", "greatest(")
    return s


# ---------- schema vivo p/ CAST final ----------
def athena(sql):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump({"QueryString": sql, "WorkGroup": "cootravale-s3-athena", "QueryExecutionContext": {"Database": "hml_gold"}}, f)
    qid = json.loads(subprocess.run(["aws", "athena", "start-query-execution", "--cli-input-json", "file://" + f.name], capture_output=True, text=True, env=ENV).stdout)["QueryExecutionId"]
    while True:
        st = json.loads(subprocess.run(["aws", "athena", "get-query-execution", "--query-execution-id", qid], capture_output=True, text=True, env=ENV).stdout)["QueryExecution"]["Status"]
        if st["State"] not in ("QUEUED", "RUNNING"):
            break
        time.sleep(2)
    assert st["State"] == "SUCCEEDED", st
    r = json.loads(subprocess.run(["aws", "athena", "get-query-results", "--query-execution-id", qid, "--max-items", "1000"], capture_output=True, text=True, env=ENV).stdout)["ResultSet"]["Rows"]
    return [[c.get("VarCharValue") for c in x["Data"]] for x in r[1:]]


def colunas_vivas():
    return athena("select column_name, data_type from information_schema.columns where table_schema='hml_gold' and table_name='fato_conciliacao_multi_kmm' order by ordinal_position")


TIPO = {"varchar": "STRING", "double": "DOUBLE", "bigint": "BIGINT", "integer": "INT", "date": "DATE"}
TIPO_TRINO = {"varchar": "varchar", "double": "double", "bigint": "bigint", "integer": "integer", "date": "date"}


def embrulha(corpo, cols, tipos):
    sel = ",\n    ".join("CAST(%s AS %s) AS %s" % (n, tipos[t], n) for n, t in cols)
    return "SELECT\n    %s\nFROM (\n%s\n) t" % (sel, corpo)


if __name__ == "__main__":
    src = open(FONTE, encoding="utf-8").read()
    cols = colunas_vivas()
    base = "WITH" + src[src.index("WITH") + 4:]
    # Spark
    corpo = spark(comum(base, "{env}"))
    cab = ("-- Fato: conciliacao Multi (TMS) x KMM (ERP), CT-e + NF, uma linha por documento. Gerado de conciliacao_multi_kmm.sql por gerar_conciliacao_gold.py.\n"
           "-- Traducao Athena->Spark: try_cast->CAST, varchar->STRING, date_diff->datediff, array_agg->array_sort(collect_set), contains->array_contains, split_part->split()[n], GREATEST preserva NULL,\n"
           "-- ORDER BY com NULLS LAST (Spark ordena NULL primeiro no ASC), view vw_fato_operacional_painel_filial -> CTE painel_view (mesma regra).\n"
           "-- Colunas e tipos iguais aos da tabela hml_gold.fato_conciliacao_multi_kmm (105 colunas), para o BI ler com select *.\n")
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    open(SAIDA, "w", encoding="utf-8").write(cab + embrulha(corpo, cols, TIPO) + "\n")
    # Teste Athena (sem funcoes Spark)
    t = comum(base, "prd")
    open(TESTE, "w", encoding="utf-8").write(embrulha(t, cols, TIPO_TRINO) + "\n")
    print("gerados:", SAIDA, TESTE, len(cols), "colunas")
