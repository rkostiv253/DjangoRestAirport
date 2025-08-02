# DjangoRestAirport

This is an API for airport service build with Python using Django Rest Framework. This app allows to add countries, 
cities, airports, airplane types and airplanes, routes, create flights and order tickets. 

## Installation 

Python3 must be already installed
```shell
git clone https://github.com/rkostiv253/tasktodo-task-manager.git
cd DjangoRestAirport
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
set DB_HOST=<your db hostname>
set DB_NAME=<your db name>
set DB_USER=<your db username>
set DB_PASSWORD=<your db user password>
set SECRET_KEY=<your secret key>
python3 manage.py makemigrations
python3 manage.py migrate
```

## Run with docker

Docker should be installed
```shell
docker-compose build
docker-compose up
```

## Features

- JWT Authenticated
- Admin panel /admin/
- Documentation is located in api/doc/swagger
- Add countries, cities, airports, airplane types, airplanes and routes 
- Create, edit and delete flights
- Order tickets

## Tech stack

- **Backend**: Python, Django Rest Framework
- **Database**: SQLite, PostgreSQL


├── airport
│   └──  management
│        └── commands
│           └── __init__.py
│           └── wait_for_db
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── permissions.py
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
├── airport_service
    ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py

├── media
│   └── uploads
│       └── routes
└── user
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── permissions.py
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
├── .dockerignore
├── .env
├── .flake8
├── .gitignore
├── docker-compose.yaml
├── Dockerfile
├── manage.py
├── README.md
├── requirements.txt