from seguimientos.models import (
    AñoAcademico,
    Ciclo,
    Modulo,
    UnidadDeTrabajo,
    Profesor,
    Grupo,
    Docencia,
    Seguimiento,
    EstadoSeguimiento,
    EvaluacionSeguimiento,
    MotivoNoCumpleSeguimiento,
)
import pyodbc
import django.db.utils
import secrets
import re

"""
IMPORTANTE
Este script permite migraciones desde la base de datos concreta del IESJC,
si quieres migrar tu propia base de datos puedes cogerlo como base.
"""


def run():
    # Modificar esta parte con credenciales para la base de datos SQLSERVER que se quiere migrar
    SERVER = "localhost"
    DATABASE = "IESJC"
    USERNAME = "sa"
    PASSWORD = "yourStrong(!)Password"
    connectionString = f"DRIVER={{/opt/microsoft/msodbcsql/lib64/libmsodbcsql-18.5.so.1.1}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};TrustServerCertificate=yes"
    conn = pyodbc.connect(connectionString)

    year = AñoAcademico.objects.get_or_create(año_academico="2024-25", actual=True)[0]
    print("Año ", year)

    originalYearID = 1069

    pasarCiclos(conn, year)
    pasarAsignaturas(conn, year, originalYearID)
    pasarProfesores(conn, originalYearID)
    pasarSeguimientos(conn, originalYearID)  # Esto incluye grupos


def pasarCiclos(conn, year):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ABREVS WHERE CODIGO = 'IDCICLO'")

    for row in cursor:
        print(f"{row.TEXTO}")
        if row.TEXTO == "DAM-DAW":
            Ciclo.objects.get_or_create(año_academico=year, nombre="DAW")
            Ciclo.objects.get_or_create(año_academico=year, nombre="DAM")
        else:
            Ciclo.objects.get_or_create(año_academico=year, nombre=row.TEXTO)


def pasarAsignaturas(conn, year, ogYearID):
    # First, handle DAM and DAW cycles (originally stored as DAM-DAW)
    dam_ciclo, _ = Ciclo.objects.get_or_create(nombre="DAM", año_academico=year)
    daw_ciclo, _ = Ciclo.objects.get_or_create(nombre="DAW", año_academico=year)

    # Process DAM-DAW cycle
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM ASIGNATURA A JOIN ABREVS B ON A.IDCICLO = B.IDABREVS WHERE TEXTO = 'DAM-DAW'"
    )
    dam_daw_data = cursor.fetchall()

    for row in dam_daw_data:
        # Check if this subject belongs to DAM, DAW, or both
        cursor_grupo = conn.cursor()
        cursor_grupo.execute(
            f"SELECT DISTINCT g.NombreGrupo FROM SEGUIMIENTO s JOIN GRUPOS g ON g.IdGrupo = s.IDGRUPO WHERE s.idASIGNATURA = {row.idASIGNATURA} AND s.IDCURSOACADEMICO = {ogYearID}"
        )
        grupos = cursor_grupo.fetchall()

        is_dam = any(
            "DAM" in grupo.NombreGrupo for grupo in grupos if grupo.NombreGrupo
        )
        is_daw = any(
            "DAW" in grupo.NombreGrupo for grupo in grupos if grupo.NombreGrupo
        )

        # Create modulo for DAM if it belongs to DAM
        if is_dam:
            print(f"DAM - {row.NOMBRE} - {traducirCurso(row.IDCURSO)}")
            modulo_dam = Modulo.objects.get_or_create(
                ciclo=dam_ciclo, nombre=row.NOMBRE, curso=traducirCurso(row.IDCURSO)
            )[0]

            # Process temario for DAM
            cursor2 = conn.cursor()
            cursor2.execute(
                f"SELECT * FROM TEMARIO WHERE idASIGNATURA = {row.idASIGNATURA}"
            )
            data2 = cursor2.fetchall()

            # Group by UT and keep only the one with highest idTEMARIO
            ut_groups = {}
            for row2 in data2:
                ut = row2.UT
                if ut not in ut_groups or row2.idTEMARIO > ut_groups[ut].idTEMARIO:
                    ut_groups[ut] = row2

            # Process the filtered records
            for row2 in ut_groups.values():
                title = row2.NOMBRE.strip()
                pattern = r"^\d+\s*[-\.]\s*"
                title = re.sub(pattern, "", title)
                UnidadDeTrabajo.objects.get_or_create(
                    modulo=modulo_dam, numero_tema=row2.UT, titulo=title
                )

        # Create modulo for DAW if it belongs to DAW
        if is_daw:
            print(f"DAW - {row.NOMBRE} - {traducirCurso(row.IDCURSO)}")
            modulo_daw = Modulo.objects.get_or_create(
                ciclo=daw_ciclo, nombre=row.NOMBRE, curso=traducirCurso(row.IDCURSO)
            )[0]

            # Process temario for DAW
            cursor2 = conn.cursor()
            cursor2.execute(
                f"SELECT * FROM TEMARIO WHERE idASIGNATURA = {row.idASIGNATURA}"
            )
            data2 = cursor2.fetchall()

            # Group by UT and keep only the one with highest idTEMARIO
            ut_groups = {}
            for row2 in data2:
                ut = row2.UT
                if ut not in ut_groups or row2.idTEMARIO > ut_groups[ut].idTEMARIO:
                    ut_groups[ut] = row2

            # Process the filtered records
            for row2 in ut_groups.values():
                title = row2.NOMBRE.strip()
                pattern = r"^\d+\s*[-\.]\s*"
                title = re.sub(pattern, "", title)
                UnidadDeTrabajo.objects.get_or_create(
                    modulo=modulo_daw, numero_tema=row2.UT, titulo=title
                )

    # Now process other cycles (excluding DAW and DAM as they were handled above)
    ciclos = Ciclo.objects.exclude(nombre="DAW").exclude(nombre="DAM")
    for ciclo in ciclos:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT * FROM ASIGNATURA A JOIN ABREVS B ON A.IDCICLO = B.IDABREVS WHERE TEXTO = '{ciclo.nombre}'"
        )
        data = cursor.fetchall()
        for row in data:
            print(f"{ciclo.nombre} - {row.NOMBRE} - {traducirCurso(row.IDCURSO)}")
            modulo = Modulo.objects.get_or_create(
                ciclo=ciclo, nombre=row.NOMBRE, curso=traducirCurso(row.IDCURSO)
            )[0]
            cursor2 = conn.cursor()
            cursor2.execute(
                f"SELECT * FROM TEMARIO WHERE idASIGNATURA = {row.idASIGNATURA}"
            )
            data2 = cursor2.fetchall()

            # Group by UT and keep only the one with highest idTEMARIO PORQUE HAY TEMAS REPETIDOS >:(
            ut_groups = {}
            for row2 in data2:
                ut = row2.UT
                if ut not in ut_groups or row2.idTEMARIO > ut_groups[ut].idTEMARIO:
                    ut_groups[ut] = row2

            # Process the filtered records
            for row2 in ut_groups.values():
                # Strip whitespace from the line
                title = row2.NOMBRE.strip()

                # Pattern to match number followed by optional whitespace, then either "- " or ". "
                pattern = r"^\d+\s*[-\.]\s*"

                # Remove the number prefix and return the cleaned text
                title = re.sub(pattern, "", title)
                UnidadDeTrabajo.objects.get_or_create(
                    modulo=modulo, numero_tema=row2.UT, titulo=title
                )


def pasarProfesores(conn, originalYearID):
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT * FROM PROFESOR p WHERE EXISTS (SELECT * FROM SEGUIMIENTO s WHERE s.IDPROFESOR = p.idPROFESOR AND s.IDCURSOACADEMICO = {originalYearID} )"
    )
    data = cursor.fetchall()
    for row in data:
        print(row.Nombre)
        try:
            Profesor.objects.get_or_create(
                activo=True,
                email=row.Email,
                nombre=row.Nombre,
                password=secrets.token_urlsafe(10),
            )
        except django.db.utils.IntegrityError:
            pass


def traducirCurso(a):
    return max(a - 1, 1)  # porque 1º es id 1 pero 2º es 3, 3º es 4, 4º es 5


def pasarSeguimientos(conn, originalYearID):
    """
    Migrates seguimientos from old database to new Django models
    """
    # Get the current academic year
    year = AñoAcademico.objects.get(actual=True)

    # First, we need to map old IDs to new objects
    estado_mapping = {
        36: EstadoSeguimiento.ADELANTADO,
        37: EstadoSeguimiento.ATRASADO,
        38: EstadoSeguimiento.AL_DIA,
    }

    evaluacion_mapping = {
        33: EvaluacionSeguimiento.PRIMERA,
        34: EvaluacionSeguimiento.SEGUNDA,
        35: EvaluacionSeguimiento.TERCERA,
    }

    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT 
            s.idSEGUIMIENTO,
            s.IDCURSOACADEMICO,
            s.IDPROFESOR,
            s.MES,
            s.IDGRUPO,
            s.IDEVALUACION,
            s.IDASIGNATURA,
            s.IDTEMARIO_IMPARTIDO,
            s.IDTEMARIO_IMPARTIENDOSE,
            s.ULTIMO_CONTENIDO_IMPARTIDO,
            s.CUMPLE_PROGRAMACION,
            s.ESTADO_PROGRAMACION,
            s.MOTIVO_NO_CUMPLE,
            s.OBSERVACIONES,
            g.NombreGrupo,
            p.Email as ProfesorEmail,
            a.NOMBRE as AsignaturaNombre,
            a.IDCURSO as AsignaturaCurso,
            abr.TEXTO as CicloNombre
        FROM SEGUIMIENTO s
        JOIN GRUPOS g ON s.IDGRUPO = g.IdGrupo
        JOIN PROFESOR p ON s.IDPROFESOR = p.idPROFESOR
        JOIN ASIGNATURA a ON s.IDASIGNATURA = a.idASIGNATURA
        JOIN ABREVS abr ON a.IDCICLO = abr.IDABREVS
        WHERE s.IDCURSOACADEMICO = {originalYearID}
        ORDER BY s.idSEGUIMIENTO
    """)

    seguimientos_data = cursor.fetchall()

    for row in seguimientos_data:
        print(f"Processing seguimiento {row.idSEGUIMIENTO}...")
        print(row)
        # Convert month (12-21 to 1-12)
        mes_convertido = convertir_mes(row.MES)

        # Find the profesor
        try:
            profesor = Profesor.objects.get(email=row.ProfesorEmail)
        except Profesor.DoesNotExist:
            print(f"Profesor with email {row.ProfesorEmail} not found, skipping...")
            continue

        # Find or create the grupo
        grupo_nombre = row.NombreGrupo
        ciclo_nombre = determinar_ciclo_desde_grupo(row.CicloNombre, grupo_nombre)

        try:
            ciclo = Ciclo.objects.get(nombre=ciclo_nombre, año_academico=year)
        except Ciclo.DoesNotExist:
            print(f"Ciclo {ciclo_nombre} not found, skipping...")
            continue

        # Determine curso from grupo name or use AsignaturaCurso
        curso = extraer_curso_de_grupo(grupo_nombre) or traducirCurso(
            row.AsignaturaCurso
        )

        grupo, created = Grupo.objects.get_or_create(
            nombre=grupo_nombre, ciclo=ciclo, curso=curso
        )

        # Find the modulo
        try:
            modulo = Modulo.objects.get(
                nombre=row.AsignaturaNombre,
                ciclo=ciclo,
                curso=traducirCurso(row.AsignaturaCurso),
            )
        except Modulo.DoesNotExist:
            print(
                f"Modulo {row.AsignaturaNombre} not found for ciclo {ciclo_nombre}, skipping..."
            )
            continue

        # Find or create docencia
        docencia, created = Docencia.objects.get_or_create(
            profesor=profesor, grupo=grupo, modulo=modulo
        )

        # Get the current UnidadDeTrabajo (temario_impartiendose)
        try:
            temario_actual = get_unidad_trabajo_by_old_id(
                conn, row.IDTEMARIO_IMPARTIENDOSE, modulo
            )
        except UnidadDeTrabajo.DoesNotExist:
            print(
                f"UnidadDeTrabajo with old ID {row.IDTEMARIO_IMPARTIENDOSE} not found, skipping..."
            )
            continue

        # Map estado
        estado = estado_mapping.get(row.ESTADO_PROGRAMACION, EstadoSeguimiento.AL_DIA)

        # Map evaluacion
        evaluacion = evaluacion_mapping.get(
            row.IDEVALUACION, EvaluacionSeguimiento.PRIMERA
        )

        # Determine justifications
        justificacion_estado = ""
        if estado != EstadoSeguimiento.AL_DIA:
            justificacion_estado = row.OBSERVACIONES or "No encontrado"

        justificacion_cumple = ""
        motivo_no_cumple = ""
        if row.CUMPLE_PROGRAMACION != 1:
            justificacion_cumple = row.MOTIVO_NO_CUMPLE or ""
            motivo_no_cumple = MotivoNoCumpleSeguimiento.SECUENCIA

        # Create or update seguimiento
        seguimiento, created = Seguimiento.objects.get_or_create(
            docencia=docencia,
            mes=mes_convertido,
            temario_actual=temario_actual,
            ultimo_contenido_impartido=row.ULTIMO_CONTENIDO_IMPARTIDO
            or "No encontrado",
            estado=estado,
            justificacion_estado=justificacion_estado,
            justificacion_cumple_programacion=justificacion_cumple,
            motivo_no_cumple_programacion=motivo_no_cumple,
            cumple_programacion=row.CUMPLE_PROGRAMACION == 1,
            evaluacion=evaluacion,
        )

        if created:
            # Set completed temario (all previous to current)
            if row.IDTEMARIO_IMPARTIDO:
                temarios_completados = get_temarios_completados(
                    conn, row.IDTEMARIO_IMPARTIDO, modulo
                )
                if temarios_completados:
                    seguimiento.temario_completado.set(temarios_completados)

            print(
                f"Created seguimiento for {profesor.nombre} - {modulo.nombre} - Mes {mes_convertido}"
            )
        else:
            print(
                f"Seguimiento already exists for {profesor.nombre} - {modulo.nombre} - Mes {mes_convertido}"
            )


def convertir_mes(mes_old):
    """Convert old month system (12-21) to new system (1-12)"""
    if mes_old >= 18:
        return mes_old - 9  # September to December
    else:
        return mes_old - 11  # January to June


def determinar_ciclo_desde_grupo(ciclo_original, grupo_nombre):
    """Determine the correct ciclo name from the original ciclo and grupo name"""
    if ciclo_original == "DAM-DAW":
        if "DAM" in grupo_nombre:
            return "DAM"
        elif "DAW" in grupo_nombre:
            return "DAW"
    else:
        return ciclo_original


def extraer_curso_de_grupo(grupo_nombre):
    """Extract curso number from grupo name (e.g., '1DAM' -> 1, '2DAW' -> 2)"""
    if not grupo_nombre:
        return None

    # Look for number at the beginning
    import re

    match = re.match(r"^(\d+)", grupo_nombre)
    if match:
        return int(match.group(1))

    return None


def get_unidad_trabajo_by_old_id(conn, old_temario_id, modulo):
    """Get UnidadDeTrabajo by old TEMARIO ID"""
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT UT FROM TEMARIO WHERE idTEMARIO = {old_temario_id}")
    except Exception:
        return UnidadDeTrabajo.objects.get(modulo=modulo, numero_tema=1)
    row = cursor.fetchone()

    if not row:
        raise UnidadDeTrabajo.DoesNotExist(f"Old temario ID {old_temario_id} not found")

    try:
        return UnidadDeTrabajo.objects.get(modulo=modulo, numero_tema=row.UT)
    except UnidadDeTrabajo.DoesNotExist:
        raise UnidadDeTrabajo.DoesNotExist(
            f"UnidadDeTrabajo with numero_tema {row.UT} not found for modulo {modulo}"
        )


def get_temarios_completados(conn, last_completed_id, modulo):
    """Get all UnidadDeTrabajo that should be marked as completed"""
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT UT FROM TEMARIO WHERE idTEMARIO = {last_completed_id}")
    except Exception:
        return None
    row = cursor.fetchone()

    if not row:
        return []

    last_completed_ut = row.UT

    # Get all UnidadDeTrabajo with numero_tema <= last_completed_ut
    return UnidadDeTrabajo.objects.filter(
        modulo=modulo, numero_tema__lte=last_completed_ut
    )
