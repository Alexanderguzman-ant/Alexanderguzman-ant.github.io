# Portafolio — Alexander Guzmán Yañez

Sitio estático (HTML/CSS/JS, sin servidor ni build) con mi presentación
profesional y el Observatorio territorial de situación de calle.

## Situación de calle en Chile: de la etnografía a los datos

Este proyecto nace del trabajo de campo. Primero observé la problemática
etnográficamente —una temporada acompañando a personas en situación de calle
en una comuna de Santiago— y esa experiencia dejó preguntas que el terreno
solo no podía responder: ¿el patrón que veía en esa comuna era local o
general? ¿dónde se concentra el fenómeno a escala nacional y con qué se
relaciona?

El recorrido del proyecto sigue esa intuición, en tres movimientos:

1. **Etnografía** (`caso-situacion-calle.html`). El trabajo cualitativo
   muestra que quienes viven en calle no son necesariamente originarios del
   territorio donde se les encuentra: hay trayectorias de movimiento, redes
   de apoyo y formas de arraigo que hacen que una comuna reciba o expulse
   personas. La calle no se distribuye al azar; se instala donde es tolerada.
2. **Microdatos** (`observatorio.html`). Para contrastar esa experiencia con
   el fenómeno a escala macro, procesé los microdatos del Censo 2024 (INE):
   18,5 millones de personas censadas, de las cuales 21.750 fueron registradas
   en situación de calle. El observatorio es un mapa comunal interactivo
   (coroplético por cuartil de vulnerabilidad IGVUST del MDS, círculos
   proporcionales al conteo, tasas por 1.000 habitantes) con indicadores
   comunales, regionales y nacionales.
3. **Contraste y matiz** (`datos/analisis_hurdle_psc.py`). El análisis
   estadístico comunal (modelo hurdle: dónde aparece el fenómeno y con qué
   intensidad) pone a prueba la lectura etnográfica y la matiza desde un
   ángulo más estructural.

### Resultados principales

- La situación de calle es un fenómeno **estructuralmente urbano**: el 100%
  de las comunas urbanas registra al menos una persona en calle; 144 comunas
  (mayoritariamente rurales) no registran ninguna.
- La **vulnerabilidad comunal (IGVUST) no explica el patrón**: la calle no se
  distribuye según la pobreza del territorio sino según su estructura urbana.
  El resultado resiste cuatro chequeos de robustez.
- **Colchane** es un caso anómalo y propio: su altísima tasa se asocia a los
  flujos migratorios en el paso fronterizo, un proceso distinto al del resto
  del país.
- El diálogo entre ambos métodos es el punto: los datos dicen *dónde* se
  concentra el fenómeno; la etnografía aporta el *mecanismo* (restricciones
  de arraigo y tolerancia institucional de cada territorio). La tolerancia no
  produce la calle — se relaciona con su **visibilidad**: dónde puede
  instalarse, permanecer y ser contada.

## Reproducibilidad

Todo el proceso desde los microdatos hasta el mapa está versionado:

```
datos/
├── 202510_igvust_comunal_cuartil.xlsx    # Clasificación IGVUST comunal (MDS)
├── poblacion_comunal_censo2024.xlsx      # Población por comuna, Censo 2024
├── generar_comuna_indicadores.py         # Microdatos Censo 2024 → JSON del mapa
├── analisis_hurdle_psc.py                # Modelo hurdle comunal (presencia e intensidad)
├── resultados_hurdle_psc.csv             # Coeficientes de todas las variantes
└── resultados_hurdle_diagnosticos.csv    # Diagnósticos y comunas influyentes
```

- Los microdatos del Censo 2024 no se versionan (se descargan del INE);
  `generar_comuna_indicadores.py` documenta el formato esperado y reproduce
  `assets/observatorio/comuna_indicadores.json` byte a byte.
- Las geometrías comunales (`assets/observatorio/comunas.geojson`) provienen
  de la División Político-Administrativa oficial (SUBDERE/MINVU),
  simplificadas preservando topología.
- Para replicar el análisis: `python analisis_hurdle_psc.py` dentro de
  `datos/` (el script documenta decisiones analíticas y limitaciones).

## Estructura del sitio

```
├── index.html                 # Inicio, sobre mí, proyectos
├── caso-situacion-calle.html  # Caso de estudio etnográfico
├── observatorio.html          # Observatorio territorial (mapa + indicadores)
├── styles.css                 # Estilo
├── assets/observatorio/       # GeoJSON comunal + indicadores por comuna
├── datos/                     # Insumos, pipeline y resultados del análisis
└── img/                       # Fotografías
```

## Publicación

El sitio es estático: basta servir la carpeta tal cual.
Está pensado para GitHub Pages (`usuario.github.io`), pero funciona en
cualquier hosting estático (Netlify, Cloudflare Pages, etc.).
