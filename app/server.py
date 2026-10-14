"""API web do Como Eu Fico: SQLite operacional com agregados municipais."""
import os
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

ROOT = Path(__file__).resolve().parent.parent
DB = Path(os.environ.get("COMO_EU_FICO_DB", str(ROOT / "data/app/como_eu_fico.sqlite"))).expanduser()
app = FastAPI(title="Como Eu Fico")

def validate_db():
    """Identifica banco ausente, ponteiro LFS e esquema incompleto."""
    if not DB.is_file():
        return "Banco SQLite não encontrado em " + str(DB) + ". Execute git lfs pull na raiz do repositório."
    try:
        with DB.open("rb") as stream:
            header = stream.read(64)
        if header.startswith(b"version https://git-lfs.github.com"):
            return "Arquivo é ponteiro do Git LFS, não SQLite. Execute git lfs pull."
        if not header.startswith(b"SQLite format 3\\x00"):
            return "Arquivo do banco não é SQLite válido: " + str(DB)
        with sqlite3.connect(DB.resolve().as_uri() + "?mode=ro", uri=True) as cx:
            required = {"municipios", "votos_presidenciais", "bolsa_familia_mensal", "origem_dados"}
            available = {r[0] for r in cx.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
            missing = required - available
            if missing:
                return "Banco operacional incompleto. Tabelas/views ausentes: " + ", ".join(sorted(missing))
            if cx.execute("SELECT COUNT(*) FROM municipios").fetchone()[0] != 5571:
                return "Banco operacional não possui os 5.571 municípios esperados."
    except (OSError, sqlite3.Error) as exc:
        return "Falha ao ler banco SQLite: " + str(exc)
    return None


def connect():
    error = validate_db()
    if error:
        raise HTTPException(503, error)
    cx = sqlite3.connect(DB.resolve().as_uri() + "?mode=ro", uri=True)
    cx.row_factory = sqlite3.Row
    return cx


@app.get("/api/health")
def health():
    error = validate_db()
    if error:
        raise HTTPException(503, error)
    return {"status": "ok", "database": "ready"}

@app.get("/api/fontes")
def fontes():
    with connect() as cx:
        return [dict(r) for r in cx.execute("SELECT * FROM origem_dados")]

@app.get("/api/municipios")
def municipios(q: str = "", limit: int = 30):
    with connect() as cx:
        return [dict(r) for r in cx.execute(
            "SELECT codigo_ibge,nome,uf,populacao,ano_populacao FROM municipios "
            "WHERE codigo_ibge LIKE ? OR nome LIKE ? "
            "ORDER BY nome IS NULL,nome,codigo_ibge LIMIT ?",
            ("%" + q + "%", "%" + q + "%", min(max(limit,1),100))
        )]

@app.get("/api/municipios/{codigo_ibge}")
def municipio(codigo_ibge: str):
    with connect() as cx:
        row = cx.execute("SELECT * FROM municipios WHERE codigo_ibge=?", (codigo_ibge,)).fetchone()
        if row is None: raise HTTPException(404, "Município não encontrado")
        bolsa = [dict(r) for r in cx.execute(
            "SELECT mes_competencia,parcelas,valor_centavos FROM bolsa_familia_mensal "
            "WHERE codigo_ibge=? ORDER BY mes_competencia", (codigo_ibge,)
        )]
        votos = [dict(r) for r in cx.execute(
            "SELECT candidato,votos FROM votos_presidenciais WHERE codigo_ibge=? "
            "AND eleicao=2026 AND turno=1 ORDER BY votos DESC", (codigo_ibge,)
        )]
        return {"municipio":dict(row),"bolsa_familia":bolsa,
                "votos_presidenciais":votos,"eleitoral_disponivel":bool(votos)}

@app.get("/", response_class=HTMLResponse)
def home():
    return """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Como Eu Fico</title><style>
body{margin:0;background:#f6f8f5;color:#163629;font:16px system-ui,sans-serif}
header{background:#16412b;color:white;padding:35px 6%}header p{max-width:700px}
main{max-width:900px;padding:30px 20px;margin:auto}
input{width:100%;box-sizing:border-box;padding:15px;border:1px solid #bbb;border-radius:7px}
button{display:block;width:100%;padding:12px;text-align:left;background:white;border:1px solid #ddd;cursor:pointer}
section{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:20px}
article{padding:20px;background:white;border:1px solid #ddd;border-radius:8px}
small{color:#53665d}svg{width:100%;height:150px}
@media(max-width:650px){section{grid-template-columns:1fr}}
</style></head><body><header><h1>Como Eu Fico</h1>
<p>Como a verba federal chega ao seu município? E como ele votou?</p></header>
<main><label>Município ou código IBGE<input id="search" placeholder="Digite o nome ou código"></label>
<div id="choices"></div><h2 id="title"></h2><p id="population"></p><section id="panels" hidden>
<article><h3>Bolsa Família</h3><strong id="total"></strong><p id="parcelas"></p><svg id="chart" viewBox="0 0 600 150"></svg>
<small>CGU; valores registrados por competência. Parcelas não são famílias únicas nem comprovam saque.</small></article>
<article><h3>Votação presidencial 2026</h3><p id="votes"></p>
<small>Primeiro turno, TSE. A comparação territorial não demonstra causalidade.</small></article>
</section><p id="error"></p></main>
<script>
const qs=s=>document.querySelector(s),money=n=>(n/100).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
let debounce;
qs('#search').addEventListener('input',()=>{clearTimeout(debounce);debounce=setTimeout(async()=>{
const q=qs('#search').value.trim();qs('#choices').replaceChildren();if(!q)return;
const data=await(await fetch('/api/municipios?q='+encodeURIComponent(q))).json();
for(const m of data){const b=document.createElement('button');b.textContent=(m.nome||'Município')+' — '+(m.uf||'IBGE')+' ('+m.codigo_ibge+')';
b.onclick=()=>show(m.codigo_ibge);qs('#choices').append(b)}
},180)});
async function show(code){qs('#error').textContent='';const res=await fetch('/api/municipios/'+encodeURIComponent(code));
if(!res.ok){qs('#error').textContent='Município indisponível';return}
const d=await res.json(),m=d.municipio,b=d.bolsa_familia,v=d.votos_presidenciais;
history.replaceState({},'', '?municipio='+code);qs('#choices').replaceChildren();qs('#panels').hidden=false;
qs('#title').textContent=(m.nome||'Município IBGE '+code)+(m.uf?' — '+m.uf:'');qs('#population').textContent=m.populacao!=null?'População: '+m.populacao.toLocaleString('pt-BR')+' (IBGE, '+m.ano_populacao+')':'População IBGE ainda não carregada';
qs('#total').textContent=money(b.reduce((s,x)=>s+x.valor_centavos,0));
qs('#parcelas').textContent=b.reduce((s,x)=>s+x.parcelas,0).toLocaleString('pt-BR')+' parcelas registradas';
qs('#votes').textContent=v.length?v.map(x=>({'13':'Lula','22':'Flávio Bolsonaro'}[x.candidato]||'Candidato '+x.candidato)+' ('+x.candidato+'): '+x.votos.toLocaleString('pt-BR')+' votos ('+(x.votos*100/v.reduce((s,i)=>s+i.votos,0)).toFixed(1).replace('.',',')+'%)').join(' • '):
'Dados eleitorais ainda não carregados. Ausência não significa zero.';
const svg=qs('#chart');svg.replaceChildren();const max=Math.max(1,...b.map(x=>x.valor_centavos));
if(b.length){const points=b.map((x,i)=>(10+i*580/Math.max(1,b.length-1))+','+(140-120*x.valor_centavos/max)).join(' ');
const line=document.createElementNS('http://www.w3.org/2000/svg','polyline');
line.setAttribute('points',points);line.setAttribute('fill','none');line.setAttribute('stroke','#18844d');line.setAttribute('stroke-width','3');svg.append(line)}
}
const code=new URLSearchParams(location.search).get('municipio');if(code)show(code);
</script></body></html>"""
