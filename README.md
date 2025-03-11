# Backend-SistemaDeSeguimiento
Backend de la aplicación de seguimiento
- [Diagrama Entidad-Relación](https://dbdiagram.io/e/67cf0d1975d75cc84489350e/67d0147c75d75cc844a50b2c)

## Setup del entorno de desarollo

1. Iniciar un contenedor de Postgres `docker run -e POSTGRES_PASSWORD=1234 -e POSTGRES_DB=seguimientos -d -p 5432:5432 postgres:latest`
2. Iniciar el shell pipenv `pipenv shell`
3. Instalar las dependencias `pipenv install`
4. Iniciar la aplicación `python manage.py runserver`
