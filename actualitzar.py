#!/usr/bin/env python3
"""
barcelona-projectes / actualitzar.py
=====================================
Executa'l un cop al mes. Comprova les fonts oficials de cada projecte,
detecta canvis i genera un informe HTML + JSON llest per actualitzar el site.

Ús:
    python3 actualitzar.py

Requisits:
    pip install requests beautifulsoup4
"""

import json, re, time, datetime, hashlib, os, sys
from urllib.parse import urljoin, quote
import requests
from bs4 import BeautifulSoup

# ── CONFIG ────────────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0 Safari/537.36"
}
TIMEOUT = 12
SNAPSHOT_FILE = "snapshots.json"   # historial de canvis
REPORT_FILE   = "informe.html"     # informe llegible

# ── PROJECTES I FONTS ─────────────────────────────────────────────────────────
# Cada projecte té:
#   id, nom, promotor, web_oficial, cerca_notícies (llista de URLs de cerca)
PROJECTES = [
    # ── AJUNTAMENT ──────────────────────────────────────────────────────────
    dict(id=1,  nom="Superilla Eixample – Eixos Verds",
         promotor="Ajuntament de Barcelona",
         web="https://ajuntament.barcelona.cat/superilles/es/",
         cerques=[
             "https://www.barcelona.cat/ca/cercador?q=superilla+eixample",
             "https://news.google.com/search?q=superilla+eixample+barcelona&hl=ca",
         ]),
    dict(id=2,  nom="Reforma de La Rambla",
         promotor="Ajuntament de Barcelona",
         web="https://ajuntament.barcelona.cat/pla-accio-govern2023-2027/es/actuacion/reforma-de-la-rambla_492",
         cerques=[
             "https://www.barcelona.cat/ca/cercador?q=reforma+rambla",
             "https://news.google.com/search?q=reforma+rambla+barcelona&hl=ca",
         ]),
    dict(id=3,  nom="Transformació de les Glòries (Canòpia)",
         promotor="Ajuntament de Barcelona",
         web="https://ajuntament.barcelona.cat/ecologiaurbana/es/actuaciones/can%C3%B2pia-de-les-gl%C3%B2ries",
         cerques=[
             "https://news.google.com/search?q=canopia+glories+barcelona&hl=ca",
         ]),
    dict(id=4,  nom="La Sagrera – Estació Intermodal",
         promotor="Ajuntament de Barcelona",
         web="https://www.sagrera.cat/",
         cerques=[
             "https://www.sagrera.cat/noticies/",
             "https://news.google.com/search?q=sagrera+estacio+barcelona&hl=ca",
         ]),
    dict(id=5,  nom="Reconversió Fàbrica Mercedes-Benz (Bon Pastor)",
         promotor="Ajuntament de Barcelona",
         web="https://ajuntament.barcelona.cat/sant-andreu/es/",
         cerques=[
             "https://news.google.com/search?q=mercedes+benz+bon+pastor+barcelona&hl=ca",
         ]),
    dict(id=6,  nom="Transformació recinte de La Model",
         promotor="Ajuntament de Barcelona",
         web="https://ajuntament.barcelona.cat/eixample/es/",
         cerques=[
             "https://news.google.com/search?q=la+model+barcelona+transformacio&hl=ca",
         ]),
    dict(id=7,  nom="Reforma de Montjuïc",
         promotor="Ajuntament de Barcelona",
         web="https://ajuntament.barcelona.cat/sants-montjuic/es/",
         cerques=[
             "https://news.google.com/search?q=montjuic+reforma+barcelona&hl=ca",
         ]),
    dict(id=8,  nom="Cobertura Gran Via (Glòries–Bilbao)",
         promotor="Ajuntament de Barcelona",
         web="https://ajuntament.barcelona.cat/ecologiaurbana/es/noticia/el-cobriment-de-la-gran-via-entre-badajoz-i-bilbao_1283752",
         cerques=[
             "https://news.google.com/search?q=cobertura+gran+via+glories+bilbao+barcelona&hl=ca",
         ]),
    dict(id=9,  nom="La Industrial+",
         promotor="Ajuntament de Barcelona",
         web="https://ajuntament.barcelona.cat/eixample/es/",
         cerques=[
             "https://news.google.com/search?q=la+industrial+barcelona+innovacio&hl=ca",
         ]),
    dict(id=10, nom="Reforma de Via Laietana",
         promotor="Ajuntament de Barcelona",
         web="https://ajuntament.barcelona.cat/ecologiaurbana/es/noticia/via-laietana-nova-via-civica_1213879",
         cerques=[
             "https://news.google.com/search?q=via+laietana+reforma+barcelona&hl=ca",
         ]),
    dict(id=11, nom="Reforma de Plaça Espanya",
         promotor="Ajuntament de Barcelona",
         web="https://ajuntament.barcelona.cat/sants-montjuic/es/",
         cerques=[
             "https://news.google.com/search?q=placa+espanya+reforma+barcelona&hl=ca",
         ]),
    dict(id=12, nom="Transformació de Vallcarca",
         promotor="Ajuntament de Barcelona",
         web="https://ajuntament.barcelona.cat/gracia/es/",
         cerques=[
             "https://news.google.com/search?q=vallcarca+transformacio+barcelona&hl=ca",
         ]),
    dict(id=13, nom="Desenvolupament 22@ Nord",
         promotor="Ajuntament de Barcelona",
         web="https://www.22barcelona.com/",
         cerques=[
             "https://www.22barcelona.com/ca/",
             "https://news.google.com/search?q=22%40+barcelona+nord&hl=ca",
         ]),

    # ── GENERALITAT / ATM / FGC ──────────────────────────────────────────────
    dict(id=14, nom="Tronc Central L9/L10 Metro",
         promotor="ATM / Generalitat de Catalunya",
         web="https://www.atm.cat/web/ca/projectes/projectes-en-curs/tronc-central-l9-l10.php",
         cerques=[
             "https://www.atm.cat/web/ca/projectes/projectes-en-curs/tronc-central-l9-l10.php",
             "https://news.google.com/search?q=tronc+central+L9+L10+metro+barcelona&hl=ca",
         ]),
    dict(id=15, nom="Prolongació L8 FGC (Espanya–Gràcia)",
         promotor="Generalitat de Catalunya / FGC",
         web="https://www.fgc.cat/ca/fgc/projectes-infraestructura/prolongacio-linia-barcelona-valles/",
         cerques=[
             "https://www.fgc.cat/ca/fgc/projectes-infraestructura/prolongacio-linia-barcelona-valles/",
             "https://news.google.com/search?q=L8+FGC+prolongacio+gracia+barcelona&hl=ca",
         ]),
    dict(id=16, nom="Prolongació L2 a Montjuïc",
         promotor="ATM / Generalitat de Catalunya",
         web="https://www.atm.cat/web/ca/projectes/projectes-en-curs/prolongacio-linia-2.php",
         cerques=[
             "https://www.atm.cat/web/ca/projectes/projectes-en-curs/prolongacio-linia-2.php",
             "https://news.google.com/search?q=metro+L2+montjuic+barcelona&hl=ca",
         ]),
    dict(id=17, nom="Connexió Tramvia per la Diagonal",
         promotor="ATM / Ajuntament",
         web="https://tram.cat/ca/projectes/connexio-tramvia-diagonal/",
         cerques=[
             "https://tram.cat/ca/projectes/connexio-tramvia-diagonal/",
             "https://news.google.com/search?q=tramvia+diagonal+connexio+barcelona&hl=ca",
         ]),
    dict(id=18, nom="Nou Clínic – Campus Diagonal",
         promotor="Generalitat / Hospital Clínic",
         web="https://www.clinicbarcelona.org/el-clinic/projectes/nou-clinic",
         cerques=[
             "https://www.clinicbarcelona.org/el-clinic/projectes/nou-clinic",
             "https://news.google.com/search?q=nou+clinic+campus+diagonal+barcelona&hl=ca",
         ]),

    # ── ESTAT / ADIF / AENA ─────────────────────────────────────────────────
    dict(id=19, nom="Reforma Estació de Sants (Vestíbuls)",
         promotor="Adif / Ministeri de Transports",
         web="https://www.adif.es/es_ES/infraestructuras/estaciones/71801/informacion_000001.shtml",
         cerques=[
             # Plataforma de contractació de l'Estat — licitacions Adif Barcelona Sants
             "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=qNf2x0TdNEiKuF0GEP2%2FpA%3D%3D",
             "https://news.google.com/search?q=estacio+sants+reforma+adif+barcelona&hl=ca",
         ]),
    dict(id=20, nom="Ampliació Gran Estació de Sants",
         promotor="Adif / Ministeri de Transports",
         web="https://www.adif.es/",
         cerques=[
             "https://news.google.com/search?q=gran+estacio+sants+ampliacio+barcelona&hl=ca",
         ]),
    dict(id=21, nom="Ampliació Aeroport El Prat",
         promotor="AENA",
         web="https://www.aena.es/es/aeropuerto-barcelona/ampliacion.html",
         cerques=[
             "https://www.aena.es/es/aeropuerto-barcelona/ampliacion.html",
             "https://news.google.com/search?q=ampliacio+aeroport+prat+barcelona&hl=ca",
         ]),

    # ── PORT DE BARCELONA ────────────────────────────────────────────────────
    dict(id=22, nom="Nous accessos al Port de Barcelona",
         promotor="Port de Barcelona",
         web="https://www.portdebarcelona.cat/es/infraestructura/accesos-terrestres",
         cerques=[
             "https://www.portdebarcelona.cat/es/infraestructura/accesos-terrestres",
             "https://news.google.com/search?q=nous+accessos+port+barcelona&hl=ca",
         ]),
    dict(id=23, nom="BlueTechPort",
         promotor="Port de Barcelona",
         web="https://www.portdebarcelona.cat/es/economia-azul/bluetechport",
         cerques=[
             "https://www.portdebarcelona.cat/es/economia-azul/bluetechport",
             "https://news.google.com/search?q=bluetechport+barcelona&hl=ca",
         ]),

    # ── FUNDACIONS / PRIVATS ─────────────────────────────────────────────────
    dict(id=24, nom="Camp Nou – Espai Barça",
         promotor="FC Barcelona",
         web="https://www.fcbarcelona.es/es/club/espai-barca",
         cerques=[
             "https://www.fcbarcelona.es/es/club/espai-barca",
             "https://news.google.com/search?q=camp+nou+espai+barca+obres&hl=ca",
         ]),
    dict(id=25, nom="Ciutadella del Coneixement",
         promotor="Ajuntament de Barcelona",
         web="https://ajuntament.barcelona.cat/sant-marti/es/",
         cerques=[
             "https://news.google.com/search?q=ciutadella+coneixement+barcelona&hl=ca",
         ]),
    dict(id=26, nom="Ampliació MACBA",
         promotor="Consorci Generalitat/Ajuntament",
         web="https://www.macba.cat/ca/el-museu/sobre-el-macba/projecte-ampliacio",
         cerques=[
             "https://www.macba.cat/ca/el-museu/sobre-el-macba/projecte-ampliacio",
             "https://news.google.com/search?q=macba+ampliacio+barcelona&hl=ca",
         ]),
    dict(id=27, nom="Hall 0 Fira de Barcelona",
         promotor="Fira de Barcelona",
         web="https://www.firabarcelona.com/ca/la-fira/infraestructures/hall-0/",
         cerques=[
             "https://www.firabarcelona.com/ca/la-fira/infraestructures/hall-0/",
             "https://news.google.com/search?q=hall+0+fira+barcelona&hl=ca",
         ]),
]

# ── FONTS OBERTES (APIs) ───────────────────────────────────────────────────────
OPEN_DATA_SOURCES = [
    {
        "nom": "Ajuntament – Obres i llicències",
        "url": "https://opendata-ajuntament.barcelona.cat/data/api/action/datastore_search"
               "?resource_id=f43d8b5d-59b7-4e2d-9e08-1b01f95f8a69&limit=50",
        "tipus": "json_ckan",
    },
    {
        "nom": "Ajuntament – Actuacions urbanístiques",
        "url": "https://opendata-ajuntament.barcelona.cat/data/api/action/datastore_search"
               "?resource_id=3c6d5e7f-2a3b-4c5d-8e9f-1a2b3c4d5e6f&limit=50",
        "tipus": "json_ckan",
    },
    {
        "nom": "Generalitat – Inversions en infraestructures",
        "url": "https://analisi.transparenciacatalunya.cat/resource/4yd6-3ssy.json"
               "?$limit=50&$where=codi_ambit%3D%27BCN%27",
        "tipus": "json_socrata",
    },
    {
        "nom": "Contractació Estat – Adif licitacions",
        "url": "https://contrataciondelestado.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom",
        "tipus": "atom_feed",
    },
]

# ── HELPERS ───────────────────────────────────────────────────────────────────
def fetch(url, timeout=TIMEOUT):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r
    except Exception as e:
        return None

def page_hash(text):
    return hashlib.md5(text.encode("utf-8", errors="replace")).hexdigest()[:12]

def load_snapshots():
    if os.path.exists(SNAPSHOT_FILE):
        with open(SNAPSHOT_FILE) as f:
            return json.load(f)
    return {}

def save_snapshots(snaps):
    with open(SNAPSHOT_FILE, "w") as f:
        json.dump(snaps, f, ensure_ascii=False, indent=2)

def extract_text(html):
    """Extreu text net d'una pàgina HTML."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return " ".join(soup.get_text(separator=" ").split())[:8000]

def extract_news_headlines(html):
    """Extreu titulars de Google News."""
    soup = BeautifulSoup(html, "html.parser")
    headlines = []
    for a in soup.find_all("a", href=True):
        txt = a.get_text(strip=True)
        if len(txt) > 30 and len(txt) < 200:
            headlines.append(txt)
    return headlines[:8]

# ── CHECK OPEN DATA ───────────────────────────────────────────────────────────
def check_open_data():
    results = []
    for src in OPEN_DATA_SOURCES:
        r = fetch(src["url"])
        if not r:
            results.append({"font": src["nom"], "estat": "❌ No accessible", "registres": 0, "mostra": []})
            continue
        try:
            if src["tipus"] in ("json_ckan", "json_socrata"):
                data = r.json()
                if src["tipus"] == "json_ckan":
                    recs = data.get("result", {}).get("records", [])
                else:
                    recs = data if isinstance(data, list) else []
                results.append({
                    "font": src["nom"],
                    "estat": "✅ Accessible",
                    "registres": len(recs),
                    "mostra": [str(rec)[:120] for rec in recs[:3]],
                })
            else:  # atom
                soup = BeautifulSoup(r.text, "xml")
                entries = soup.find_all("entry")[:5]
                results.append({
                    "font": src["nom"],
                    "estat": "✅ Accessible",
                    "registres": len(entries),
                    "mostra": [e.find("title").get_text()[:120] if e.find("title") else "" for e in entries],
                })
        except Exception as e:
            results.append({"font": src["nom"], "estat": f"⚠️ Error: {e}", "registres": 0, "mostra": []})
    return results

# ── CHECK PROJECTS ────────────────────────────────────────────────────────────
def check_projects(snapshots):
    results = []
    total = len(PROJECTES)
    for i, p in enumerate(PROJECTES):
        print(f"  [{i+1}/{total}] {p['nom'][:50]}…", end=" ", flush=True)
        result = {
            "id": p["id"],
            "nom": p["nom"],
            "promotor": p["promotor"],
            "web": p["web"],
            "canvi_web": False,
            "noticies": [],
            "error": None,
        }

        # 1. Check official web
        r = fetch(p["web"])
        if r:
            text = extract_text(r.text)
            h = page_hash(text)
            key = f"web_{p['id']}"
            old = snapshots.get(key, {})
            if old.get("hash") and old["hash"] != h:
                result["canvi_web"] = True
                result["canvi_web_data"] = old.get("data", "desconeguda")
            snapshots[key] = {"hash": h, "data": datetime.date.today().isoformat()}
            print("web✓", end=" ", flush=True)
        else:
            result["error"] = "Web no accessible"
            print("web✗", end=" ", flush=True)

        # 2. Check news searches
        for url in p.get("cerques", []):
            if "news.google.com" in url:
                r2 = fetch(url)
                if r2:
                    headlines = extract_news_headlines(r2.text)
                    result["noticies"].extend(headlines)
                time.sleep(0.5)  # respectful delay

        result["noticies"] = list(dict.fromkeys(result["noticies"]))[:6]  # deduplicate
        print(f"notícies:{len(result['noticies'])}")
        results.append(result)
        time.sleep(0.8)

    return results

# ── GENERATE HTML REPORT ──────────────────────────────────────────────────────
def generate_report(project_results, open_data_results):
    today = datetime.date.today().strftime("%d/%m/%Y")
    canvis = [r for r in project_results if r["canvi_web"]]
    errors = [r for r in project_results if r["error"]]
    with_news = [r for r in project_results if r["noticies"]]

    html = f"""<!DOCTYPE html>
<html lang="ca">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Informe Actualització – Barcelona Projectes · {today}</title>
<style>
  body{{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;padding:32px;max-width:900px;margin:0 auto;line-height:1.6;}}
  h1{{font-size:24px;font-weight:800;color:#f4a623;margin-bottom:4px;}}
  .sub{{font-size:13px;color:#64748b;margin-bottom:32px;}}
  h2{{font-size:15px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;margin:32px 0 12px;border-top:1px solid #1e293b;padding-top:20px;}}
  .kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:32px;}}
  .kpi{{background:#1e293b;border-radius:10px;padding:16px;text-align:center;}}
  .kpi .n{{font-size:28px;font-weight:800;color:#f4a623;}}
  .kpi .l{{font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.07em;}}
  .card{{background:#1e293b;border-radius:10px;padding:16px;margin-bottom:10px;border-left:3px solid #334155;}}
  .card.canvi{{border-left-color:#f59e0b;}}
  .card.error{{border-left-color:#ef4444;}}
  .card.ok{{border-left-color:#10b981;}}
  .cnom{{font-weight:700;font-size:14px;margin-bottom:4px;}}
  .cprom{{font-size:11px;color:#64748b;margin-bottom:8px;}}
  .tag{{display:inline-block;font-size:10px;font-weight:600;padding:2px 8px;border-radius:20px;margin-right:4px;}}
  .tag-canvi{{background:#f59e0b22;color:#f59e0b;}}
  .tag-ok{{background:#10b98122;color:#10b981;}}
  .tag-error{{background:#ef444422;color:#ef4444;}}
  .news-list{{margin-top:8px;padding-left:0;list-style:none;}}
  .news-list li{{font-size:12px;color:#94a3b8;padding:4px 0;border-bottom:1px solid #0f172a;}}
  .news-list li::before{{content:"→ ";color:#f4a623;}}
  .src-card{{background:#1e293b;border-radius:8px;padding:12px;margin-bottom:8px;font-size:12px;}}
  .src-ok{{color:#10b981;}}
  .src-err{{color:#ef4444;}}
  .instruccions{{background:#1e293b;border-radius:10px;padding:20px;margin-top:32px;font-size:13px;color:#94a3b8;}}
  .instruccions h3{{color:#f4a623;margin-bottom:10px;font-size:14px;}}
  code{{background:#0f172a;padding:2px 6px;border-radius:4px;font-size:12px;color:#10b981;}}
  a{{color:#3b82f6;text-decoration:none;}}
  a:hover{{text-decoration:underline;}}
</style>
</head>
<body>
<h1>📊 Informe Actualització — Barcelona Projectes</h1>
<div class="sub">Generat el {today} · {len(project_results)} projectes revisats</div>

<div class="kpis">
  <div class="kpi"><div class="n">{len(project_results)}</div><div class="l">Revisats</div></div>
  <div class="kpi"><div class="n" style="color:#f59e0b">{len(canvis)}</div><div class="l">Canvis detectats</div></div>
  <div class="kpi"><div class="n" style="color:#10b981">{len(with_news)}</div><div class="l">Amb notícies</div></div>
  <div class="kpi"><div class="n" style="color:#ef4444">{len(errors)}</div><div class="l">Errors</div></div>
</div>
"""

    # CANVIS
    if canvis:
        html += "<h2>⚠️ Canvis detectats a les webs oficials</h2>\n"
        html += "<p style='font-size:12px;color:#64748b;margin-bottom:12px'>Aquests projectes han canviat contingut a la seva web oficial des de l'última revisió. Revisa'ls manualment.</p>\n"
        for r in canvis:
            html += f"""<div class="card canvi">
  <div class="cnom">{r['nom']}</div>
  <div class="cprom">{r['promotor']}</div>
  <span class="tag tag-canvi">⚠️ Canvi detectat</span>
  <a href="{r['web']}" target="_blank" style="font-size:11px;">Obre web oficial →</a>
</div>\n"""

    # NOTÍCIES
    if with_news:
        html += "<h2>📰 Notícies recents per projecte</h2>\n"
        for r in with_news:
            html += f"""<div class="card">
  <div class="cnom">{r['nom']}</div>
  <div class="cprom">{r['promotor']}</div>
  <ul class="news-list">{''.join(f"<li>{n}</li>" for n in r['noticies'])}</ul>
</div>\n"""

    # SENSE CANVIS
    ok_list = [r for r in project_results if not r["canvi_web"] and not r["error"] and not r["noticies"]]
    if ok_list:
        html += "<h2>✅ Sense canvis detectats</h2>\n"
        for r in ok_list:
            html += f"""<div class="card ok">
  <div class="cnom">{r['nom']}</div>
  <div class="cprom">{r['promotor']}</div>
  <span class="tag tag-ok">✅ Sense canvis</span>
</div>\n"""

    # ERRORS
    if errors:
        html += "<h2>❌ Webs no accessibles</h2>\n"
        for r in errors:
            html += f"""<div class="card error">
  <div class="cnom">{r['nom']}</div>
  <div class="cprom">{r['promotor']}</div>
  <span class="tag tag-error">❌ {r['error']}</span>
  <a href="{r['web']}" target="_blank" style="font-size:11px;margin-left:8px;">Comprova manualment →</a>
</div>\n"""

    # DADES OBERTES
    html += "<h2>🗃️ Estat de les fonts de dades obertes</h2>\n"
    for src in open_data_results:
        cls = "src-ok" if "✅" in src["estat"] else "src-err"
        html += f"""<div class="src-card">
  <strong>{src['font']}</strong><br>
  <span class="{cls}">{src['estat']}</span>
  {f"· {src['registres']} registres" if src['registres'] else ""}
  {"<br><small style='color:#475569'>" + " | ".join(src['mostra'][:2]) + "</small>" if src['mostra'] else ""}
</div>\n"""

    # INSTRUCCIONS
    html += """<div class="instruccions">
<h3>🔧 Què fer amb aquest informe</h3>
<ol>
  <li><strong>Canvis detectats</strong> → Obre la web oficial i comprova quina informació ha canviat (estat, inversió, data de fi, etc.). Actualitza <code>index.html</code> al repo de GitHub.</li>
  <li><strong>Notícies</strong> → Revisa si hi ha anuncis de nous projectes o canvis d'estat importants que no estiguin reflectits al site.</li>
  <li><strong>Errors</strong> → La web oficial pot estar temporalment caiguda. Torna-ho a provar manualment.</li>
  <li><strong>Dades obertes</strong> → Si algun portal torna registres nous rellevants, consideres afegir-los com a projectes nous.</li>
</ol>
<p style="margin-top:12px">Per actualitzar el site un cop revisats els canvis:</p>
<code>python3 publicar.py</code> — puja automàticament l'<code>index.html</code> actualitzat a GitHub Pages.
</div>
</body>
</html>"""

    return html

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print("\n🔍 Barcelona Projectes — Comprovació mensual")
    print("=" * 50)

    snapshots = load_snapshots()

    print("\n📡 Comprovant fonts de dades obertes…")
    open_data = check_open_data()
    for src in open_data:
        print(f"  {src['estat']} {src['nom']} ({src['registres']} registres)")

    print(f"\n🏗️  Comprovant {len(PROJECTES)} projectes…")
    project_results = check_projects(snapshots)

    save_snapshots(snapshots)
    print(f"\n💾 Snapshots guardats a {SNAPSHOT_FILE}")

    report = generate_report(project_results, open_data)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"📄 Informe generat: {REPORT_FILE}")

    canvis = sum(1 for r in project_results if r["canvi_web"])
    errors = sum(1 for r in project_results if r["error"])
    news   = sum(1 for r in project_results if r["noticies"])

    print(f"\n{'='*50}")
    print(f"✅ Fet! {len(project_results)} projectes revisats")
    print(f"   ⚠️  {canvis} canvis detectats")
    print(f"   📰 {news} projectes amb notícies")
    print(f"   ❌ {errors} errors")
    print(f"\nObre {REPORT_FILE} al navegador per veure l'informe complet.\n")

if __name__ == "__main__":
    main()
