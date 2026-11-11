"""Etapa 7b: indice HTML navegavel (MAPEAMENTO/index.html).

- Miniaturas JPEG em MAPEAMENTO/_indice/miniaturas/ (so refaz as que mudaram).
- index.html sem dependencias externas: arvore de pastas, busca, grade de miniaturas,
  visualizador (setas do teclado) e a aba Cobertura (cobertura_final.csv + resumo_final.json).
Uso: python gera_indice.py   (depois de relatorio_final.py)
"""
import csv
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent / "MAPEAMENTO"
THUMBS = ROOT / "_indice" / "miniaturas"
SECOES = {
    "02-menus": "Menus da barra",
    "03-telas": "Telas (janelas)",
    "04-dockers": "Dockers",
    "05-ferramentas": "Ferramentas",
    "06-barras": "Barras de ferramentas",
    "07-menus-de-contexto": "Menus de contexto",
}


def thumb(png):
    rel = png.relative_to(ROOT)
    out = THUMBS / rel.with_suffix(".jpg")
    if not out.exists() or out.stat().st_mtime < png.stat().st_mtime:
        out.parent.mkdir(parents=True, exist_ok=True)
        im = Image.open(png).convert("RGB")
        w, h = im.size
        im.thumbnail((360, 300))
        im.save(out, "JPEG", quality=78)
    else:
        with Image.open(png) as im:
            w, h = im.size
    return out.relative_to(ROOT), w, h


def main():
    imgs = []
    for sec in SECOES:
        for png in sorted((ROOT / sec).rglob("*.png")):
            t, w, h = thumb(png)
            imgs.append([png.relative_to(ROOT).as_posix(), t.as_posix(), w, h])
    R = ROOT / "90-relatorios"
    with open(R / "cobertura_final.csv", encoding="utf-8-sig") as f:
        cob = [dict(r) for r in csv.DictReader(f, delimiter=";")]
    for r in cob:
        for k in ("imagem", "menu_print"):
            r[k] = r[k].replace("\\", "/")
    with open(R / "cobertura_definicoes_internas.csv", encoding="utf-8-sig") as f:
        defs = [dict(r) for r in csv.DictReader(f, delimiter=";")]
    resumo = json.loads((R / "resumo_final.json").read_text(encoding="utf-8"))
    data = {"secoes": SECOES, "imgs": imgs, "cob": cob, "defs": defs, "resumo": resumo}
    html = TEMPLATE.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    (ROOT / "index.html").write_text(html, encoding="utf-8")
    print(len(imgs), "imagens;", len(cob), "itens na cobertura ->", ROOT / "index.html")


TEMPLATE = r"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mapa do CorelDRAW 2026</title>
<style>
:root{--bg:#f6f6f4;--panel:#fff;--ink:#1d1d1b;--muted:#6b6b66;--line:#e3e2dc;--accent:#1f6f5c;--accent-soft:#e3f0ec;
--ok:#1f7a4d;--warn:#a5650a;--bad:#b3261e;--shadow:0 1px 2px rgba(0,0,0,.06),0 2px 8px rgba(0,0,0,.05)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161615;--panel:#1f1f1d;--ink:#ecebe6;--muted:#9b9a93;
--line:#33332f;--accent:#5cc3a6;--accent-soft:#1d332d;--ok:#5cc38a;--warn:#e0a54a;--bad:#ef7a70;--shadow:none}}
:root[data-theme="dark"]{--bg:#161615;--panel:#1f1f1d;--ink:#ecebe6;--muted:#9b9a93;--line:#33332f;--accent:#5cc3a6;
--accent-soft:#1d332d;--ok:#5cc38a;--warn:#e0a54a;--bad:#ef7a70;--shadow:none}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 "Segoe UI",system-ui,sans-serif}
header{position:sticky;top:0;z-index:5;display:flex;gap:16px;align-items:center;padding:10px 16px;
background:var(--panel);border-bottom:1px solid var(--line)}
header h1{font-size:16px;margin:0;white-space:nowrap}
header h1 small{color:var(--muted);font-weight:400}
.tabs{display:flex;gap:4px}
.tabs button{border:0;background:none;color:var(--muted);padding:6px 12px;border-radius:6px;cursor:pointer;font:inherit}
.tabs button.on{background:var(--accent-soft);color:var(--accent);font-weight:600}
#busca{flex:1;max-width:420px;padding:7px 10px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink);font:inherit}
label.chk{color:var(--muted);white-space:nowrap;display:flex;gap:6px;align-items:center;cursor:pointer}
main{display:flex;min-height:calc(100vh - 53px)}
nav{width:300px;flex:none;border-right:1px solid var(--line);background:var(--panel);overflow:auto;
max-height:calc(100vh - 53px);position:sticky;top:53px;padding:8px 0}
nav ul{list-style:none;margin:0;padding:0}
nav li>div{display:flex;align-items:center;gap:4px;padding:3px 10px 3px calc(var(--d)*14px + 8px);cursor:pointer;
white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--ink)}
nav li>div:hover{background:var(--bg)}
nav li>div.sel{background:var(--accent-soft);color:var(--accent);font-weight:600}
nav .tw{width:14px;flex:none;color:var(--muted);font-size:10px;text-align:center}
nav .n{margin-left:auto;color:var(--muted);font-size:12px;padding-left:8px}
nav .nm{overflow:hidden;text-overflow:ellipsis}
#conteudo{flex:1;min-width:0;padding:16px 20px 40px}
.trilha{color:var(--muted);margin-bottom:12px;font-size:13px}
.trilha b{color:var(--ink)}
h2.grupo{font-size:13px;font-weight:600;color:var(--muted);margin:22px 0 8px;padding-bottom:4px;border-bottom:1px solid var(--line)}
h2.grupo:first-child{margin-top:0}
.grade{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;overflow:hidden;cursor:pointer;box-shadow:var(--shadow);
display:flex;flex-direction:column}
.card:hover{border-color:var(--accent)}
.card .im{height:150px;display:flex;align-items:center;justify-content:center;background:#2a2a28;overflow:hidden}
.card img{max-width:100%;max-height:150px;display:block}
.card .cap{padding:6px 8px;font-size:12px;line-height:1.35;word-break:break-word}
.card .cap small{display:block;color:var(--muted)}
.mais{margin:14px 0;padding:8px 14px;border:1px solid var(--line);border-radius:6px;background:var(--panel);color:var(--ink);cursor:pointer;font:inherit}
#lb{position:fixed;inset:0;background:rgba(10,10,10,.92);display:none;z-index:20;flex-direction:column}
#lb.on{display:flex}
#lb .bar{display:flex;gap:12px;align-items:center;padding:10px 16px;color:#ddd;font-size:13px}
#lb .bar span{flex:1;word-break:break-all}
#lb .bar a,#lb .bar button{color:#ddd;background:#333;border:0;border-radius:5px;padding:5px 10px;cursor:pointer;text-decoration:none;font:inherit}
#lb .vw{flex:1;overflow:auto;display:flex;align-items:flex-start;justify-content:center;padding:0 16px 16px}
#lb img{max-width:100%;height:auto;background:#fff}
#lb img.real{max-width:none}
.resumo{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px;margin-bottom:18px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px 12px}
.kpi b{display:block;font-size:22px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12px}
.filtros{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 12px}
.filtros button{border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:999px;padding:4px 10px;cursor:pointer;font:inherit;font-size:12px}
.filtros button.on{border-color:var(--accent);background:var(--accent-soft);color:var(--accent);font-weight:600}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);font-size:13px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{position:sticky;top:53px;background:var(--panel);font-size:12px;color:var(--muted);font-weight:600}
td.p{word-break:break-word}
.st{white-space:nowrap;font-weight:600;font-size:12px}
.st.ok{color:var(--ok)}.st.av{color:var(--warn)}.st.no{color:var(--bad)}
a.ver{color:var(--accent);cursor:pointer;text-decoration:underline}
.nota{color:var(--muted);max-width:820px}
@media (max-width:760px){main{display:block}nav{width:auto;position:static;max-height:40vh;border-right:0;border-bottom:1px solid var(--line)}
header{flex-wrap:wrap}#busca{max-width:none;width:100%;order:9}.grade{grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}}
</style>
</head>
<body>
<header>
  <h1>CorelDRAW 2026 <small>mapa de telas</small></h1>
  <div class="tabs"><button id="tPrints" class="on">Prints</button><button id="tCob">Cobertura</button></div>
  <input id="busca" type="search" placeholder="Buscar pelo nome (ex.: Contour, Options, Fill)">
  <label class="chk"><input type="checkbox" id="ti"> tela inteira</label>
</header>
<main>
  <nav id="arvore"></nav>
  <section id="conteudo"></section>
</main>
<div id="lb"><div class="bar"><button id="lbAnt">&larr;</button><button id="lbProx">&rarr;</button>
<span id="lbNome"></span><button id="lbZoom">tamanho real</button><a id="lbAbrir" target="_blank">abrir arquivo</a>
<button id="lbFechar">fechar (Esc)</button></div><div class="vw"><img id="lbImg" alt=""></div></div>
<script>
const D=/*DATA*/null;
const $=s=>document.querySelector(s);
const enc=p=>p.split('/').map(encodeURIComponent).join('/');
const nome=p=>p.split('/').pop().replace(/\.png$/i,'');
const nomePasta=s=>D.secoes[s]?D.secoes[s]:s;
let telaInteira=false,selPasta='',busca='',aba='prints',lista=[],lbI=0,abertas=new Set(Object.keys(D.secoes));
try{telaInteira=localStorage.getItem('ti')==='1'}catch(e){}
$('#ti').checked=telaInteira;
function visiveis(){return D.imgs.filter(i=>telaInteira||!i[0].split('/').includes('tela-inteira'))}
function arvore(){
  const raiz={k:{},n:0};
  for(const i of visiveis()){const ps=i[0].split('/');ps.pop();let no=raiz;no.n++;
    for(const p of ps){no.k[p]=no.k[p]||{k:{},n:0};no=no.k[p];no.n++}}
  const ul=document.createElement('ul');
  const add=(no,cam,d,pai)=>{for(const p of Object.keys(no.k).sort((a,b)=>a.localeCompare(b,'pt',{numeric:true}))){
    const c=cam?cam+'/'+p:p,f=no.k[p],tem=Object.keys(f.k).length>0;const li=document.createElement('li');
    const dv=document.createElement('div');dv.style.setProperty('--d',d);dv.title=c;
    dv.innerHTML=`<span class="tw">${tem?(abertas.has(c)?'▾':'▸'):''}</span><span class="nm"></span><span class="n">${f.n}</span>`;
    dv.querySelector('.nm').textContent=d===0?nomePasta(p):p;
    if(c===selPasta)dv.className='sel';
    dv.onclick=()=>{if(tem&&(selPasta===c||!abertas.has(c))){abertas.has(c)&&selPasta===c?abertas.delete(c):abertas.add(c)}
      selPasta=c;busca='';$('#busca').value='';aba='prints';render()};
    li.appendChild(dv);pai.appendChild(li);
    if(tem&&abertas.has(c)){const sub=document.createElement('ul');li.appendChild(sub);add(f,c,d+1,sub)}}};
  const li0=document.createElement('li');const d0=document.createElement('div');d0.style.setProperty('--d',0);
  d0.innerHTML=`<span class="tw"></span><span class="nm">Visão geral</span><span class="n">${raiz.n}</span>`;
  if(!selPasta)d0.className='sel';d0.onclick=()=>{selPasta='';aba='prints';render()};li0.appendChild(d0);ul.appendChild(li0);
  add(raiz,'',0,ul);$('#arvore').replaceChildren(ul)}
function card(i,idx){const c=document.createElement('div');c.className='card';
  const ps=i[0].split('/');c.innerHTML=`<div class="im"><img loading="lazy" alt=""></div><div class="cap"><span></span><small></small></div>`;
  c.querySelector('img').src=enc(i[1]);c.querySelector('.cap span').textContent=nome(i[0]);
  c.querySelector('.cap small').textContent=`${i[2]}×${i[3]}`;c.onclick=()=>abrir(idx);return c}
function grupos(arr,el){let atual=null,grade=null,n=0;const LIM=400;
  const pinta=(ini)=>{for(let k=ini;k<arr.length&&k<ini+LIM;k++){const i=arr[k];const g=i[0].split('/').slice(0,-1).join('/');
      if(g!==atual){atual=g;const h=document.createElement('h2');h.className='grupo';
        h.textContent=g.split('/').map((p,j)=>j===0?nomePasta(p):p).join('  ›  ');el.appendChild(h);
        grade=document.createElement('div');grade.className='grade';el.appendChild(grade)}
      grade.appendChild(card(i,k))}
    if(ini+LIM<arr.length){const b=document.createElement('button');b.className='mais';
      b.textContent=`mostrar mais (${arr.length-ini-LIM} restantes)`;b.onclick=()=>{b.remove();pinta(ini+LIM)};el.appendChild(b)}};
  pinta(0)}
function geral(el){const r=D.resumo;const vs=visiveis();
  el.innerHTML=`<p class="nota">Prints de menus, telas, dockers, ferramentas, barras e menus de contexto do CorelDRAW 2026 (inglês).
  Escolha uma pasta à esquerda, busque pelo nome ou veja na aba <b>Cobertura</b> o que tem print e o que ficou de fora, com o motivo.
  As pastas com nome de contexto (doc-vazio, retangulo, texto-artistico…) mostram a mesma tela com aquele objeto selecionado.
  Detalhes no <a href="LEIA-ME.md">LEIA-ME.md</a>.</p>`;
  const k=document.createElement('div');k.className='resumo';
  for(const [s,t] of Object.entries(D.secoes)){const n=vs.filter(i=>i[0].startsWith(s+'/')).length;
    const d=document.createElement('div');d.className='kpi';d.style.cursor='pointer';d.innerHTML=`<b>${n}</b><span></span>`;
    d.querySelector('span').textContent=t;d.onclick=()=>{selPasta=s;abertas.add(s);render()};k.appendChild(d)}
  el.appendChild(k)}
function prints(){const el=$('#conteudo');el.replaceChildren();
  let arr=visiveis();
  if(busca){const q=busca.toLowerCase();arr=arr.filter(i=>i[0].toLowerCase().includes(q));
    const t=document.createElement('div');t.className='trilha';t.innerHTML=`<b>${arr.length}</b> prints com “<span></span>”`;
    t.querySelector('span').textContent=busca;el.appendChild(t)}
  else if(selPasta){arr=arr.filter(i=>i[0].startsWith(selPasta+'/'));
    const t=document.createElement('div');t.className='trilha';
    t.innerHTML=`<b></b> · ${arr.length} prints`;t.querySelector('b').textContent=selPasta.split('/').map((p,j)=>j===0?nomePasta(p):p).join('  ›  ');el.appendChild(t)}
  else{geral(el);return}
  lista=arr;grupos(arr,el)}
const CL=s=>s.startsWith('ok')?'ok':(s==='fora do escopo'||s==='nao aberto de proposito'||s==='oculto'?'av':'no');
let filtroCob='todos';
function cobertura(){const el=$('#conteudo');el.replaceChildren();const r=D.resumo;
  const k=document.createElement('div');k.className='resumo';
  const kp=(n,t)=>{const d=document.createElement('div');d.className='kpi';d.innerHTML=`<b>${n}</b><span></span>`;d.querySelector('span').textContent=t;k.appendChild(d)};
  kp(r.itens_de_menu,'itens de menu no inventário');for(const [s,n] of r.situacao)kp(n,s);
  kp(r.definicoes_internas,'definições internas (DrawUI.xml)');el.appendChild(k);
  const p=document.createElement('p');p.className='nota';
  p.innerHTML=`Cada item dos menus da barra, cruzado com todos os logs. <b>ok</b>: tem print (da tela, do submenu, ou o comando aparece no print do menu).
  <b>nao aberto de proposito</b>: lista negra ou decisão sua (salvar, exportar, imprimir, conta, navegador). <b>sem print da tela</b>: ficou desativado em todos os contextos testados.
  <b>fora do escopo</b>: menus Purchase e Debug. Clique no nome para ver o print.`;el.appendChild(p);
  const sts=['todos','sem print (tudo que não é ok)',...r.situacao.map(x=>x[0]),'definições internas'];
  const f=document.createElement('div');f.className='filtros';
  for(const s of sts){const b=document.createElement('button');b.textContent=s;if(s===filtroCob)b.className='on';b.onclick=()=>{filtroCob=s;cobertura()};f.appendChild(b)}
  el.appendChild(f);
  const q=busca.toLowerCase();
  if(filtroCob==='definições internas'){const t=document.createElement('table');
    t.innerHTML='<thead><tr><th>tipo</th><th>nome</th><th>fotografado por outro caminho</th><th>observação</th></tr></thead><tbody></tbody>';
    for(const d of D.defs.filter(d=>!q||d.nome.toLowerCase().includes(q))){const tr=document.createElement('tr');
      for(const v of [d.tipo,d.nome,d.fotografado_por_outro_caminho,d.observacao]){const td=document.createElement('td');td.textContent=v;tr.appendChild(td)}
      t.tBodies[0].appendChild(tr)}el.appendChild(t);return}
  let rows=D.cob;if(filtroCob==='sem print (tudo que não é ok)')rows=rows.filter(x=>!x.situacao.startsWith('ok'));
  else if(filtroCob!=='todos')rows=rows.filter(x=>x.situacao===filtroCob);
  if(q)rows=rows.filter(x=>x.caminho.toLowerCase().includes(q));
  const t=document.createElement('table');
  t.innerHTML='<thead><tr><th>item</th><th>tipo</th><th>situação</th><th>contexto</th><th>por dentro</th><th>motivo / nota</th></tr></thead><tbody></tbody>';
  const idx=new Map(D.imgs.map((i,n)=>[i[0],n]));
  for(const x of rows){const tr=document.createElement('tr');const td0=document.createElement('td');td0.className='p';
    const img=x.imagem||x.menu_print;
    if(img&&idx.has(img)){const a=document.createElement('a');a.className='ver';a.textContent=x.caminho;
      a.onclick=()=>{lista=D.imgs;abrir(idx.get(img))};td0.appendChild(a)}else td0.textContent=x.caminho;
    tr.appendChild(td0);
    const vals=[x.tipo,x.situacao,x.contexto,x.prints_dentro,x.motivo];
    vals.forEach((v,j)=>{const td=document.createElement('td');td.textContent=v;if(j===1)td.className='st '+CL(v);tr.appendChild(td)});
    t.tBodies[0].appendChild(tr)}
  el.appendChild(t)}
function abrir(i){lbI=i;const it=lista[i];$('#lbImg').src=enc(it[0]);$('#lbImg').className='';$('#lbNome').textContent=it[0];
  $('#lbAbrir').href=enc(it[0]);$('#lb').classList.add('on')}
function mover(d){if(!lista.length)return;abrir((lbI+d+lista.length)%lista.length)}
$('#lbAnt').onclick=()=>mover(-1);$('#lbProx').onclick=()=>mover(1);
$('#lbFechar').onclick=()=>$('#lb').classList.remove('on');
$('#lbZoom').onclick=()=>$('#lbImg').classList.toggle('real');
document.addEventListener('keydown',e=>{if(!$('#lb').classList.contains('on'))return;
  if(e.key==='Escape')$('#lb').classList.remove('on');if(e.key==='ArrowRight')mover(1);if(e.key==='ArrowLeft')mover(-1)});
$('#busca').oninput=e=>{busca=e.target.value.trim();render()};
$('#ti').onchange=e=>{telaInteira=e.target.checked;try{localStorage.setItem('ti',telaInteira?'1':'0')}catch(x){}render()};
$('#tPrints').onclick=()=>{aba='prints';render()};$('#tCob').onclick=()=>{aba='cob';render()};
function render(){$('#tPrints').className=aba==='prints'?'on':'';$('#tCob').className=aba==='cob'?'on':'';
  arvore();aba==='cob'?cobertura():prints();}
render();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
