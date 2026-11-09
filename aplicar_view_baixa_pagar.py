"""Cria/atualiza hml_gold.vw_fato_baixa_pagar (vw_fato_baixa_pagar.sql) e mostra as colunas.
Uso:  python aplicar_view_baixa_pagar.py
Rollback: DROP VIEW hml_gold.vw_fato_baixa_pagar  (nada mais depende dela ate o Financeiro ser ligado a ela).
"""
import json, os, subprocess, sys, tempfile, time

ENV = dict(os.environ, AWS_DEFAULT_OUTPUT="json", AWS_DEFAULT_REGION="us-east-1")
SQL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vw_fato_baixa_pagar.sql")


def aws(*a):
    r = subprocess.run(["aws", *a], capture_output=True, text=True, env=ENV)
    if r.returncode:
        sys.exit("ERRO aws: " + r.stderr.strip())
    return json.loads(r.stdout) if r.stdout.strip() else None


q = open(SQL, encoding="utf-8").read()
q = q[q.index("CREATE OR REPLACE VIEW"):].strip().rstrip(";")
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
t = aws("glue", "get-table", "--database-name", "hml_gold", "--name", "vw_fato_baixa_pagar")["Table"]
print("view criada com", len(t["StorageDescriptor"]["Columns"]), "colunas:", [c["Name"] for c in t["StorageDescriptor"]["Columns"]])
