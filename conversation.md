El sistema está completo y los 71 tests pasan. Tu fichero 01-loin-target/02-LOIN-Arquitetura.xlsx ya está convertido a
  out/02-IDS-Arquitetura.ids: 13 especificaciones, válido contra el XSD de IDS 1.0 y contra el esquema IFC4X3_ADD2. No he hecho
  ningún commit.

  Primero, un error mío: había un .gitignore sin versionar (copiado desde Windows) y lo sobrescribí sin leerlo. No puedo
  recuperar su contenido; si tienes la copia original, revísalo.

  Cómo se reparte el trabajo

  - Script determinista (loin2ids). Lee .xlsx y .ods, detecta la columna de fase y corrige erratas contra el esquema IFC
    (Lenght, With, Predifined Type, IfcPipeSgment). También saca los dataType del esquema oficial, convierte las tablas
    SECClasS en prefijos y escribe y valida el XML.
  - LLM (skill /loin-to-ids). Solo interviene en lo que requiere criterio, y lo deja escrito con su motivo en decisions.yaml;
    nunca toca el XML. Ejemplos: Espessura? sin Pset, hojas que se solapan sobre la misma entidad, el filtro de la hoja de
    materiales, Psets propios como WBS_bSPT.

  Lo que han revelado los golden

  Los 8 golden se convierten sin bloqueos. Las Geral coinciden exactamente; en el resto hay 43 diferencias, y todas son errores
  de los golden según la hoja y el esquema IFC. Están documentadas una a una en docs/desvios-golden.md. Las más graves:
  - En SRU-EST, las entidades de LançoEscadas y LançoRampas están cruzadas.
  - Se conservan erratas como Lenght y ValveMechanisme (esta última con un dataType inexistente).
  - Faltan requisitos que la hoja sí marca.

  Tests

  - Golden: cualquier diferencia nueva frente a los golden, o una documentada que deje de aparecer, hace fallar el test.
  - Validez: todo IDS generado pasa el XSD y el esquema IFC, y la conversión sale idéntica byte a byte en cada ejecución.
  - Robustez: hojas sintéticas con columnas desplazadas, espacios, mayúsculas, notas, y cada tipo de bloqueo junto con la
    decisión que lo resuelve.
  - Funcional: un IFC sintético que cumple pasa el IDS generado y uno incompleto falla.
  - Unitarios, CLI y fichero objetivo.

  Decisiones que te corresponden

  1. WBS_bSPT (en projects/arquitetura/decisions.yaml): lo he aceptado sin dataType, así que vale cualquier valor, igual que
     hacen los golden con su Pset propio. Si quieres exigir texto, añade data_type: IFCLABEL.
  2. min_occurs: 1, como en los golden: el modelo tiene que contener al menos un elemento de cada especificación, así que un
     proyecto sin rampas fallará. Con 0 solo se comprueban los elementos que existan.
  3. Cabecera del IDS: faltan author (tiene que ser un e-mail) y copyright en project.yaml.
  4. Errata en la hoja objetivo: ARQ-Guardas tiene Lenght. Se corrige automáticamente con un aviso; conviene corregirla también
     en la hoja.

  Archivos

  - loin2ids/: el conversor, con su configuración en loin2ids/config/.
  - .claude/skills/loin-to-ids/: la skill.
  - CLAUDE.md
  - tests/: incluye tests/golden/known_deviations.yaml y las decisiones de ejemplo de los golden.
  - projects/arquitetura/: project.yaml y decisions.yaml de tu fichero objetivo.
  - README.md y docs/, en portugués: guía de usuario, gramática de la hoja LOIN, desarrollo y tests, y desviaciones de los
    golden.
  - docs/PLAN.md: copia del plan aprobado.
  - HANDOFF.md: lo he reescrito con el estado actual para que puedas cambiar de ordenador.

  Para usarlo en adelante: deja la hoja en 01-loin-target/ y escribe /loin-to-ids en Claude Code.