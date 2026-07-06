# Microservicio ML — Knowledge Tracing (Lairn)

Servicio de estimación de dominio de conocimiento para el motor adaptativo de
Lairn. Sirve un modelo **BKT (Bayesian Knowledge Tracing)** entrenado y expone
una API REST que el backend Django consume para decidir la dificultad y el
siguiente concepto a evaluar.

## Estructura

```
microservicio_ml/
├── app/                     # EL SERVICIO (FastAPI) — lo que corre en producción
│   ├── main.py              #   crea la app (app factory)
│   ├── config.py            #   ajustes: rutas, umbrales, versión
│   ├── schemas.py           #   contratos Pydantic (entrada/salida)
│   ├── api/rutas.py         #   endpoints /health y /predict
│   └── servicios/           #   lógica: predictor.py + preprocesamiento.py
│
├── ml/                      # INVESTIGACIÓN / ENTRENAMIENTO (no va en la imagen)
│   ├── modelos/             #   definiciones de modelos: bkt.py, dkt.py
│   ├── datos/               #   generadores / descarga de datasets
│   └── notebooks/           #   01_bkt · 02_dkt · 03_sakt
│
├── artefactos/              # MODELOS ENTRENADOS (.pkl + config + métricas)
│   ├── concept_vocab.json   #   mapa concepto (texto libre) → skill entrenado
│   ├── bkt_sintetico/       #   ← el que sirve el servicio por defecto
│   ├── bkt_real/  dkt_real/  dkt_sintetico/
│
├── requirements/            # base.txt · api.txt (servir) · train.txt (entrenar)
├── scripts/migrar_artefactos.py
├── tests/
└── Dockerfile · .dockerignore
```

**Separación clave:** `app/` (servir, ligero, sin PyTorch) vs `ml/` (entrenar,
con PyTorch/Jupyter). La imagen de Docker solo empaqueta lo primero.

## Cómo se ejecuta

Forma parte del `docker-compose.yml` de la raíz del monorepo:

```bash
docker compose up -d ml
```

- Dentro de Docker escucha en `http://ml:8001` (lo que usa el backend).
- Publicado en el host en `http://localhost:8002`.

### Local (sin Docker)

```bash
pip install -r requirements/api.txt
uvicorn app.main:app --reload --port 8001
```

## API

| Método | Ruta       | Descripción |
|--------|------------|-------------|
| GET    | `/health`  | Estado del servicio y skills disponibles. |
| POST   | `/predict` | Estima dominio por concepto y sugiere dificultad. |
| GET    | `/docs`    | Documentación interactiva (Swagger). |

### `POST /predict`

```json
{
  "interacciones": [
    {"concepto": "Derivada del seno", "correcto": true},
    {"concepto": "Derivada del seno", "correcto": false}
  ]
}
```

Respuesta (resumen): por cada concepto `reconocido`, `p_dominado`, `nivel`
(1=débil, 2=en desarrollo, 3=dominado) y una `dificultad_sugerida` global.
Los conceptos fuera del vocabulario entrenado devuelven `reconocido: false`.

## Modelos

| Modelo          | Conceptos                                   | AUC  |
|-----------------|---------------------------------------------|------|
| `bkt_sintetico` | derivada_seno, derivada_coseno, regla_cadena | ~0.71 |
| `bkt_real`      | 10 skills de ASSISTments                     | ~0.71 |
| `dkt_*`         | LSTM (PyTorch)                               | ~0.74 |

El servicio usa **`bkt_sintetico`** por defecto porque sus 3 conceptos de
derivadas se pueden mapear a exámenes reales de la app. Se puede cambiar con la
variable de entorno `ML_MODELO`.

## Entrenar / re-entrenar

Los modelos se entrenan desde los notebooks en `ml/notebooks/`:

```bash
pip install -r requirements/train.txt
jupyter lab ml/notebooks/
```

> Si se reorganizan los módulos de `ml/modelos/`, re-guarda los `.pkl` con
> `python scripts/migrar_artefactos.py` para que apunten a la nueva ruta.

## Pruebas

```bash
pip install -r requirements/api.txt pytest
pytest
```
