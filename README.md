# Backend-SistemaDeSeguimiento

Backend de la aplicación de seguimiento

- [Diagrama Entidad-Relación](https://dbdiagram.io/e/67cf0d1975d75cc84489350e/67d0147c75d75cc844a50b2c)

## Setup del entorno de desarollo

1. Iniciar un contenedor de Postgres `docker run -e POSTGRES_PASSWORD=1234 -e POSTGRES_DB=seguimientos -d -p 5432:5432 postgres:latest`
2. Iniciar el shell pipenv `pipenv shell`
3. Instalar las dependencias `pipenv install`
4. Iniciar la aplicación `python manage.py runserver`

## Endpoints

Filtra por defecto por el último año academico.

- `/login`
- `/register`
- `/reset-password`
- `/profesores/` CRUD de profesores
- `/profesores/<id_profesor>` CRUD de un profesor
- `/ciclos` CRUD de ciclos
- `/ciclos/<nombre_ciclo>` CRUD de un ciclo
- `/grupos` CRUD de grupos
- `/grupos/<nombre_grupo>` CRUD de un grupo
- `/modulos/` CRUD de modulos
- `/modulos/<id_modulo>` CRUD de un modulo
- `/modulos/<id_modulo>/temario/` CRUD del temario de un modulo
- `/modulos/<id_modulo>/temario/<id_temario>` CRUD de una unidad de temario de un modulo
- `/docencias/` CRUD de las docencias
- `/docencias/<id_docencia>` CRUD de una de las docencias
- `/seguimientos/` CRUD de los seguimientos
- `/seguimientos/<id_seguimiento>` CRUD de uno de los seguimientos
- `/seguimientos-faltantes/<mes>` Devuelve una lista de los seguimientos no realizados en el mes indicado del último año academico
- `/enviar-recordatorio/` Envia un recordatorio por email a todas las docencias que se incluyan en el cuerpo de la petición
- `/descargar-seguimientos/<mes>` Devuelve un .xlsx con los seguimientos del mes
