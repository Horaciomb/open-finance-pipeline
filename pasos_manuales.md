# Pasos manuales — Proyecto 3 (fuera de Claude Code)

Reutilizas la misma instancia Supabase de los proyectos 1 y 2. Hay UN paso
nuevo que no existía antes: conseguir la API key de FRED.

---

## DURANTE — mientras Claude Code trabaja

### 5. Reutilizar tu DATABASE_URL (1 min)

Misma instancia de los proyectos 1 y 2. Reúsalo del .env de cualquiera de esos.

### 6. Crear el .env local (2 min)

```
DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-...pooler.supabase.com:5432/postgres
FRED_API_KEY=tu_key_de_32_caracteres
```

⚠️ Verifica que `.env` esté en `.gitignore`.

### 7. Ejecutar bootstrap.sql (2 min)

Cuando Claude Code genere `sql/bootstrap.sql` (crea `openfin_raw` y `openfin`):

- Supabase → SQL Editor → pega → Run
- Verifica en Table Editor, cambiando el esquema a `openfin_raw`.
- Esto no toca tus esquemas fx, econ, econ_raw, polla ni public.

### 8. Probar el EL localmente (10 min)

```bash
pip install -r requirements.txt
python -m src.el.pipeline --source prices   # yfinance, diario
python -m src.el.pipeline --source fred     # FRED, semanal
```

(los nombres exactos de los comandos los define Claude Code; ajusta si difieren)
Revisa en Supabase que `openfin_raw.prices` y `openfin_raw.fred_observations`
tengan filas.

### 9. Probar dbt localmente (10 min)

```bash
cd dbt
dbt debug
dbt build
dbt docs generate && dbt docs serve
```

Presta atención especial al **source cross-schema** `stg_fx_rates` — verifica
en el lineage que efectivamente esté leyendo de `fx.exchange_rates` (del
proyecto 1) y no fallando por permisos. Si tu rol de conexión no tiene acceso
de lectura a `fx`, puede que necesites un GRANT adicional (avísame si pasa).

### 10. Probar el frontend localmente (5 min)

```bash
cd frontend
npm install
cp .env.example .env   # configura VITE_API_URL=http://localhost:8000
npm run dev
```

Ábrelo en el navegador y confirma que el gráfico y las tarjetas rendericen
(aunque sea con la API corriendo en local, `uvicorn src.api.main:app --reload`
en otra terminal).

---

## DESPUÉS — deploy y publicación

### 11. GitHub Secrets (3 min)

- Repo → Settings → Secrets and variables → Actions
- Crea: `DATABASE_URL` y `FRED_API_KEY`

### 12. GitHub Pages para dbt docs (5 min)

- Settings → Pages → Source: GitHub Actions (igual que proyecto 2)
- URL resultante: `https://horaciomb.github.io/open-finance-pipeline/`

### 13. Deploy de la API en Render (10 min)

- render.com → New → Web Service → conecta el repo
- Build: `pip install -r requirements.txt`
- Start: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
- Environment → `DATABASE_URL`, `FRED_API_KEY`
- Verifica `/docs`

### 14. Deploy del dashboard en Vercel (10 min)

- vercel.com → Add New Project → selecciona `open-finance-pipeline`
- **Root Directory: `frontend`** (importante, el repo tiene Python + Node mezclados)
- Environment Variables → `VITE_API_URL` = la URL de tu API en Render
- Deploy → te da una URL tipo `open-finance-pipeline.vercel.app`

### 15. Probar los workflows (5 min)

- ci.yml: verde en cada push
- pipeline-daily.yml: "Run workflow" manual → confirma que carga precios
- pipeline-weekly.yml: "Run workflow" manual → confirma que carga FRED + dbt build
- dbt-docs.yml: confirma que las docs se actualizan en Pages

### 16. Añadir el proyecto al portfolio (5 min)

En tu `projects.json`:

- title: "Open Finance Pipeline — Medallion Architecture"
- description: pipeline con arquitectura Bronze/Silver/Gold combinando Yahoo
  Finance, FRED y tipo de cambio de Bolivia, con dbt, API y dashboard React.
- tech: Python, dbt, PostgreSQL, FastAPI, React, Recharts, Vercel, Render,
  GitHub Actions, Medallion Architecture
- links: repo, API en Render, dashboard en Vercel, dbt docs en GitHub Pages
  → CUATRO links públicos, más que cualquier otro proyecto tuyo.
- Screenshot: el dashboard con el gráfico y las tarjetas.

---

## Checklist rápido

- [ ] Repo creado y clonado
- [ ] CLAUDE.md en la raíz
- [ ] Python 3.11+ y Node 18+ confirmados
- [ ] FRED_API_KEY obtenida (nuevo paso — cuenta gratis en FRED)
- [ ] DATABASE_URL reutilizado
- [ ] .env con ambas credenciales, en .gitignore
- [ ] bootstrap.sql ejecutado → openfin_raw y openfin
- [ ] EL de precios (yfinance) probado localmente
- [ ] EL de FRED probado localmente
- [ ] dbt debug + dbt build verdes
- [ ] Source cross-schema a fx.exchange_rates confirmado funcionando
- [ ] dbt docs explorado (lineage con la referencia cross-schema visible)
- [ ] Frontend corriendo en local contra la API local
- [ ] GitHub Secrets (DATABASE_URL + FRED_API_KEY)
- [ ] GitHub Pages activado para dbt docs
- [ ] API deployada en Render
- [ ] Dashboard deployado en Vercel (root directory = frontend)
- [ ] Los 4 workflows probados
- [ ] Proyecto añadido al portfolio con 4 links

---

## Por qué este proyecto cierra el círculo

Con los 3 proyectos completos, tu portafolio demuestra: ETL simple (P1) → EL+dbt
con modelado dimensional (P2) → arquitectura Medallion completa con múltiples
fuentes, reutilización de datos entre proyectos, y una capa de visualización
(P3). Eso no es "hice 3 proyectos sueltos" — es una progresión coherente que
cualquier Data Engineer Senior reconoce como buena práctica real.
