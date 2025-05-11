- [Setup del entorno de desarollo](#setup-del-entorno-de-desarollo)
- [Setup del entorno de despliegue](#setup-del-entorno-de-despliegue)
- [Endpoints](#endpoints)
  - [Autenticación - `/auth/`](#autenticación---auth)
    - [Registro en la app - POST `/users/`](#registro-en-la-app---post-users)
    - [Login - POST `/token/login/`](#login---post-tokenlogin)
    - [Login - POST `/token/logout/`](#login---post-tokenlogout)
  - [API `/api/`](#api-api)
    - [Año Academico Actual `GET` `/year-actual/`](#año-academico-actual-get-year-actual)
    - [Docencias `/docencias/`](#docencias-docencias)
      - [Listado](#listado)
    - [Módulos `/modulos/`](#módulos-modulos)
      - [Listado](#listado-1)
      - [Detalle `/<pk>/`](#detalle-pk)
      - [Detalle Temario `/<pk>/temario/`](#detalle-temario-pktemario)
    - [Seguimientos faltantes `/seguimientos-faltantes/<slug:año_academico>/<int:mes>/`](#seguimientos-faltantes-seguimientos-faltantesslugaño_academicointmes)
    - [Seguimientos faltantes anual `/seguimientos-faltantes-anual/<slug:año_academico>/`](#seguimientos-faltantes-anual-seguimientos-faltantes-anualslugaño_academico)
    - [Seguimientos `/seguimientos/`](#seguimientos-seguimientos)
      - [Listado `POST, GET`](#listado-post-get)
      - [Detalle `PUT, PATCH, GET` `/<pk>/`](#detalle-put-patch-get-pk)
    - [Enviar recordatorios `POST` - `/enviar-recordatorios/`](#enviar-recordatorios-post---enviar-recordatorios)

Backend de la aplicación de seguimiento

# Setup del entorno de desarollo

1. Iniciar un contenedor de Postgres `docker run -e POSTGRES_PASSWORD=1234 -e POSTGRES_DB=seguimientos -d -p 5432:5432 postgres:latest`
2. Iniciar el shell pipenv `pipenv shell`
3. Instalar las dependencias `pipenv install`
4. Añadir los ficheros estaticos `python manage.py collectstatic`
5. Iniciar la aplicación `python manage.py runserver`

# Setup del entorno de despliegue

1. Variables de entorno

```py
SECRET_KEY="django-insecure-1seo&72qbf8$p6z2t&7m2%_mvnbslm$)g#wy4ix@bbruuwmug"
DEBUG=False #False en producción
FRONTEND_URL="http://localhost:5173" #URL de la applicación de frontend
DB_NAME="seguimientos" #Datos de la base de datos postgresql
DB_USER="postgres"
DB_PASSWORD="1234"
DB_HOST="localhost"
DB_PORT="5432"
```

# Endpoints

## Autenticación - `/auth/`

Más endpoints accesibles en la documentación de [Djoser](https://djoser.readthedocs.io/en/latest/base_endpoints.html)

### Registro en la app - POST `/users/`

```json
{
  "email": "email@dominio.com",
  "nombre": "Fulano de Tal",
  "password": "password"
}
```

### Login - POST `/token/login/`

```json
{
  "email": "email@dominio.com",
  "password": "password"
}
```

Si es correcto devuelve un `json` como

```json
{ "auth_token": "b704c9fc3655635646356ac2950269f352ea1139" }
```

Para usarlo, añadir el header: `Authorization: Token b704c9fc3655635646356ac2950269f352ea1139`

### Login - POST `/token/logout/`

Necesita autenticación

```json
{
    "b704c9fc3655635646356ac2950269f352ea1139"
}
```

Se invalida el token

## API `/api/`

Necesita autenticación en todos los endpoints

### Año Academico Actual `GET` `/year-actual/`

```json
{
  "año_academico_actual": "2025-26"
}
```

### Docencias `/docencias/`

Estos endpoints son solo `GET`

#### Listado

Lista de las docencias, muestra solo los del profesor autenticado, en el año actual.

```json
[
  {
    "id": 1,
    "profesor": {
      "id": 2,
      "nombre": "Émilie Jardin",
      "email": "a@profes.es",
      "activo": true
    },
    "modulo": {
      "id": 3,
      "nombre": "Matematicas",
      "curso": 2,
      "año_academico": "2025-26",
      "ciclo": "ESO"
    },
    "grupo": {
      "nombre": "ESOM2",
      "curso": 2,
      "ciclo": "ESO"
    }
  }
]
```

### Módulos `/modulos/`

Estos endpoints son solo `GET`

#### Listado

Lista de los modulos

```json
[
  {
    "id": 2,
    "nombre": "Física",
    "curso": 1,
    "año_academico": "2025-26",
    "ciclo": "ESO"
  },
  {
    "id": 1,
    "nombre": "Literatura",
    "curso": 1,
    "año_academico": "2025-26",
    "ciclo": "ESO"
  },
  {
    "id": 3,
    "nombre": "Matematicas",
    "curso": 2,
    "año_academico": "2025-26",
    "ciclo": "ESO"
  }
]
```

#### Detalle `/<pk>/`

```json
{
  "id": 1,
  "nombre": "Literatura",
  "curso": 1,
  "año_academico": "2025-26",
  "ciclo": "ESO"
}
```

#### Detalle Temario `/<pk>/temario/`

```json
[
  {
    "id": 1,
    "numero_tema": 1,
    "titulo": "Integrales",
    "modulo": 3
  },
  {
    "id": 2,
    "numero_tema": 2,
    "titulo": "Ecuaciones diferenciales",
    "modulo": 3
  },
  {
    "id": 3,
    "numero_tema": 3,
    "titulo": "Teoria de lenguajes",
    "modulo": 3
  }
]
```

### Seguimientos faltantes `/seguimientos-faltantes/<slug:año_academico>/<int:mes>/`

Encuentra las docencias con seguimientos faltantes del profesor autenticado para el año (formato:2024-25) y mes concretos.
Puede tener el modificador opcional `?all` para tener todos los seguimientos faltantes, solo funciona para admins.

```json
[
  {
    "id": 1,
    "profesor": {
      "id": 2,
      "nombre": "Émilie Jardin",
      "email": "a@profes.es"
    },
    "modulo": {
      "id": 3,
      "nombre": "Matematicas",
      "curso": 2,
      "año_academico": "2025-26",
      "ciclo": "ESO"
    },
    "grupo": {
      "nombre": "ESOM2",
      "curso": 2,
      "ciclo": "ESO"
    }
  }
]
```

### Seguimientos faltantes anual `/seguimientos-faltantes-anual/<slug:año_academico>/`

Encuentra las docencias con seguimientos faltantes para un año académico completo (formato: 2024-25), organizadas por mes.
Para cada mes, devuelve una lista con los IDs de las docencias que no tienen seguimiento.
Por defecto, solo muestra los seguimientos faltantes del profesor autenticado.
Puede tener el modificador opcional `?all` para mostrar todos los seguimientos faltantes, solo funciona para admins.

```json
{
  "1": [2, 5, 8],
  "2": [2, 5],
  "3": [5, 8, 10],
  "4": [2, 5, 8, 10],
  "5": [5, 8]
}
```

### Seguimientos `/seguimientos/`

#### Listado `POST, GET`

Consigue los seguimientos del profesor autenticado. Se puede filtrar con los parametros tal que `?year=2024-25` y `?mes=4`. Filtra por defecto por el año actual

```json
[
  {
    "id": 44,
    "profesor": {
      "id": 95,
      "nombre": "Emilie",
      "email": "b@profes.es",
      "activo": true,
      "is_admin": false
    },
    "modulo": {
      "id": 76,
      "ciclo": {
        "id": 53,
        "nombre": "DAW",
        "año_academico": "2025-26"
      },
      "nombre": "Tecnologias Web",
      "curso": 1
    },
    "grupo": {
      "id": 59,
      "nombre": "DAW1M",
      "curso": 1,
      "ciclo": 53
    },
    "temario_completado": [76, 77],
    "ultimo_contenido_impartido": "Operadores",
    "estado": "AL_DIA",
    "justificacion_estado": "",
    "cumple_programacion": true,
    "justificacion_cumple_programacion": "",
    "mes": 4,
    "evaluacion": "PRIMERA",
    "temario_actual": 78,
    "docencia": 84
  },
  {
    "id": 45,
    "profesor": {
      "id": 1,
      "nombre": "Adrian",
      "email": "adrianpuyetm@gmail.com",
      "activo": true,
      "is_admin": true
    },
    "modulo": {
      "id": 76,
      "ciclo": {
        "id": 53,
        "nombre": "DAW",
        "año_academico": "2025-26"
      },
      "nombre": "Tecnologias Web",
      "curso": 1
    },
    "grupo": {
      "id": 60,
      "nombre": "DAW1T",
      "curso": 1,
      "ciclo": 53
    },
    "temario_completado": [76, 77],
    "ultimo_contenido_impartido": "Lambdas",
    "estado": "AL_DIA",
    "justificacion_estado": "",
    "cumple_programacion": true,
    "justificacion_cumple_programacion": "",
    "mes": 5,
    "evaluacion": "SEGUNDA",
    "temario_actual": 78,
    "docencia": 86
  }
]
```

#### Detalle `PUT, PATCH, GET` `/<pk>/`

Recibe:

```json
{
  "id": 1,
  "temario_completado": [76, 77],
  "ultimo_contenido_impartido": "Ultimo contenido",
  "estado": "ADELANTADO", //(ATRASADO, AL_DIA)
  "justificacion_estado": "justifiacion",
  "cumple_programacion": true,
  "justificacion_cumple_programacion": "justificiacion",
  "mes": 5,
  "evaluacion": "SEGUNDA", //(PRIMERA, TERCERA)
  "temario_actual": 1,
  "docencia": 1
}
```

Devuelve:

```json
{
  "id": 1,
  "profesor": {
    "id": 2,
    "nombre": "Émilie Jardin",
    "email": "a@profes.es"
  },
  "año_academico": "2025-26",
  "ultimo_contenido_impartido": "Integracion por partes - 4",
  "temario_completado": [76, 77],
  "estado": "ADELANTADO",
  "justificacion_estado": "",
  "cumple_programacion": true,
  "justificacion_cumple_programacion": "",
  "mes": 5,
  "temario_actual": 1,
  "docencia": 1
}
```

### Enviar recordatorios `POST` - `/enviar-recordatorios/`

Envia un recordatorio por email a todas las docencias que se incluyan en el cuerpo de la petición

```json
"docencias":[1,4,5],
"mes": 4
```

Devuelve

```json
{
  "status": "success",
  "detail": "Se enviaron 2 recordatorios de seguimiento",
  "emails_enviados": 2,
  "total_profesores": 2,
  "profesores_no_activos": [],
  "docencias_no_encontradas": []
}
```
