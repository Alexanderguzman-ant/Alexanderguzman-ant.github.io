# -*- coding: utf-8 -*-
"""
¿Dónde se concentra la situación de calle en Chile y con qué se relaciona?
Análisis comunal con datos del Censo 2024.

QUÉ BUSCA ESTE ANÁLISIS
-----------------------
El siguiente análisis estadístico busca comprender el fenómeno de la situación
calle a partir de los datos territoriales disponibles. El mapa del observatorio
muestra DÓNDE están las 21.750 personas en situación de calle (PSC); aquí se
exploran posibles relaciones entre esa distribución y dos características de
cada comuna —su nivel de vulnerabilidad (IGVUST) y su carácter rural o urbano—
sin descartar que el tamaño de la población, por sí solo, pueda dar cuenta de
buena parte del patrón. Se trata de una exploración de asociaciones entre
territorios, no de una prueba de causas.

UN CONTEXTO QUE EL DATO NO CAPTURA
----------------------------------
El análisis etnográfico previo (caso de una comuna de Santiago) señala que
quienes viven en calle no son necesariamente originarios del territorio donde
fueron censados: hay trayectorias de movimiento, redes de apoyo y formas de
arraigo que hacen que una comuna reciba o albergue personas llegadas de otras
partes. Este análisis describe dónde se concentra el fenómeno; las razones de
esa concentración se interpretan a la luz de ese trabajo cualitativo.

CÓMO ESTÁ ARMADA LA MUESTRA (qué comunas entran a cada paso)
------------------------------------------------------------
  Punto de partida: las 346 comunas de Chile, cada una con su conteo de PSC,
                    su población censada, su cuartil de vulnerabilidad y su
                    clasificación territorial (rural / mixta / urbana).

  Pregunta 1 — ¿en qué comunas APARECE el fenómeno?
               Entran las 346 comunas. Cada una aporta un sí (202 comunas
               tienen al menos una persona en calle) o un no (144 no
               registran). Las 144 comunas en cero no se descartan: son la
               evidencia clave de que el fenómeno no está en todas partes.

  Pregunta 2 — ¿qué tan INTENSO es el fenómeno donde aparece?
               Entran solo las 202 comunas con PSC. Aquí lo que importa no es
               el conteo bruto sino la tasa: cuántas personas en calle hay por
               cada habitante de la comuna.

  Esta división en dos preguntas se conoce como modelo "hurdle" (de valla):
  primero se cruza la valla de existir, después se mide cuánto.

  Chequeos de robustez: los resultados principales se recalculan cuatro veces
  más para confirmar que no dependen de casos particulares:
    (a) sin las 51 comunas que el INE marca bajo umbral estadístico
        (poblaciones tan pequeñas que las tasas son inestables);
    (b) sin Colchane. Su alto número de personas en calle se asocia
        deductivamente a los movimientos migratorios: personas en tránsito
        que quedan a la espera en el paso fronterizo, muchas veces en
        condición de calle no por arraigo ni por la dinámica local, sino por
        la imposibilidad de seguir avanzando. Es un proceso distinto al del
        resto del país y merece ser mirado como caso propio;
    (c) sin el corredor fronterizo norte (Arica, Colchane, Pozo Almonte),
        atravesado por esos mismos flujos;
    (d) solo comunas urbanas, para observar la vulnerabilidad dentro de
        territorios comparables.

DECISIONES ANALÍTICAS (y sus razones)
-------------------------------------
  - Se modela el conteo de personas, no la tasa directamente. Comparar tasas
    "en bruto" trata igual a una comuna de 800 habitantes que a una de
    400.000; el modelo pondera cada comuna según su población, así las tasas
    inestables de comunas pequeñas pesan menos sin necesidad de borrarlas.
    (Técnicamente: Binomial Negativa con offset log(población); se verificó
    que la sobredispersión justifica NB sobre Poisson.)
  - La vulnerabilidad entra como cuartiles (1 = más vulnerable, 4 = menos),
    comparando cada cuartil contra el primero.
  - Cada región tiene su propio ajuste (efectos fijos), para que la
    comparación entre cuartiles sea "dentro" de cada macrozona y no entre
    norte y sur.
  - En la Pregunta 1 la clasificación urbana no entra como variable: el 100%
    de las comunas urbanas registra PSC, así que no hay variación que estimar.
    Ese hecho ES el resultado, y se reporta como tal.
  - Antártica (12202) no tiene clasificación territorial en el SIVUST; se
    asigna 'Rural' por tratarse de un asentamiento pequeño y aislado.
  - El umbral INE se toma del archivo de población (51 comunas). El JSON del
    mapa solo marca las 6 que además tienen PSC, porque ese aviso fue pensado
    para las tasas mostradas en pantalla.

LIMITACIONES DECLARADAS
-----------------------
  - La Pregunta 2 usa el modelo estándar sobre conteos positivos, sin el
    ajuste formal de truncamiento en cero: aproximación razonable para una
    exploración como esta, no para inferencia fina.
  - No se calculó autocorrelación espacial (I de Moran) por no contar con
    librerías espaciales en el entorno; los efectos regionales absorben parte
    de esa estructura, pero queda como limitación.
  - Los datos son un corte en el tiempo y a nivel comunal: lo que se reporta
    son asociaciones entre territorios, no causas ni comportamientos
    individuales (falacia ecológica).
  - El censo sub-registra poblaciones ocultas y el esfuerzo de conteo varía
    entre comunas; parte de los contrastes rurales podría deberse a la
    medición y no a una ausencia real del fenómeno.

Para reproducir:  python analisis_hurdle_psc.py   (dentro de la carpeta datos/)
Salida: resultados_hurdle_psc.csv — coeficientes de todas las variantes
        (OR = cuánto más probable es la presencia; IRR = cuánto mayor podría
        ser la tasa; en ambos casos, 1 significa "sin diferencia").
"""

import json
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

warnings.simplefilter('ignore')

# ---------------- Dataset ----------------
with open('../assets/observatorio/comuna_indicadores.json', encoding='utf-8') as f:
    datos = json.load(f)

df = pd.DataFrame(datos).T
df.index.name = 'cod_com'
df = df.reset_index()
df['cod_com'] = df['cod_com'].astype(int)
df['cod_reg'] = df['cod_com'] // 1000
for col in ['n_psc', 'pob_total', 'c_ig_nac', 'psc_x1000', 'edad_promedio',
            'pct_hombres', 'pct_discapacidad', 'escolaridad_promedio']:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df['bajo_umbral'] = df['bajo_umbral'].astype(bool)

ig = pd.read_excel('202510_igvust_comunal_cuartil.xlsx')[['cod_com', 'Clasificación']]
df = df.merge(ig, on='cod_com', how='left')
df['Clasificación'] = df['Clasificación'].fillna('Rural')  # Antártica (12202)

# Umbral INE: el JSON solo marca las 6 comunas bajo umbral CON PSC (para el * de la
# tasa); la exclusión de sensibilidad usa las 51 del archivo de población.
pob = pd.read_excel('poblacion_comunal_censo2024.xlsx')[['comuna', 'bajo_umbral']]
pob = pob.rename(columns={'comuna': 'cod_com', 'bajo_umbral': 'bajo_umbral_ine'})
df = df.merge(pob, on='cod_com', how='left')
df['bajo_umbral_ine'] = df['bajo_umbral_ine'].fillna(False).astype(bool)

df['presencia'] = (df['n_psc'] > 0).astype(int)
df['log_pob'] = np.log(df['pob_total'])
df['cuartil'] = df['c_ig_nac'].astype(int).astype(str)
df['clasif'] = df['Clasificación']

print('Dataset:', df.shape[0], 'comunas | con PSC:', df['presencia'].sum(),
      '| bajo_umbral:', df['bajo_umbral'].sum())

FORMULA = 'presencia ~ C(cuartil) + log_pob + C(cod_reg)'
FORMULA_NB = 'n_psc ~ C(cuartil) + C(clasif, Treatment(reference="Rural")) + log_pob + C(cod_reg)'
FORMULA_NB_URB = 'n_psc ~ C(cuartil) + log_pob + C(cod_reg)'  # variante solo urbanas

# ---------------- Ajuste de las dos partes ----------------
def ajustar(d, etiqueta):
    """Ajusta logit de presencia y NB2 de intensidad; retorna resumen de ambos."""
    res = {'variante': etiqueta, 'n': len(d), 'n_pos': int(d['presencia'].sum())}

    # Si la presencia es constante (solo urbanas: todas con PSC), el logit no
    # es estimable — ese hecho ES el resultado de la parte extensiva.
    logit = None
    if d['presencia'].nunique() > 1:
        logit = smf.logit(FORMULA, data=d).fit(disp=0)
        res['logit_pseudoR2'] = logit.prsquared

    pos = d[d['presencia'] == 1]
    formula_nb = FORMULA_NB if d['clasif'].nunique() > 1 else FORMULA_NB_URB
    nb = smf.negativebinomial(formula_nb, data=pos, offset=np.log(pos['pob_total'])).fit(disp=0)
    res['nb_alpha'] = nb.params.get('alpha', np.nan)
    res['nb_alpha_p'] = nb.pvalues.get('alpha', np.nan)
    return res, logit, nb


def irr_table(modelo, parte, variante):
    """Tabla de OR (logit) o IRR (NB) con IC 95%."""
    ci = modelo.conf_int()
    out = pd.DataFrame({
        'parte': parte,
        'variante': variante,
        'termino': modelo.params.index,
        'est': np.exp(modelo.params.values),
        'ic_inf': np.exp(ci[0].values),
        'ic_sup': np.exp(ci[1].values),
        'p': modelo.pvalues.values,
    })
    return out


# ---------------- Variantes ----------------
CORREDOR_NORTE = [15101, 1403, 1404]  # Arica, Colchane, Pozo Almonte

variantes = {
    'principal': df,
    'a_sin_bajo_umbral': df[~df['bajo_umbral_ine']],
    'b_sin_colchane': df[df['cod_com'] != 1403],
    'c_sin_corredor_norte': df[~df['cod_com'].isin(CORREDOR_NORTE)],
    'd_solo_urbanas': df[df['clasif'] == 'Urbana'],
}

tablas, resumenes, modelos = [], [], {}
for nombre, d in variantes.items():
    res, logit, nb = ajustar(d, nombre)
    resumenes.append(res)
    if logit is not None:
        tablas.append(irr_table(logit, '1_presencia_logit', nombre))
    tablas.append(irr_table(nb, '2_intensidad_nb', nombre))
    modelos[nombre] = (logit, nb)

resultados = pd.concat(tablas, ignore_index=True)
resultados.to_csv('resultados_hurdle_psc.csv', index=False)

# ---------------- Salida por consola ----------------
pd.set_option('display.width', 200)
print('\n=== RESUMEN DE VARIANTES ===')
print(pd.DataFrame(resumenes).round(3).to_string(index=False))

def show(parte, terminos=None):
    sub = resultados[resultados['parte'] == parte]
    if terminos:
        sub = sub[sub['termino'].isin(terminos)]
    piv = sub.pivot_table(index='termino', columns='variante', values='est').round(2)
    print(piv.to_string())

print('\n=== OR logit (presencia) — cuartil ===')
print('(clasif excluida del logit: Urbana separa perfectamente — el 100% registra PSC)')
show('1_presencia_logit', ['C(cuartil)[T.2]', 'C(cuartil)[T.3]', 'C(cuartil)[T.4]', 'log_pob'])

print('\n=== IRR NB (intensidad) — cuartil y clasificación ===')
show('2_intensidad_nb', ['C(cuartil)[T.2]', 'C(cuartil)[T.3]', 'C(cuartil)[T.4]',
                         'C(clasif, Treatment(reference="Rural"))[T.Mixta]',
                         'C(clasif, Treatment(reference="Rural"))[T.Urbana]', 'log_pob'])

print('\n=== IRR con IC95% y p — variante principal ===')
pp = resultados[(resultados['variante'] == 'principal') &
                (~resultados['termino'].str.startswith('C(cod_reg)'))].round(3)
print(pp[['parte', 'termino', 'est', 'ic_inf', 'ic_sup', 'p']].to_string(index=False))

# ---------------- Diagnósticos ----------------
logit_p, nb_p = modelos['principal']
print('\n=== DIAGNÓSTICOS (variante principal) ===')
print('Logit pseudo-R2:', round(logit_p.prsquared, 3))
print('NB alpha:', round(nb_p.params['alpha'], 3),
      '| p(alpha=0):', format(nb_p.pvalues['alpha'], '.2e'),
      '-> sobredispersión significativa si p<0.05 (justifica NB sobre Poisson)')

# Influencia en logit: distancia de Cook
inf = logit_p.get_influence()
cooks = inf.cooks_distance[0]
top_inf = pd.DataFrame({'comuna': df['comuna'].values, 'cook': cooks}).nlargest(5, 'cook')
print('\nComunas más influyentes en logit (Cook):')
print(top_inf.round(4).to_string(index=False))

print('\nResultados guardados en resultados_hurdle_psc.csv')
