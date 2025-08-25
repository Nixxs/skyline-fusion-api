# API-Boilerplate Project

## Description

This is a biolerplate project, it acts as a starting point for your backend and is based on python fast-api. It comes with user authentication with JWT tokens, logging and test infrastructure so you can get started right away making your application tables and and routes. Protect them using dependancy injection as shown in the get-user route.

## Dependancies

### Docker

You will need to setup a local postgres database instance for the application you can do this easily using the the included docker-compose but you will need to make sure you have docker desktop installed first.

    - https://docker.com

### Test Database

Before you run pytest, make sure you have a database already created in your docker postgresdb called `test-db` you can change the nasme of this in the `config.py` or even setup the docker-compose to spin that up for you automatically but you only need to do it once so I normally just use phadmin to do it manually.

## Getting set up

1. After cloneing the project, create a virtual environment with:
    - `python -m venv .venv`
2. next install all the dependancies with
    - `python -m pip install -r requirements.txt`
    - `python -m pip install -r requirements-dev.txt`
3. now setup setup your `.env` in the root of the project:
    ```
    ENV_STATE=global
    DB_NAME=api-db
    DB_HOST=localhost
    DB_PORT=5432 
    DB_SSL=prefer 
    DB_USER=postgres
    DB_PASSWORD=pa55word

    FRONTEND_URL=http://127.0.0.1:8080
    JWT_SECRET=1234abcd
    ```
3. make sure docker desktop is running then start the database via docker-compose:
    - `docker-compose up -d`
    - Note: this will also start up a docker version of the application, you can use this to test against as well. 
4.  start the local dev environment with (note that the port is 8001 because docker will run on 8000)
    - `uvicorn api.main:app --reload --port 8001`

## How to build stuff

### Database Tables and Models

Create database tables in the database.py using SQL Alchemy. These tables will be created automatically when the application starts.

Models are used when handling data that is going to and from the users of the API. Create new models in the /api/models folder.

### Routes

### Protecting Routes

### Tests

## Deploying to IIS on a windows server

1. install python on the windows server first for all users so its installed in program files
2. copy the application into the server ie
    ```
    C:\apps\skyline-fusion-api\
    .env
    requirements.txt
    main.py
    api\...
    logs\         (create)
    ```
3. from powershell navigate to the application directory, install the python virtual environment and python dependancies
    ``` 
    cd C:\apps\skyline-fusion-api
    py -3.11 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install --upgrade pip
    pip install -r requirements.txt
    # if not already pinned
    pip install uvicorn[standard] fastapi asgi-correlation-id
    ```
4. Confirm it runs locally first using:
    ```
    .\.venv\Scripts\Activate.ps1
    uvicorn main:app --host 127.0.0.1 --port 8000
    ```
5. next download a copy of the NSSM.exe from: `https://nssm.cc/download`
6. now, run the commands below to create and start the fastapi application as as service:
    ```
    C:\apps\nssm\nssm.exe install SkylineFusionAPI "C:\apps\skyline-fusion-api\run-uvicorn.bat"
    C:\apps\nssm\nssm.exe set SkylineFusionAPI AppDirectory C:\apps\skyline-fusion-api
    C:\apps\nssm\nssm.exe set SkylineFusionAPI Start SERVICE_AUTO_START
    C:\apps\nssm\nssm.exe set SkylineFusionAPI AppStdout C:\apps\skyline-fusion-api\logs\stdout.log
    C:\apps\nssm\nssm.exe set SkylineFusionAPI AppStderr C:\apps\skyline-fusion-api\logs\stderr.log

    C:\apps\nssm\nssm.exe start SkylineFusionAPI
    C:\apps\nssm\nssm.exe status SkylineFusionAPI
    type C:\apps\skyline-fusion-api\logs\stderr.log
    ```
7. next we need to setup the reverse proxy so it runs through IIS via HTTPS and via the domain of you iis server first install the Application Request Routing from
  - ARR Installer: `https://www.iis.net/downloads/microsoft/application-request-routing`
8. create an iis application in IIS with:
    - alias: skyline-fusion-api
    - physical path: C:\apps\skyline-fusion-api
9. make sure iis can read that folder so go in and set the security to grant access to IIS_IUSRS
10. the correct web.config is already in this application repo so just use that but make sure its in that application folder.
11. next in IIS click on the server node then: 
    `Application Request Routing > server proxy settings > enable proxy`
12. Go into the IIS Default Web Site > application URL rewrite and add the below server variables:
    ```Default Web Site → URL Rewrite → View Server Variables → Add…
    HTTP_X_FORWARDED_PROTO
    HTTP_X_FORWARDED_HOST
    HTTP_X_FORWARDED_FOR```
13. next go into configuration Editor under default website and unlock:
    - system.webServer/webSocket
    - system.webServer/rewrite/rules
    - system.webServer/rewrite/allowedServerVariables
14. Now I had to also rebind the site to HTTPS
    ```Site → Bindings…

    HTTP 80: hostname skyline.ngis.com.au (or blank if catch-all)

    HTTPS 443: hostname skyline.ngis.com.au, select the correct cert. probably wildcard 2025```
15. now restart IIS and test it