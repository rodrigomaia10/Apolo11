"""Aplica a versao atual de hml_gold.vw_fato_titulo_pagar (vw_financeiro_titulos.sql) e confere as colunas.
Uso:  python aplicar_view_pagar.py
Rollback: aplicar o arquivo vw_financeiro_titulos.sql.bak_20261013 (mesmo trecho CREATE OR REPLACE da view de pagar).
"""
import json, os, subprocess, sys, tempfile, time

ENV = dict(os.environ, AWS_DEFAULT_OUTPUT="json", AWS_DEFAULT_REGION="us-east-1")
SQL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vw_financeiro_titulos.sql")
MARCA = "CREATE OR REPLACE VIEW hml_gold.vw_fato_titulo_pagar"


def aws(*a):
    r = subprocess.run(["aws", *a], capture_output=True, text=True, env=ENV)
    if r.returncode:
        sys.exit("ERRO aws: " + r.stderr.strip())
    return json.loads(r.stdout) if r.stdout.strip() else None


def colunas():
    t = aws("glue", "get-table", "--database-name", "hml_gold", "--name", "vw_fato_titulo_pagar")["Table"]
    return [c["Name"] for c in t["StorageDescriptor"]["Columns"]]


antes = colunas()
texto = open(SQL, encoding="utf-8").read()
q = texto[texto.index(MARCA):].strip().rstrip(";")
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
    json.dump({"QueryString": q, "WorkGroup": "cootravale-s3-athena", "QueryExecutionContext": {"Database": "hml_gold"}}, f)
qid = aws("athena", "start-query-execution", "--cli-input-json", "file://" + f.name)["QueryExecutionId"]
os.unlink(f.name)
for _ in range(60):
    s = aws("athena", "get-query-execution", "--query-execution-id", qid)["QueryExecution"]["Status"]
    if s["State"] not in ("QUEUED", "RUNNING"):
        break
    time.sleep(5)
if s["State"] != "SUCCEEDED":
    sys.exit("Athena %s: %s" % (s["State"], s.get("StateChangeReason", "")))
depois = colunas()
print("colunas antes: %d, depois: %d" % (len(antes), len(depois)))
print("novas:", [c for c in depois if c not in antes], "| removidas:", [c for c in antes if c not in depois])
print("mesma ordem das antigas:", depois[:len(antes)] == antes)
