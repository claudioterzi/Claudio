# GENESI-006 — CadQuery Esempi Pratici per Pocket NC V2-50CHK
*Completato automaticamente da Agente Orario SDQ-1 — 2026-06-18*

---

## 1. Setup Ambiente

### Installazione CadQuery
```bash
# Opzione A: conda (raccomandato per stabilità)
conda install -c cadquery -c conda-forge cadquery

# Opzione B: pip (più rapido, alcuni moduli 3D richiedono dipendenze aggiuntive)
pip install cadquery cadquery-massembly

# Verifica
python -c "import cadquery as cq; print(cq.__version__)"
```

### Visualizzazione interattiva
```bash
# CQ-Editor (IDE grafico per CadQuery)
conda install -c cadquery -c conda-forge cq-editor

# Oppure in Jupyter
pip install jupyter cadquery-jupyter
```

### Per G-code
```bash
# FreeCAD (per Path workbench + post-processor Pocket NC)
# Scarica da: https://www.freecad.org/

# Alternativa Python: nc-utils per manipolazione G-code
pip install nc-utils
```

---

## 2. Struttura Base di un Pezzo CadQuery

```python
import cadquery as cq

# Concetti fondamentali:
# - Workplane: piano di lavoro (XY, XZ, YZ o faccia del solido)
# - Sketch: profilo 2D su workplane
# - 3D operation: extrude, revolve, sweep, loft

# Esempio base: cubo con smusso
pezzo = (
    cq.Workplane("XY")          # Parte dal piano XY
    .box(50, 30, 15)             # Crea un box 50×30×15mm
    .edges("|Z")                 # Seleziona spigoli verticali
    .chamfer(2)                  # Smussa di 2mm
    .faces(">Z")                 # Seleziona faccia superiore
    .workplane()                 # Nuovo piano di lavoro
    .circle(8)                   # Profilo circolare
    .cutThruAll()                # Foro passante
)

# Esporta
cq.exporters.export(pezzo, "pezzo_base.step")  # STEP per CAM
cq.exporters.export(pezzo, "pezzo_base.stl")   # STL per preview
```

---

## 3. Esempio 1 — Anello / Gioiello Base

```python
"""
Anello sigillo in alluminio — adatto per fresatura 5 assi Pocket NC
Dimensioni: diametro esterno 22mm, diametro interno 18mm, altezza 8mm
"""
import cadquery as cq

def crea_anello(
    diam_esterno: float = 22.0,
    diam_interno: float = 18.0,
    altezza: float = 8.0,
    profondita_incisione: float = 1.5,
    testo: str = "SDQ-1"
) -> cq.Workplane:
    
    # Corpo principale: tubo
    anello = (
        cq.Workplane("XY")
        .circle(diam_esterno / 2)
        .circle(diam_interno / 2)
        .extrude(altezza)
    )
    
    # Smusso superiore e inferiore
    anello = (
        anello
        .edges("%Circle and >Z")   # Spigolo circolare superiore
        .chamfer(0.8)
        .edges("%Circle and <Z")   # Spigolo circolare inferiore
        .chamfer(0.8)
    )
    
    # Incisione testo sulla superficie esterna (simulata come tasca)
    # Nota: per testo reale usare cq.text() con extrude negativo
    anello = (
        anello
        .faces(">Z")
        .workplane()
        .text(testo, fontsize=3.5, distance=-profondita_incisione)
    )
    
    return anello

anello = crea_anello()
cq.exporters.export(anello, "anello_sdq1.step")
print("Anello creato: anello_sdq1.step")

# Note per Pocket NC:
# - Materiale consigliato: alluminio 6061-T6 o ottone CZ121
# - Fissaggio: chuck 4 griffe o fixture custom
# - Utensile esterno: end mill 2mm per incisione testo
# - Strategia: contornatura esterna + incisione + foro interno
```

---

## 4. Esempio 2 — Componente Meccanico con Tasche e Fori

```python
"""
Piastra supporto sensore — componente meccanico con tasche e fori di montaggio
Dimensioni: 80×50×12mm, alluminio
"""
import cadquery as cq

def crea_piastra_sensore(
    lunghezza: float = 80.0,
    larghezza: float = 50.0,
    spessore: float = 12.0,
) -> cq.Workplane:
    
    # Corpo base
    piastra = (
        cq.Workplane("XY")
        .box(lunghezza, larghezza, spessore, centered=[True, True, False])
        .edges("|Z")
        .fillet(3.0)  # Raccorda spigoli verticali
    )
    
    # Tasca centrale per alloggiamento sensore
    piastra = (
        piastra
        .faces(">Z")
        .workplane()
        .rect(40, 25)
        .cutBlind(-6.0)  # Tasca profonda 6mm
    )
    
    # Raccorda il fondo della tasca
    piastra = (
        piastra
        .faces(">Z[1]")  # Fondo tasca
        .edges()
        .fillet(1.0)
    )
    
    # 4 fori M3 di montaggio agli angoli
    piastra = (
        piastra
        .faces(">Z")
        .workplane()
        .pushPoints([
            (28, 18), (-28, 18),
            (28, -18), (-28, -18)
        ])
        .hole(3.2, 12.0)  # Foro passante diametro 3.2mm per vite M3
    )
    
    # 2 fori M4 per fissaggio principale
    piastra = (
        piastra
        .faces(">Z")
        .workplane()
        .pushPoints([(0, 20), (0, -20)])
        .cboreHole(4.2, 8.0, 4.0)  # Foro con counterbore per testa vite
    )
    
    return piastra

piastra = crea_piastra_sensore()
cq.exporters.export(piastra, "piastra_sensore.step")

# Note per Pocket NC:
# - Strategia: face milling → tasca centrale → foratura
# - Sequenza utensili: end mill 8mm (sgrossatura), end mill 4mm (finitura tasca), 
#   drill 3.2mm e 4.2mm (foratura)
# - Fissaggio: morsa parallela, pezzi su paralleli
```

---

## 5. Esempio 3 — Forma Organica con Spline

```python
"""
Manico ergonomico — forma organica generata con loft tra profili
Lunghezza: 120mm, adatto per fresatura 5 assi (necessaria per superfici curve)
"""
import cadquery as cq
from cadquery import Edge, Wire, Solid

def crea_manico_ergonomico() -> cq.Workplane:
    """Crea forma organica con loft tra profili ellittici a diverse altezze."""
    
    # Profili a diverse altezze (z = 0, 40, 80, 120mm)
    profili = []
    
    # Profilo 1: base ellittica larga
    p1 = (
        cq.Workplane("XY").workplane(offset=0)
        .ellipse(18, 12)
    )
    profili.append(p1.vals()[0])
    
    # Profilo 2: strozzatura centrale
    p2 = (
        cq.Workplane("XY").workplane(offset=40)
        .ellipse(14, 9)
    )
    profili.append(p2.vals()[0])
    
    # Profilo 3: ingrossamento per grip
    p3 = (
        cq.Workplane("XY").workplane(offset=80)
        .ellipse(20, 11)
    )
    profili.append(p3.vals()[0])
    
    # Profilo 4: punta affusolata
    p4 = (
        cq.Workplane("XY").workplane(offset=120)
        .ellipse(10, 7)
    )
    profili.append(p4.vals()[0])
    
    # Loft tra i profili
    manico = cq.Workplane("XY").add(
        cq.Solid.makeLoft(profili, ruled=False)  # Smooth loft
    )
    
    return manico

# Alternativa: sweep lungo curva
def crea_manico_sweep() -> cq.Workplane:
    """Manico con sezione circolare swept lungo una curva spline."""
    
    # Asse curvo del manico (curva spline)
    asse = (
        cq.Workplane("XZ")
        .spline([(0, 0), (10, 30), (5, 60), (15, 90), (0, 120)])
    )
    
    # Profilo sezione
    sezione = (
        cq.Workplane("XY")
        .ellipse(15, 10)
    )
    
    # Sweep
    return cq.Workplane("XY").sweep(sezione, asse)

manico = crea_manico_ergonomico()
cq.exporters.export(manico, "manico_organico.step")

# Note per Pocket NC 5 assi:
# - RICHIEDE 5 assi (asse B e A per superfici curvilinee)
# - Strategia: 3+2 o continuo 5 assi (swarf milling per pareti)
# - Post-processor essenziale: Pocket NC specifico (vedi sezione 6)
```

---

## 6. Generazione G-code per Pocket NC

### Percorso consigliato: CadQuery → FreeCAD Path → G-code

```python
"""
Pipeline: CadQuery STEP → FreeCAD Path → G-code Pocket NC
"""

# Passo 1: Esporta da CadQuery in STEP
import cadquery as cq
pezzo = crea_piastra_sensore()
cq.exporters.export(pezzo, "/tmp/pezzo.step")

# Passo 2: Processo FreeCAD (eseguito via script Python)
import FreeCAD
import Part
import Path
import PathScripts.PathJob as PathJob
import PathScripts.PathProfile as PathProfile
import PathScripts.PathDrilling as PathDrilling

# Carica il modello STEP
doc = FreeCAD.newDocument("lavorazione")
shape = Part.read("/tmp/pezzo.step")
obj = doc.addObject("Part::Feature", "Pezzo")
obj.Shape = shape

# Crea Job
job = PathJob.Create("Job", [obj])
job.Stock = PathJob.Stock.CreateFromBox(obj, extra=[2, 2, 2])  # 2mm clearance

# Operazione 1: Face Mill (sgrossatura superiore)
face_op = PathProfile.Create("FaceMill", job)
face_op.ToolController = job.ToolController[0]  # End mill 8mm
face_op.StepDown = 1.0   # Passo in profondità
face_op.Offset = 0.2     # Sovrametallo per finitura

# Post-processing → G-code
import PathScripts.PostUtils as PostUtils
gcode = PostUtils.GCodeSection(job, "pocket_nc")

with open("/tmp/pezzo_pocket_nc.nc", "w") as f:
    f.write(gcode)
print("G-code generato: pezzo_pocket_nc.nc")
```

### Post-processor Pocket NC
```
# Scarica il post-processor ufficiale Pocket NC per FreeCAD:
# https://github.com/Pocket-NC/LinuxCNC-Pocket-NC/tree/master/V2/post-processors

# Oppure usa il post-processor linuxcnc generico e modifica:
# - Velocità mandrino: max 10.000 RPM (V2-50CHK)
# - Asse A e B: range A(-30°, +135°), B(-9999°, +9999°) illimitato
# - Formato coordinate: G17 (piano XY), G54 (sistema di riferimento pezzo)
```

---

## 7. Integrazione con AI (LLM → CadQuery)

### Prompt Template per Generazione Automatica

```python
SYSTEM_PROMPT = """Sei un esperto di CadQuery e fresatura 5 assi. 
Quando l'utente descrive un pezzo, generi codice Python CadQuery valido.
Regole:
- Usa solo API CadQuery standard (niente librerie esterne)
- Includi sempre: import cadquery as cq
- Termina con: cq.exporters.export(result, "output.step")
- Aggiungi commenti per le operazioni di lavorazione chiave
- Specifica materiale consigliato e utensili
"""

USER_PROMPT = "Crea un anello con diametro 20mm, foro 15mm, altezza 6mm, con incisione 'CT' sulla superficie superiore"

# Con SDQ-1 router:
from sdq1.llm.router import LLMRouter
risposta = router.chiama(SYSTEM_PROMPT, USER_PROMPT, profilo="ragionamento")
codice_cadquery = risposta.risposta.testo
```

### Validazione Automatica del Codice Generato

```python
import subprocess
import tempfile
import os

def valida_cadquery(codice: str) -> dict:
    """Esegue il codice CadQuery e verifica che produca un file STEP valido."""
    
    with tempfile.TemporaryDirectory() as tmp:
        script_path = os.path.join(tmp, "pezzo.py")
        output_path = os.path.join(tmp, "output.step")
        
        # Aggiungi export se mancante
        if "exporters.export" not in codice:
            codice += f'\ncq.exporters.export(result, "{output_path}")\n'
        
        with open(script_path, "w") as f:
            f.write(codice)
        
        # Esegui in subprocess isolato
        result = subprocess.run(
            ["python", script_path],
            capture_output=True, text=True,
            timeout=30,
            cwd=tmp
        )
        
        if result.returncode != 0:
            return {"valido": False, "errore": result.stderr[:500]}
        
        if not os.path.exists(output_path):
            return {"valido": False, "errore": "Nessun file STEP generato"}
        
        file_size = os.path.getsize(output_path)
        return {
            "valido": True,
            "file_size_bytes": file_size,
            "output": result.stdout[:200]
        }
```

---

## 8. Specifiche Pocket NC V2-50CHK

| Parametro | Valore |
|-----------|--------|
| Corsa X | 4" (101.6mm) |
| Corsa Y | 4" (101.6mm) |
| Corsa Z | 4.5" (114.3mm) |
| Asse A | -30° / +135° |
| Asse B | ±9999° (illimitato) |
| Mandrino | 50 → 10.000 RPM |
| Cono mandrino | R8 |
| Precisione | ±0.0005" (±0.013mm) |
| Materiali | Alluminio, ottone, cera, plastica (HDPE, Delrin, PEEK) |
| Acciaio | Possibile con utensili adeguati (velocità bassa) |

### Velocità di taglio consigliate
```
Alluminio 6061:  300-600 m/min (end mill 4mm a 5.000 RPM → Vc=63 m/min)
Ottone CZ121:    150-300 m/min
Cera:            500-1000 m/min (fusa per casting gioielli)
Delrin/HDPE:     200-400 m/min
```

### Fissaggio pezzi piccoli (gioielli, <50mm)
- **Fixture morbida**: blocco di alluminio con tasca fresata a misura del pezzo
- **Cera di fissaggio**: pezzo incollato con cera, poi rimosso con acetone
- **Chuck 3 griffe**: per pezzi rotondi (anelli, cilindri)
- **Vite di fissaggio**: per piastre con fori

---

*Documentazione: https://cadquery.readthedocs.io/ — Pocket NC: https://pocketnc.com/pages/documentation*
