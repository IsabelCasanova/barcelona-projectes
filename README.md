# Barcelona Projectes — Manteniment mensual

Site: **https://isabelcasanova.github.io/barcelona-projectes**

## Arxius

| Arxiu | Funció |
|---|---|
| `index.html` | El site complet (mapa + llista) |
| `actualitzar.py` | Script de comprovació mensual |
| `publicar.py` | Puja `index.html` a GitHub Pages |
| `snapshots.json` | Historial de canvis (es genera sol) |
| `informe.html` | Últim informe generat (es genera sol) |

## Flux de treball mensual (15 min)

### 1. Instal·la dependències (només el primer cop)
```bash
pip install requests beautifulsoup4
```

### 2. Executa la comprovació
```bash
python3 actualitzar.py
```
Tarda uns 5 minuts. Al final obre `informe.html` al navegador.

### 3. Revisa l'informe
- **⚠️ Canvis detectats** → obre la web oficial i actualitza `index.html`
- **📰 Notícies** → comprova si hi ha canvis d'estat importants
- **❌ Errors** → webs temporalment caigudes, comprova manualment

### 4. Actualitza `index.html` si cal
Edita els camps que hagin canviat (inversió, any de fi, estat, descripció).

### 5. Publica a GitHub Pages
```bash
export GITHUB_TOKEN="el_teu_token"
python3 publicar.py
```
O posa el token directament dins `publicar.py`.

## Fonts de dades per promotor

| Promotor | Font oficial | API/Portal |
|---|---|---|
| Ajuntament BCN | opendata-ajuntament.barcelona.cat | ✅ Sí |
| Generalitat | dadesobertes.gencat.cat | ✅ Sí |
| ATM | atm.cat/projectes | ❌ Manual |
| FGC | fgc.cat/projectes | ❌ Manual |
| Adif / Estat | contrataciondelestado.es | ✅ Atom feed |
| AENA | aena.es | ❌ Manual |
| Port de Barcelona | portdebarcelona.cat | ❌ Manual |
| FC Barcelona | fcbarcelona.es | ❌ Manual |

## Afegir un projecte nou

1. Edita `index.html` — afegeix l'objecte al array `P` amb:
   - `id`, `name`, `inv`, `ini`, `fin`, `cat`, `promotor`
   - `lat`, `lng` (coordenades exactes)
   - `web`, `p1`, `p2` (web oficial + cerques de premsa)
   - `desc` (descripció breu)

2. Edita `actualitzar.py` — afegeix el projecte a la llista `PROJECTES`

3. Publica: `python3 publicar.py`
