"""Regenera assets/observatorio/comuna_indicadores.json desde los microdatos
del Censo 2024 y la cartilla IGVUST comunal (MDS).

Uso (desde esta carpeta):

    python generar_comuna_indicadores.py <ruta/personas_censo2024.parquet>

Entradas:

  - personas_censo2024.parquet  Microdatos de personas del Censo 2024 (INE).
    No se versiona: se descarga desde https://www.ine.gob.cl/ (base de datos
    del Censo 2024) y se convierte a parquet por columnas. Se esperan al menos
    las columnas: comuna, tipo_operativo, sexo, edad, discapacidad,
    escolaridad, comuna_bajo_umbral.
  - 202510_igvust_comunal_cuartil.xlsx  Clasificacion comunal IGVUST (MDS):
    aporta nombres de comuna/region, cuartil nacional (c_ig_nac) y
    ranking nacional (rank_nac).

Definiciones (identicas a las del analisis original en R):

  - PSC: personas con tipo_operativo == 1 (operativo personas en situacion
    de calle).
  - edad_promedio / escolaridad_promedio: media comunal sobre valores >= 0
    (los codigos negativos son "no sabe/no responde"), redondeo a 1 decimal.
  - pct_hombres: share de sexo == 1 sobre el total PSC de la comuna.
  - pct_discapacidad: share de discapacidad == 1 sobre quienes declaran
    discapacidad en {1, 2}.
  - psc_x1000: 1000 * n_psc / poblacion total censada de la comuna.
  - bajo_umbral: True si la comuna esta marcada con comuna_bajo_umbral == 1
    en el microdato (denominadores pequenos, tasa inestable segun INE);
    None en comunas sin PSC (la tasa no aplica).

Salida: ../assets/observatorio/comuna_indicadores.json (una entrada por
comuna, ordenada por codigo CUT).
"""

import json
import math
import sys

import pandas as pd

PARQUET = sys.argv[1] if len(sys.argv) > 1 else "personas_censo2024.parquet"
IGVUST = "202510_igvust_comunal_cuartil.xlsx"
SALIDA = "../assets/observatorio/comuna_indicadores.json"

COLS = ["comuna", "tipo_operativo", "sexo", "edad", "discapacidad",
        "escolaridad", "comuna_bajo_umbral"]


def media_r(vals):
    """Media con suma exacta (math.fsum) y redondeo a 1 decimal.

    La suma exacta evita que el orden de acumulacion flotante cambie el
    redondeo en medias que caen justo en un empate x.x5 (caso observado:
    Alto Hospicio, 905/100 = 9.05, que el pipeline original en R redondeo
    a 9.1).
    """
    vals = [int(v) for v in vals]
    if not vals:
        return None
    return round(math.fsum(vals) / len(vals), 1)


def agrega_psc(g):
    edad_ok = g.loc[(g["edad"] >= 0) & g["edad"].notna(), "edad"]
    esc_ok = g.loc[(g["escolaridad"] >= 0) & g["escolaridad"].notna(), "escolaridad"]
    n_disc_valid = int(g["discapacidad"].isin([1, 2]).sum())
    return pd.Series({
        "n_psc": len(g),
        "edad_promedio": media_r(edad_ok),
        "pct_hombres": round(100 * int((g["sexo"] == 1).sum()) / len(g), 1),
        "pct_discapacidad": (round(100 * int((g["discapacidad"] == 1).sum()) / n_disc_valid, 1)
                             if n_disc_valid else None),
        "escolaridad_promedio": media_r(esc_ok),
    })


def main():
    censo = pd.read_parquet(PARQUET, columns=COLS)
    print(f"microdatos: {len(censo):,} personas")

    pob_total = censo.groupby("comuna").size()
    psc = censo[censo["tipo_operativo"] == 1]
    print(f"PSC: {len(psc):,} personas")
    ag = psc.groupby("comuna").apply(agrega_psc, include_groups=False)

    bajo_umbral = set(censo.loc[censo["comuna_bajo_umbral"] == 1, "comuna"].unique())

    ig = pd.read_excel(IGVUST)[["cod_com", "Comuna", "Region", "c_ig_nac", "rank_nac"]]

    salida = {}
    for _, r in ig.sort_values("cod_com").iterrows():
        cod = int(r["cod_com"])
        if cod in ag.index:
            a = ag.loc[cod]
            n_psc = int(a["n_psc"])
            # pandas convierte None a NaN en columnas float; restaurar None
            edad, pct_h, pct_d, esc = (
                None if pd.isna(a[c]) else a[c]
                for c in ("edad_promedio", "pct_hombres", "pct_discapacidad", "escolaridad_promedio")
            )
        else:
            n_psc, edad, pct_h, pct_d, esc = 0, None, None, None, None
        pob = int(pob_total.get(cod, 0))
        salida[str(cod)] = {
            "comuna": r["Comuna"],
            "region": r["Region"],
            "n_psc": n_psc,
            "edad_promedio": edad,
            "pct_hombres": pct_h,
            "pct_discapacidad": pct_d,
            "escolaridad_promedio": esc,
            "c_ig_nac": int(r["c_ig_nac"]),
            "rank_nac": int(r["rank_nac"]),
            "pob_total": pob,
            "psc_x1000": round(1000 * n_psc / pob, 2) if pob else None,
            "bajo_umbral": (cod in bajo_umbral) if n_psc > 0 else None,
        }

    with open(SALIDA, "w", encoding="utf-8", newline="\n") as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)
    print(f"escrito {SALIDA}: {len(salida)} comunas")


if __name__ == "__main__":
    main()
