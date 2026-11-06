"""
Guías iniciales del centro de ayuda (ADR-018).

Escritas a partir de las pantallas reales (etiquetas y botones tal como
aparecen en la interfaz). El Administrador puede editarlas y adjuntar videos
desde el propio centro de ayuda; `sembrar` no sobrescribe lo ya editado.
"""

ADMIN, COORD, VICE, DOC, EST = 'Administrador', 'Coordinador', 'Vicerrector', 'Docente', 'Estudiante'
GESTORES = [ADMIN, COORD]


def _p(titulo, detalle=''):
    return {'titulo': titulo, 'detalle': detalle}


GUIAS = [
    {
        'slug': 'usar-centro-de-ayuda', 'categoria': 'primeros_pasos', 'orden': 1, 'roles': [],
        'titulo': 'Cómo usar el centro de ayuda', 'ruta': '/ayuda',
        'resumen': 'Busca una tarea, filtra por categoría y abre la guía paso a paso o su video.',
        'pasos': [
            _p('Busca lo que necesitas', 'Escribe palabras como "momento", "docente" o "exportar". La búsqueda no distingue tildes ni mayúsculas.'),
            _p('Filtra por categoría', 'Las categorías agrupan las guías por proceso: estructura curricular, evaluaciones, analítica, etc.'),
            _p('Abre la guía', 'Cada guía tiene los pasos en orden, notas y, cuando existe, un video. "Ir a la pantalla" te lleva al lugar donde se hace.'),
        ],
        'notas': 'Solo ves las guías de tu rol. Si un video aún no está disponible, la guía lo indica.',
    },
    {
        'slug': 'crear-programa', 'categoria': 'estructura', 'orden': 10, 'roles': [ADMIN, COORD],
        'titulo': 'Crear o editar un programa académico', 'ruta': '/academico?tab=programas',
        'resumen': 'Registra un programa con su código, modalidad, sede y duración en semestres.',
        'pasos': [
            _p('Abre Académico → Programas', 'Verás la tabla "Programas académicos" con código, programa, modalidad, sede, duración, origen y estado.'),
            _p('Pulsa "Nuevo programa"', 'Solo el Administrador ve este botón. El Coordinador consulta los programas, pero no los crea.'),
            _p('Completa los datos', 'Código, nombre, modalidad (Presencial, Virtual, Distancia o Híbrida), sede, duración (semestres) y, si aplica, fecha de vigencia.'),
            _p('Guarda', 'Para cambiar un programa, usa el lápiz de su fila. El estado y el origen (manual, documento o importación) se muestran en la tabla.'),
        ],
        'notas': 'Los programas también pueden llegar por la importación institucional (pestaña Importar).',
    },
    {
        'slug': 'malla-semestres-asignaturas', 'categoria': 'estructura', 'orden': 20, 'roles': GESTORES,
        'titulo': 'Organizar la malla: semestres y asignaturas', 'ruta': '/academico?tab=malla',
        'resumen': 'Crea los semestres del programa y ubica en ellos sus asignaturas.',
        'pasos': [
            _p('Elige el programa activo', 'Arriba, en "Programa activo", selecciona el programa. Todas las pestañas trabajan sobre él.'),
            _p('Abre la pestaña Malla', 'A la izquierda están los semestres y a la derecha las asignaturas del catálogo del programa.'),
            _p('Crea los semestres', 'En "Semestres del programa", pulsa "Nuevo". El número es único dentro del programa; el nombre es opcional.'),
            _p('Crea las asignaturas', 'En "Asignaturas", pulsa "Nueva": código, nombre, créditos, horas por semana, tipo (Obligatoria, Electiva, Optativa o Práctica / Laboratorio) y semestre.'),
            _p('Edita o elimina', 'El lápiz edita. La papelera desactiva la asignatura (borrado lógico): deja de usarse, pero su historial se conserva.'),
        ],
        'notas': 'Una asignatura sin semestre aparece como "Sin ubicar" y en la analítica se agrupa como "Sin semestre en la malla".',
    },
    {
        'slug': 'asignar-docente-individual', 'categoria': 'docentes', 'orden': 30, 'roles': GESTORES,
        'titulo': 'Asignar el docente de una asignatura', 'ruta': '/academico?tab=malla',
        'resumen': 'Vincula la asignatura al curso del docente que la dicta.',
        'pasos': [
            _p('Abre Académico → Malla', 'Con el programa activo elegido, busca la asignatura en la lista de la derecha. Debajo del nombre dice el docente actual o "Sin docente asignado".'),
            _p('Edita la asignatura', 'Pulsa el lápiz ("Editar asignatura").'),
            _p('Elige el docente', 'En "Docente (curso en Lairn)" selecciona el curso con el nombre del docente. "Sin docente asignado" quita el vínculo.'),
            _p('Guarda', 'Desde ese momento el docente ve la asignatura en su banco de preguntas y en tareas, y sus estudiantes inscritos quedan convocados a las evaluaciones.'),
        ],
        'notas': 'La lista muestra los cursos que ya tienen los docentes. Si el docente aún no tiene uno, usa la asignación masiva: allí se crea el curso automáticamente (con aviso previo).',
    },
    {
        'slug': 'asignar-docentes-masivo', 'categoria': 'docentes', 'orden': 31, 'roles': GESTORES,
        'titulo': 'Asignar docentes a varias asignaturas con un archivo', 'ruta': '/academico?tab=malla',
        'resumen': 'Descarga la plantilla, escribe el correo de cada docente, revisa la vista previa y confirma.',
        'pasos': [
            _p('Abre Académico → Malla → "Asignar docentes"', 'El botón está en la tarjeta "Asignaturas" del programa activo.'),
            _p('Descarga la plantilla', '"Plantilla Excel" o "Plantilla CSV" traen las asignaturas activas del programa con su docente actual. El Excel incluye la hoja Docentes con los correos válidos.'),
            _p('Llena docente_email', 'Escribe el correo del docente en cada asignatura. Déjalo vacío para no cambiarla. curso_codigo es opcional: sirve para elegir uno de varios cursos del docente.'),
            _p('Sube el archivo y pulsa "Analizar archivo"', 'Se aceptan .xlsx, .csv y .json (máximo 2 MB y 2000 filas). Todavía no se guarda nada.'),
            _p('Revisa la vista previa', 'Cada fila queda Válida, Con advertencia (se creará un curso o cambia el docente), Ya asignada, Sin docente o Con error, con el motivo. Puedes filtrar por estado y descargar la vista previa.'),
            _p('Confirma', '"Confirmar N asignación(es)" aplica las filas válidas y con advertencia, todo o nada. Al final puedes descargar el resumen.'),
        ],
        'notas': 'Si el archivo cambió desde la vista previa, el sistema pide analizarlo de nuevo. Repetir el mismo archivo no duplica cursos ni asignaciones.',
    },
    {
        'slug': 'competencias-y-resultados', 'categoria': 'estructura', 'orden': 40, 'roles': GESTORES,
        'titulo': 'Registrar competencias y resultados de aprendizaje', 'ruta': '/academico?tab=competencias',
        'resumen': 'Define las competencias del programa y los RA de cada asignatura.',
        'pasos': [
            _p('Abre Académico → Competencias', 'A la izquierda están las competencias y a la derecha los "Resultados de aprendizaje (DCE)".'),
            _p('Crea la competencia', 'Pulsa "Nueva": nombre, tipo (Específica o Transversal) y descripción.'),
            _p('Crea el resultado de aprendizaje', 'Pulsa "Nuevo RA": asignatura, competencia, descripción, evidencia observable, afirmación (qué se infiere) y tarea sugerida.'),
            _p('Revisa', 'Cada RA muestra su evidencia y su tarea. Desde aquí se editan o desactivan.'),
        ],
        'notas': 'Los RA son la base de las preguntas del banco, de las evaluaciones y de la analítica.',
    },
    {
        'slug': 'momentos-de-evaluacion', 'categoria': 'evaluaciones', 'orden': 50, 'roles': GESTORES,
        'titulo': 'Crear un momento de evaluación y vincular sus RA', 'ruta': '/academico?tab=momentos',
        'resumen': 'Un momento agrupa las evaluaciones de un corte y dice qué RA deben evaluarse.',
        'pasos': [
            _p('Abre Académico → Momentos', 'La tabla "Momentos de evaluación" lista los momentos del programa con su semestre y periodo.'),
            _p('Pulsa "Nuevo momento"', 'Nombre, semestre de referencia y periodo (opcional, pero necesario para comparar por periodo en la analítica).'),
            _p('Vincula los resultados', 'En la fila del momento, el icono "Vincular resultados" abre la lista de RA. Agrega cada RA y marca "Obligatorio" si debe evaluarse sí o sí.'),
            _p('Revisa la cobertura', 'El tablero del momento muestra cuántos RA obligatorios ya tienen evaluación publicada.'),
        ],
        'notas': 'Un RA obligatorio sin evaluación publicada aparece como hallazgo en el informe de resultados de aprendizaje.',
    },
    {
        'slug': 'evaluacion-formal', 'categoria': 'evaluaciones', 'orden': 51, 'roles': GESTORES,
        'titulo': 'Programar y publicar una evaluación formal', 'ruta': '/academico?tab=momentos',
        'resumen': 'Crea la evaluación del momento, define su horario, elige preguntas o tarea y publícala.',
        'pasos': [
            _p('Abre el momento', 'En Académico → Momentos, pulsa el icono "Evaluación formal (fechas y preguntas)" del momento.'),
            _p('Pulsa "Nueva evaluación"', 'En "1. Datos de la evaluación" escribe el nombre y las instrucciones para el estudiante y elige si es cuestionario o tarea.'),
            _p('Define el horario', 'Fecha (con atajos), hora sugerida o reloj a. m./p. m., duración, tolerancia de ingreso y cierre automático. El resumen muestra cuándo abre y cierra.'),
            _p('Elige el contenido', 'Cuestionario: "2. Preguntas por resultado de aprendizaje" (solo preguntas aprobadas del banco). Tarea: "2. Tarea que se evalúa".'),
            _p('Supervisión y convocatoria (opcional)', 'Puedes asignar un supervisor que llama a lista en sala. Los convocados por defecto son los inscritos en los cursos vinculados; el cargue de estudiantes es opcional.'),
            _p('Publica', '"Publicar" pide confirmación. Desde ese momento los convocados la ven en "Evaluaciones".'),
        ],
        'notas': 'Para publicar, la evaluación necesita preguntas (o una tarea) y un cierre en el futuro.',
    },
    {
        'slug': 'convocatoria-y-cargue', 'categoria': 'estudiantes', 'orden': 60, 'roles': GESTORES,
        'titulo': 'Convocar estudiantes y cargar un listado', 'ruta': '/academico?tab=momentos',
        'resumen': 'Quiénes presentan la evaluación y cómo agregar estudiantes con un archivo.',
        'pasos': [
            _p('Convocatoria por defecto', 'Quedan convocados los estudiantes inscritos en los cursos vinculados a las asignaturas de la evaluación. No hay que hacer nada más.'),
            _p('Agregar estudiantes (opcional)', 'En la evaluación, tarjeta "Convocados" → "Agregar estudiantes (CSV o Excel)". El archivo necesita al menos la columna de correo.'),
            _p('Revisa la vista previa', 'El sistema compara nombre, programa, semestre y código del archivo con la cuenta del estudiante y marca las diferencias. Nunca sobrescribe la cuenta.'),
            _p('Confirma o pulsa "Cerrar sin cargar"', 'Solo se agregan los estudiantes válidos.'),
        ],
        'notas': 'El listado general está en el menú Estudiantes, con búsqueda, estados y exportación a CSV/Excel.',
    },
    {
        'slug': 'listado-de-estudiantes', 'categoria': 'estudiantes', 'orden': 61, 'roles': [ADMIN, COORD, DOC],
        'titulo': 'Consultar el listado de estudiantes', 'ruta': '/estudiantes',
        'resumen': 'Busca estudiantes convocados e inscritos, revisa su estado y exporta el listado.',
        'pasos': [
            _p('Abre el menú Estudiantes', 'El docente solo ve los estudiantes de sus cursos y evaluaciones.'),
            _p('Busca y filtra', 'Por nombre, correo o código, y por estado.'),
            _p('Exporta', 'Descarga el listado filtrado en CSV o Excel.'),
        ],
        'notas': 'Trata estos datos según la política de protección de datos personales de la institución (Ley 1581 de 2012).',
    },
    {
        'slug': 'supervision-en-sala', 'categoria': 'evaluaciones', 'orden': 70, 'roles': [ADMIN, COORD, DOC],
        'titulo': 'Supervisar una evaluación en sala', 'ruta': '/supervision',
        'resumen': 'Llama a lista, habilita el ingreso y atiende los incidentes de integridad.',
        'pasos': [
            _p('Abre Supervisión', 'Verás las evaluaciones en las que eres supervisor.'),
            _p('Llama a lista', 'Marca a cada convocado como presente, tarde o ausente. Solo quien está presente o tarde puede comenzar.'),
            _p('Sigue la evaluación', 'El seguimiento muestra en vivo quién no ha iniciado, quién está presentando y quién ya envió.'),
            _p('Resuelve los incidentes', 'Si un estudiante sale de pantalla completa o cambia de pestaña, primero recibe una advertencia y luego queda suspendido. Tú decides si reactivarlo o anular el intento por fraude.'),
        ],
        'notas': 'Los intentos anulados no cuentan en la analítica; el informe muestra cuántos hubo.',
    },
    {
        'slug': 'banco-de-preguntas', 'categoria': 'banco_tareas', 'orden': 80, 'roles': [DOC],
        'titulo': 'Generar y aprobar preguntas del banco', 'ruta': '/banco-preguntas',
        'resumen': 'Genera preguntas con IA para un RA, revísalas y aprueba las que irán a las evaluaciones.',
        'pasos': [
            _p('Abre Banco de preguntas', 'Solo aparecen las asignaturas que la coordinación vinculó a un curso tuyo.'),
            _p('Elige asignatura y RA', 'Opcionalmente, también una competencia transversal.'),
            _p('Pulsa "Generar preguntas con IA"', 'Las preguntas llegan "Pendientes de validación". Los estudiantes no las ven.'),
            _p('Revisa cada pregunta', '"Editar" para corregirla, "Aprobar" para pasarla al banco oficial o "Descartar".'),
            _p('Filtra el banco', 'Por estado y por competencia transversal.'),
        ],
        'notas': 'Solo las preguntas aprobadas pueden elegirse en una evaluación formal.',
    },
    {
        'slug': 'tareas-practicas', 'categoria': 'banco_tareas', 'orden': 81, 'roles': [DOC],
        'titulo': 'Crear, publicar y calificar una tarea', 'ruta': '/tareas',
        'resumen': 'Tareas prácticas con rúbrica, archivos guía y plazo, calificadas por rúbrica.',
        'pasos': [
            _p('Abre Tareas', 'Crea una tarea a mano o genérala con IA desde un resultado de aprendizaje. La rúbrica parte de la del RA cuando existe.'),
            _p('Edita el borrador', 'Instrucciones, formatos permitidos, plazo, política de retraso, rúbrica y archivos guía.'),
            _p('Publica', 'Los estudiantes del curso la ven en "Tareas".'),
            _p('Califica', 'En la tarea publicada, el panel de entregas permite calificar cada entrega con la rúbrica.'),
        ],
        'notas': 'La coordinación puede usar una tarea como evaluación formal de tipo "tarea" dentro de un momento.',
    },
    {
        'slug': 'presentar-evaluacion', 'categoria': 'evaluaciones', 'orden': 90, 'roles': [EST],
        'titulo': 'Presentar una evaluación', 'ruta': '/mis-evaluaciones',
        'resumen': 'Cómo ingresar, responder y enviar una evaluación formal.',
        'pasos': [
            _p('Abre Evaluaciones', 'Verás las evaluaciones a las que estás convocado, con su horario.'),
            _p('Espera el llamado a lista si aplica', 'Si la evaluación tiene supervisor, el botón se habilita solo cuando te marque presente (la página se actualiza cada 10 s).'),
            _p('Pulsa "Comenzar evaluación"', 'La evaluación se abre en pantalla completa. No copies, pegues ni cambies de pestaña: la primera vez recibes una advertencia y la segunda el intento queda suspendido hasta que el supervisor decida.'),
            _p('Responde', 'El índice de preguntas muestra cuáles faltan. "Ir a la siguiente pendiente" te lleva a la próxima sin responder.'),
            _p('Pulsa "Enviar evaluación"', 'Al enviar ya no puedes cambiar respuestas. Si se acaba el tiempo, se envía automáticamente.'),
        ],
        'notas': 'La nota de la evaluación formal no se muestra al estudiante. La de las tareas calificadas sí.',
    },
    {
        'slug': 'entregar-tarea', 'categoria': 'banco_tareas', 'orden': 91, 'roles': [EST],
        'titulo': 'Entregar una tarea', 'ruta': '/mis-tareas',
        'resumen': 'Consulta las instrucciones, sube tu archivo y revisa la calificación.',
        'pasos': [
            _p('Abre Tareas', 'Verás las tareas publicadas de tus cursos con su plazo.'),
            _p('Lee las instrucciones', 'Descarga los archivos guía y revisa la rúbrica y los formatos permitidos.'),
            _p('Sube tu entrega', 'Antes del plazo. Si la entregas tarde, se aplica la política de retraso de la tarea.'),
            _p('Revisa la calificación', 'Cuando el docente califica, ves la nota y la rúbrica.'),
        ],
        'notas': '',
    },
    {
        'slug': 'informe-resultados-aprendizaje', 'categoria': 'analitica', 'orden': 100, 'roles': [ADMIN, COORD, VICE],
        'titulo': 'Leer el informe de resultados de aprendizaje', 'ruta': '/reporte-institucional',
        'resumen': 'Recorre el informe en 6 pasos, de la situación general a la evidencia.',
        'pasos': [
            _p('Abre el informe', 'Menú Analítica (Coordinador), Reporte (Administrador) o Reporte institucional (Vicerrector).'),
            _p('Aplica los filtros', 'Programa, semestre, momento, asignatura, docente, competencia y fechas. Se conservan en la dirección de la página.'),
            _p('Recorre los 6 pasos', 'Panorama → Hallazgos → Profundizar → Comparar → Conclusiones → Evidencia y metodología. Usa "Siguiente" o la barra de pasos.'),
            _p('Consulta la ficha técnica', 'El botón ⓘ de cada cifra explica fórmula, fuente, unidad y limitaciones.'),
            _p('Profundiza desde un hallazgo', '"Ver detalle" aplica el filtro del hallazgo y te lleva al paso donde se ve.'),
        ],
        'notas': 'Las conclusiones son descriptivas: no establecen causas. La métrica de logro es provisional hasta que Vicerrectoría la defina. Los indicadores son institucionales propios, no indicadores oficiales del MEN.',
    },
    {
        'slug': 'notas-del-momento', 'categoria': 'analitica', 'orden': 99, 'roles': [ADMIN, COORD, VICE],
        'titulo': 'Consultar y exportar las notas del momento', 'ruta': '/notas-momento',
        'resumen': 'Nota de cada estudiante en el momento: examen, trabajo, consolidado y aporte al tercer corte, con su Excel.',
        'pasos': [
            _p('Abre "Notas"', 'En el menú (Notas del momento para el Vicerrector) o desde Académico → Momentos con el icono "Notas del momento".'),
            _p('Elige el momento', 'Se listan los momentos que tienen evaluaciones publicadas.'),
            _p('Revisa cómo se calcula', 'Examen: 5 × correctas / total de preguntas de todos los cuestionarios del momento, con un decimal y redondeo reglamentario. El momento vale el 30 % del tercer corte y el tercer corte el 40 % de la nota definitiva.'),
            _p('Define la ponderación si hay trabajo (gestor)', 'Si el momento tiene una tarea, escribe el % del examen; el del trabajo se completa solo. Sin ponderación, el consolidado queda pendiente.'),
            _p('Consulta cada estudiante', 'Nota y desempeño del examen, correctas, incorrectas y sin responder, trabajo, consolidado, nota reglamentaria y aportes. Busca y filtra por estado.'),
            _p('Exporta el Excel', '"Exportar Excel" descarga un libro con resultados individuales, resumen estadístico, detalle del examen, metodología y convenciones. Cada exportación queda registrada.'),
        ],
        'notas': 'Una celda sin nota no es cero: el estado explica el motivo. La "nota reglamentaria" aplica 0,0 solo a lo no presentado sin excusa (Acuerdo 005 de 2025). Los aportes no son la nota del tercer corte.',
    },
    {
        'slug': 'exportar-informe', 'categoria': 'analitica', 'orden': 101, 'roles': [ADMIN, COORD, VICE],
        'titulo': 'Exportar el informe a PDF o Excel', 'ruta': '/reporte-institucional?etapa=evidencia',
        'resumen': 'Descarga el informe con los mismos filtros y cifras de la pantalla.',
        'pasos': [
            _p('Aplica los filtros', 'Lo exportado coincide con lo que estás viendo.'),
            _p('Pulsa "Exportar PDF" o "Exportar Excel"', 'Están arriba a la derecha y en el paso 6.'),
            _p('PDF', 'Sigue los 6 pasos, con gráficos, fichas técnicas, metodología, numeración de páginas y fuente de cada tabla.'),
            _p('Excel', 'Una hoja por tema, con encabezados fijos, filtros, porcentajes numéricos y gráficos.'),
        ],
        'notas': 'Los archivos contienen información agregada, sin datos personales de estudiantes.',
    },
    {
        'slug': 'alertas-tempranas', 'categoria': 'analitica', 'orden': 102, 'roles': GESTORES,
        'titulo': 'Revisar las alertas tempranas', 'ruta': '/academico?tab=alertas',
        'resumen': 'Estudiantes y cursos por debajo del desempeño mínimo, con su seguimiento.',
        'pasos': [
            _p('Abre Académico → Alertas', 'Las alertas se recalculan cada vez que abres el tablero.'),
            _p('Configura la regla (Administrador)', '"Desempeño mínimo (%)", "Actividades por debajo para alertar" y si la regla está activa. El Administrador también puede exportar el listado a CSV.'),
            _p('Registra el seguimiento', 'En cada alerta, "Registrar seguimiento" deja constancia de la acción tomada.'),
        ],
        'notas': '',
    },
    {
        'slug': 'importar-pensum', 'categoria': 'importacion', 'orden': 110, 'roles': [ADMIN],
        'titulo': 'Importar programas y asignaturas', 'ruta': '/academico?tab=integracion',
        'resumen': 'Carga el pensum desde un JSON institucional, con vista previa antes de guardar.',
        'pasos': [
            _p('Abre Académico → Importar', 'Pestaña exclusiva del Administrador.'),
            _p('Elige la fuente', '"Dirección del recurso JSON", "Archivo .json" o "Contenido JSON" pegado.'),
            _p('Valida', 'La vista previa dice qué se creará, actualizará, rechazará u omitirá, y por qué. Todavía no se guarda nada.'),
            _p('Importa', 'Se aplica lo validado en una transacción. Si la fuente cambió, pide validar de nuevo. Repetirla no duplica nada.'),
            _p('Docentes (opcional)', 'Cada asignatura puede traer docente_email y curso_codigo. Se validan igual que en la asignación masiva y aparecen como filas "Docente".'),
        ],
        'notas': 'Las cuentas de usuario no se crean ni modifican desde la importación.',
    },
    {
        'slug': 'documentos-institucionales', 'categoria': 'importacion', 'orden': 111, 'roles': [ADMIN],
        'titulo': 'Cargar documentos institucionales (pensum, plan de aula, resolución)', 'ruta': '/academico?tab=integracion',
        'resumen': 'Sube un PDF, revisa lo extraído y apruébalo para incorporarlo.',
        'pasos': [
            _p('Abre Académico → Importar → "Documentos institucionales"', 'Elige el tipo de documento: Pensum, Plan de aula o Resolución.'),
            _p('Sube el PDF', 'El sistema extrae la información y deja el cargue pendiente de revisión.'),
            _p('Revisa', 'Corrige lo extraído y elige el programa destino.'),
            _p('Aprueba', 'Al aprobar se incorpora a la malla, las competencias y los RA del programa.'),
        ],
        'notas': '',
    },
]


def sembrar(Articulo) -> int:
    """Crea las guías que no existen (por slug). No toca las ya editadas. Devuelve cuántas creó."""
    creadas = 0
    for g in GUIAS:
        _obj, nuevo = Articulo.objects.get_or_create(slug=g['slug'], defaults={k: v for k, v in g.items() if k != 'slug'})
        creadas += int(nuevo)
    return creadas
