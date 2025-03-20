# Backend-SistemaDeSeguimiento

- [Backend-SistemaDeSeguimiento](#backend-sistemadeseguimiento)
  - [Setup del entorno de desarollo](#setup-del-entorno-de-desarollo)
  - [Endpoints](#endpoints)
    - [Autenticación](#autenticación)
      - [Registro en la app - POST `/auth/users/`](#registro-en-la-app---post-authusers)
      - [Login - POST `/auth/token/login/`](#login---post-authtokenlogin)
      - [Login - POST `/auth/token/logout/`](#login---post-authtokenlogout)
    - [WIP](#wip)

Backend de la aplicación de seguimiento

- [Diagrama Entidad-Relación](https://dbdiagram.io/e/67cf0d1975d75cc84489350e/67d0147c75d75cc844a50b2c)

## Setup del entorno de desarollo

1. Iniciar un contenedor de Postgres `docker run -e POSTGRES_PASSWORD=1234 -e POSTGRES_DB=seguimientos -d -p 5432:5432 postgres:latest`
2. Iniciar el shell pipenv `pipenv shell`
3. Instalar las dependencias `pipenv install`
4. Iniciar la aplicación `python manage.py runserver`

## Endpoints

### Autenticación

#### Registro en la app - POST `/auth/users/`

```json
{
  "email": "email@dominio.com",
  "nombre": "Fulano de Tal",
  "password": "password"
}
```

#### Login - POST `/auth/token/login/`

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

#### Login - POST `/auth/token/logout/`

Necesita autenticación

```json
{
    "b704c9fc3655635646356ac2950269f352ea1139"
}
```

Se invalida el token

### WIP

- `/seguimientos/` CRUD de los seguimientos
- `/seguimientos/<id_seguimiento>` CRUD de uno de los seguimientos
- `/seguimientos-faltantes/<mes>` Devuelve una lista de los seguimientos no realizados en el mes indicado del último año academico
- `/enviar-recordatorio/` Envia un recordatorio por email a todas las docencias que se incluyan en el cuerpo de la petición
- `/descargar-seguimientos/<mes>` Devuelve un .xlsx con los seguimientos del mes indicado del último año academico
