"""
Vistas del panel de Redes Neuronales, para el rol Administrador.

Dos endpoints:
  - `/administracion/redes/modelos/`    : estado de las redes (metricas de los
    modelos entrenados). Proxy resiliente al microservicio ML.
  - `/administracion/redes/resultados/` : resultados agregados del Knowledge
    Tracing sobre los estudiantes, globales y desglosados por profesor.

El "modelo de conocimiento" (ModeloConocimiento.conceptos) guarda por concepto
{intentos, correctas, nivel, secuencia, p_dominado}. Aqui se agrega para dar
una vista de sistema al administrador.
"""

import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.permissions.permisos_rol import EsAdministrador
from apps.motor_adaptativo.models import ModeloConocimiento


# Nombres legibles de los 3 niveles de dominio.
_NIVEL_TEXTO = {1: "debil", 2: "desarrollo", 3: "dominado"}


def _nuevo_acumulador() -> dict:
    """Acumulador de niveles y P(dominado) reutilizable (global o por profesor)."""
    return {
        "estudiantes": set(),
        "conceptos_evaluados": 0,
        "niveles": {1: 0, 2: 0, 3: 0},
        "pdom_sum": 0.0,
        "pdom_n": 0,
        "nivel_sum": 0,
    }


def _resumen_acumulador(acc: dict) -> dict:
    """Convierte un acumulador en su forma serializable (promedios, distribucion)."""
    conceptos = acc["conceptos_evaluados"]
    return {
        "estudiantes": len(acc["estudiantes"]),
        "conceptos_evaluados": conceptos,
        "distribucion_niveles": {
            "debil": acc["niveles"][1],
            "desarrollo": acc["niveles"][2],
            "dominado": acc["niveles"][3],
        },
        "p_dominado_promedio": round(acc["pdom_sum"] / acc["pdom_n"], 4) if acc["pdom_n"] else None,
        "nivel_promedio": round(acc["nivel_sum"] / conceptos, 2) if conceptos else None,
    }


@extend_schema(
    tags=["Analítica"],
    summary="Estado de las redes neuronales (Administrador)",
    description=(
        "Proxy al microservicio ML: lista los modelos entrenados (BKT/DKT) con sus "
        "métricas (AUC, accuracy, F1, RMSE). Si el microservicio no está disponible, "
        "responde disponible=false. Solo accesible para el Administrador."
    ),
    responses={
        200: OpenApiResponse(description="Estado y métricas de los modelos"),
        403: OpenApiResponse(description="Solo el administrador puede acceder"),
    },
)
class VistaRedesModelos(APIView):
    permission_classes = [EsAdministrador]

    def get(self, request):
        url = getattr(settings, "ML_SERVICE_URL", "") or ""
        if not url:
            return Response({"disponible": False, "modelo_activo": None, "modelos": []})
        try:
            r = requests.get(f"{url.rstrip('/')}/modelos", timeout=3)
            r.raise_for_status()
            data = r.json()
            return Response({"disponible": True, **data})
        except requests.RequestException:
            return Response({"disponible": False, "modelo_activo": None, "modelos": []})


@extend_schema(
    tags=["Analítica"],
    summary="Resultados del Knowledge Tracing (Administrador)",
    description=(
        "Agrega el modelo de conocimiento de todos los estudiantes: distribución de "
        "niveles de dominio, P(dominado) promedio y desglose por profesor y por "
        "concepto. Solo accesible para el Administrador."
    ),
    responses={
        200: OpenApiResponse(description="Resultados agregados del Knowledge Tracing"),
        403: OpenApiResponse(description="Solo el administrador puede acceder"),
    },
)
class VistaRedesResultados(APIView):
    permission_classes = [EsAdministrador]

    def get(self, request):
        registros = ModeloConocimiento.objects.select_related(
            "estudiante", "examen__curso__docente"
        )

        glob = _nuevo_acumulador()
        por_profesor = {}   # docente_id -> {"nombre":..., "acc": acumulador}
        conceptos_acc = {}  # nombre -> {"n":..,"nivel_sum":..,"pdom_sum":..,"pdom_n":..}

        for mc in registros:
            docente = mc.examen.curso.docente
            if docente.id not in por_profesor:
                nombre = f"{docente.first_name} {docente.first_last_name}".strip() or docente.email
                por_profesor[docente.id] = {"nombre": nombre, "acc": _nuevo_acumulador()}
            pacc = por_profesor[docente.id]["acc"]

            glob["estudiantes"].add(mc.estudiante_id)
            pacc["estudiantes"].add(mc.estudiante_id)

            for nombre_concepto, datos in (mc.conceptos or {}).items():
                nivel = int(datos.get("nivel", 2))
                pdom = datos.get("p_dominado")

                for acc in (glob, pacc):
                    acc["conceptos_evaluados"] += 1
                    acc["niveles"][nivel] = acc["niveles"].get(nivel, 0) + 1
                    acc["nivel_sum"] += nivel
                    if pdom is not None:
                        acc["pdom_sum"] += pdom
                        acc["pdom_n"] += 1

                ca = conceptos_acc.setdefault(
                    nombre_concepto, {"n": 0, "nivel_sum": 0, "pdom_sum": 0.0, "pdom_n": 0}
                )
                ca["n"] += 1
                ca["nivel_sum"] += nivel
                if pdom is not None:
                    ca["pdom_sum"] += pdom
                    ca["pdom_n"] += 1

        # Ranking de conceptos por nivel promedio (mas debiles primero)
        conceptos = sorted(
            (
                {
                    "concepto": nombre,
                    "evaluaciones": c["n"],
                    "nivel_promedio": round(c["nivel_sum"] / c["n"], 2) if c["n"] else None,
                    "p_dominado_promedio": round(c["pdom_sum"] / c["pdom_n"], 4) if c["pdom_n"] else None,
                }
                for nombre, c in conceptos_acc.items()
            ),
            key=lambda x: (x["nivel_promedio"] if x["nivel_promedio"] is not None else 99),
        )

        profesores = sorted(
            (
                {"profesor": p["nombre"], **_resumen_acumulador(p["acc"])}
                for p in por_profesor.values()
            ),
            key=lambda x: x["estudiantes"],
            reverse=True,
        )

        return Response({
            "global": _resumen_acumulador(glob),
            "conceptos": conceptos,
            "por_profesor": profesores,
        })
