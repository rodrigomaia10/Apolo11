"""Reverte a curva do Financeiro para a margem FINANCEIRA (decisao do usuario em 20/10/2026): a foto do DRE serve so para comparar.
Rodar com o Financeiro FECHADO:  python ajusta_curva_visao_financeira.py
Backup: Financeiro.Report_backup_20261020_h
"""
import json, os, shutil

base = r"C:\project\PowerBIClaudio\14 - Controladoria"
rep = os.path.join(base, "Financeiro.Report")
bk = rep + "_backup_20261020_h"
if not os.path.exists(bk):
    shutil.copytree(rep, bk)
vis = os.path.join(rep, "definition", "pages", "a1b2c3d4e5f607182908", "visuals")
ROT = "Margem financeira (receita − custo de frete)"


def ref(tab, med, dn):
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": tab}}, "Property": med}},
            "queryRef": "%s.%s" % (tab, med), "nativeQueryRef": med, "displayName": dn}


def entidade(proj):
    f = proj["field"]
    k = "Measure" if "Measure" in f else "Column"
    return f[k]["Expression"]["SourceRef"]["Entity"], f[k]["Property"]


# cartao principal
p = os.path.join(vis, "a5", "visual.json")
d = json.load(open(p, encoding="utf-8"))
d["visual"]["query"]["queryState"]["Values"]["projections"] = [ref("Documentos", "Margem de Frete % (bruta)", ROT)]
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# tabela: tira as colunas do DRE e renomeia a margem
p = os.path.join(vis, "t_curva", "visual.json")
d = json.load(open(p, encoding="utf-8"))
pr = d["visual"]["query"]["queryState"]["Values"]["projections"]
antes = len(pr)
pr[:] = [x for x in pr if entidade(x)[0] != "DreLinhas"]
for x in pr:
    if entidade(x) == ("Documentos", "Margem de Frete % (bruta)"):
        x["displayName"] = ROT
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# rodape
p = os.path.join(vis, "rodape", "visual.json")
d = json.load(open(p, encoding="utf-8"))
r = d["visual"]["objects"]["general"][0]["properties"]["paragraphs"][0]["textRuns"][0]
i = r["value"].find(" MARGEM DE FRETE =")
if i >= 0:
    r["value"] = r["value"][:i]
r["value"] += (" MARGEM FINANCEIRA = receita dos documentos menos custo de frete e ocorrência, antes de impostos e repasse; "
               "visão financeira, não contábil. A margem de contribuição contábil só aparece nas páginas de conferência.")
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("curva revertida para a margem financeira; colunas removidas da tabela:", antes - len(pr))
