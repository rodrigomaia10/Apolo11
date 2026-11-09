"""Atualiza hml_gold.fato_conciliacao_multi_kmm: cria a proxima versao (vNN) a partir de
conciliacao_multi_kmm.sql, valida e so entao repontar a tabela real (SET LOCATION).
Uso:  python atualizar_conciliacao.py          (pede confirmacao antes de trocar)
      python atualizar_conciliacao.py --sim    (troca sem perguntar)
Se qualquer passo falhar antes do SET LOCATION, a tabela real continua na versao anterior.
Rollback manual: ALTER TABLE hml_gold.fato_conciliacao_multi_kmm SET LOCATION '<versao anterior>'.
"""
import json, os, re, subprocess, sys, tempfile, time

REGIAO, WG, DB = "us-east-1", "cootravale-s3-athena", "hml_gold"
TABELA = "fato_conciliacao_multi_kmm"
BUCKET, PREFIXO = "cootravale-layer-gold", "hml/gold"
SQL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conciliacao_multi_kmm.sql")
ENV = dict(os.environ, AWS_DEFAULT_OUTPUT="json", AWS_DEFAULT_REGION=REGIAO)


def aws(*args):
    r = subprocess.run(["aws", *args], capture_output=True, text=True, env=ENV)
    if r.returncode:
        sys.exit("ERRO aws %s\n%s" % (" ".join(args[:3]), r.stderr.strip()))
    return json.loads(r.stdout) if r.stdout.strip() else None


def athena(sql, espera=1800):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump({"QueryString": sql, "WorkGroup": WG, "QueryExecutionContext": {"Database": DB}}, f)
    qid = aws("athena", "start-query-execution", "--cli-input-json", "file://" + f.name)["QueryExecutionId"]
    os.unlink(f.name)
    t0 = time.time()
    while time.time() - t0 < espera:
        s = aws("athena", "get-query-execution", "--query-execution-id", qid)["QueryExecution"]["Status"]
        if s["State"] not in ("QUEUED", "RUNNING"):
            if s["State"] != "SUCCEEDED":
                sys.exit("Athena %s: %s" % (s["State"], s.get("StateChangeReason", "")))
            return qid
        time.sleep(10)
    sys.exit("Athena demorou demais (query %s)" % qid)


def contagem(tabela):
    qid = athena("SELECT count(*) FROM %s.%s" % (DB, tabela))
    return int(aws("athena", "get-query-results", "--query-execution-id", qid)["ResultSet"]["Rows"][1]["Data"][0]["VarCharValue"])


# 1. proxima versao: maior vNN no S3 e no catalogo + 1
s3 = subprocess.run(["aws", "s3", "ls", "s3://%s/%s/" % (BUCKET, PREFIXO)], capture_output=True, text=True, env=ENV).stdout
versoes = [int(m) for m in re.findall(r"%s_v(\d+)/" % TABELA, s3)]
nova = "v%d" % (max(versoes) + 1)
novo_nome = "%s_%s" % (TABELA, nova)
local_novo = "s3://%s/%s/%s/" % (BUCKET, PREFIXO, novo_nome)
print("Versao nova:", nova)

# 2. schema da tabela real (a CTAS tem que sair com os mesmos nomes/tipos/ordem)
live = aws("glue", "get-table", "--database-name", DB, "--name", TABELA)["Table"]
anterior = live["StorageDescriptor"]["Location"]
cols = [(c["Name"], c["Type"]) for c in live["StorageDescriptor"]["Columns"]]
sel = ",\n  ".join(n if t == "string" else "CAST(%s AS %s) AS %s" % (n, t, n) for n, t in cols)
corpo = open(SQL, encoding="utf-8").read().rstrip()
ctas = ("CREATE TABLE %s.%s\nWITH (format='PARQUET', parquet_compression='GZIP', external_location='%s') AS\n"
        "SELECT %s\nFROM (\n%s\n) t" % (DB, novo_nome, local_novo, sel, corpo))
n_antes = contagem(TABELA)
print("Tabela atual: %s linhas, aponta para %s" % (n_antes, anterior))

# 3. cria a versao nova
print("Criando %s (pode levar alguns minutos)..." % novo_nome)
athena(ctas)

# 4. valida antes de trocar
n_novo = contagem(novo_nome)
print("Versao nova: %s linhas (antes: %s)" % (n_novo, n_antes))
if n_novo < 0.8 * n_antes:
    sys.exit("Parou: a versao nova tem menos de 80%% das linhas da atual. Nada foi trocado. Confira %s." % novo_nome)

if "--sim" not in sys.argv and input("Trocar a tabela real para %s? [s/N] " % nova).strip().lower() != "s":
    sys.exit("Nao troquei. A versao %s ficou criada; a tabela real continua em %s" % (nova, anterior))

# 5. troca e teste com select * completo (o count(*) nao pega erro de tipo de coluna)
athena("ALTER TABLE %s.%s SET LOCATION '%s'" % (DB, TABELA, local_novo))
try:
    athena("SELECT * FROM %s.%s" % (DB, TABELA))
except SystemExit as e:
    print("FALHOU o select * na tabela real. Voltando para a versao anterior...")
    athena("ALTER TABLE %s.%s SET LOCATION '%s'" % (DB, TABELA, anterior))
    sys.exit("Rollback feito. Motivo: %s" % e)
print("OK. %s.%s agora aponta para %s (%s linhas). Pode atualizar o Power BI." % (DB, TABELA, local_novo, n_novo))
