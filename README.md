- [Setup del entorno de desarollo](#setup-del-entorno-de-desarollo)
- [Endpoints](#endpoints)
  - [Autenticación - `/auth/`](#autenticación---auth)
    - [Registro en la app - POST `/users/`](#registro-en-la-app---post-users)
    - [Login - POST `/token/login/`](#login---post-tokenlogin)
    - [Login - POST `/token/logout/`](#login---post-tokenlogout)
  - [API `/api/`](#api-api)
    - [Año Academico Actual `GET` `/current-year/`](#año-academico-actual-get-current-year)
    - [Docencias `/docencias/`](#docencias-docencias)
      - [Listado](#listado)
    - [Módulos `/modulos/`](#módulos-modulos)
      - [Listado](#listado-1)
      - [Detalle `/<pk>/`](#detalle-pk)
      - [Detalle Temario `/<pk>/temario/`](#detalle-temario-pktemario)
    - [Seguimientos faltantes `/seguimientos-faltantes/<slug:año_academico>/<int:mes>/`](#seguimientos-faltantes-seguimientos-faltantesslugaño_academicointmes)
    - [Seguimientos `/seguimientos/`](#seguimientos-seguimientos)
      - [Listado `GET`](#listado-get)
      - [Detalle `POST, PUT, PATCH, GET` `/<pk>/`](#detalle-post-put-patch-get-pk)
    - [WIP](#wip)

Backend de la aplicación de seguimiento

- [Diagrama Entidad-Relación](https://dbdiagram.io/e/67cf0d1975d75cc84489350e/67d0147c75d75cc844a50b2c)

# Setup del entorno de desarollo

1. Iniciar un contenedor de Postgres `docker run -e POSTGRES_PASSWORD=1234 -e POSTGRES_DB=seguimientos -d -p 5432:5432 postgres:latest`
2. Iniciar el shell pipenv `pipenv shell`
3. Instalar las dependencias `pipenv install`
4. Añadir los ficheros estaticos `python manage.py collectstatic`
5. Iniciar la aplicación `python manage.py runserver`

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

### Año Academico Actual `GET` `/current-year/`

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
    "impartido": true,
    "modulo": 3
  },
  {
    "id": 2,
    "numero_tema": 2,
    "titulo": "Ecuaciones diferenciales",
    "impartido": false,
    "modulo": 3
  },
  {
    "id": 3,
    "numero_tema": 3,
    "titulo": "Teoria de lenguajes",
    "impartido": false,
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

### Seguimientos `/seguimientos/`

#### Listado `GET`

Consigue los seguimientos del profesor autenticado. Se puede filtrar con los parametros tal que `?year=2024-25` y `?mes=4`. Filtra por defecto por el año actual

```json
[
  {
    "id": 1,
    "profesor": {
      "id": 2,
      "nombre": "Émilie Jardin",
      "email": "a@profes.es"
    },
    "año_academico": "2025-26",
    "ultimo_contenido_impartido": "Integracion por partes - 4",
    "estado": "ADELANTADO",
    "justificacion_estado": "",
    "cumple_programacion": true,
    "justificacion_cumple_programacion": "",
    "mes": 5,
    "temario_actual": 1,
    "docencia": 1
  },
  {
    "id": 2,
    "profesor": {
      "id": 2,
      "nombre": "Émilie Jardin",
      "email": "a@profes.es"
    },
    "año_academico": "2025-26",
    "ultimo_contenido_impartido": "Introduccion",
    "estado": "AL_DIA",
    "justificacion_estado": "",
    "cumple_programacion": true,
    "justificacion_cumple_programacion": "",
    "mes": 7,
    "temario_actual": 2,
    "docencia": 1
  }
]
```

#### Detalle `POST, PUT, PATCH, GET` `/<pk>/`

Recibe:

```json
{
  "id": 1,
  "ultimo_contenido_impartido": "Ultimo contenido",
  "estado": "ADELANTADO", //(ATRASADO, AL_DIA)
  "justificacion_estado": "justifiacion",
  "cumple_programacion": true,
  "justificacion_cumple_programacion": "justificiacion",
  "mes": 5,
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
  "estado": "ADELANTADO",
  "justificacion_estado": "",
  "cumple_programacion": true,
  "justificacion_cumple_programacion": "",
  "mes": 5,
  "temario_actual": 1,
  "docencia": 1
}
```

### WIP

- `/enviar-recordatorio/` Envia un recordatorio por email a todas las docencias que se incluyan en el cuerpo de la petición
