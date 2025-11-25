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


2. Install OSGeo4W: https://download.osgeo.org/osgeo4w/v2/osgeo4w-setup.exe 
   The database connection requires it for spatial data handling

   Set an environment variable for: `SPATIALITE_LIBRARY_PATH=C:\OSGeo4W\bin\mod_spatialite.dll`
   Add the bin to your windows system PATH: `C:\OSGeo4W\bin`

3. GCP Buckets
   This application also needs to use a GCP storage bucket when you setup the ENV file for the project you must cofig a GCS_IMAGES_BUCKET and GCS_SERVICE_ACCOUNT_FILE the service account file is created in GCP IAM when you make a new service account the json file can be generated there then you must give that service account STORAGE ADMIN role so it can manage the buckets for image storage. While you are there should can also create a bucket for the app to use then set your GCS_IMAGES_BUCKET value to the name of that bucket. 

4. Exiftool
   This application uses exiftool to properly extract exif data from image files you must get this from here:
   `https://exiftool.org/`
   then set your .env EXIF_TOOL_PATH to the exiftool.exe file that you downloaded

5. env file
   your .env file should live in the root of the project and look something like this now:
```
```
   ```
      FRONTEND_URL=https://heathgate.ngis.com.au
      ENV_STATE=global
      DATABASE_PATH=D:\apps\skyline-fusion-api\data\db\hgr_drone_image_db_dev.gpkg
      DATA_PATH=D:\apps\skyline-fusion-api\data
      EXIF_TOOL_PATH=D:\apps\exiftool\exiftool.exe

      GCS_IMAGES_BUCKET=heathgate-drone-images-dev
      GCS_SERVICE_ACCOUNT_FILE=D:\apps\skyline-fusion-api\service-account.json
   ```
   ```
   ```

6. copy the application into the server ie
    ```
    C:\apps\skyline-fusion-api\
    .env
    requirements.txt
    main.py
    api\...
    logs\         (create)
    ```

7. from powershell navigate to the application directory, install the python virtual environment and python dependancies
    ``` 
    cd C:\apps\skyline-fusion-api
    py -3.11 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install --upgrade pip
    pip install -r requirements.txt
    # if not already pinned
    pip install uvicorn[standard] fastapi asgi-correlation-id
    ```
8. Confirm it runs locally first using:
    ```
    .\.venv\Scripts\Activate.ps1
    uvicorn api.main:app --host 127.0.0.1 --port 8000
    ```
9. next download a copy of the NSSM.exe from: `https://nssm.cc/download`
10. now, run the commands below to create and start the fastapi application as as service:
    ```
    D:\apps\nssm\nssm.exe install SkylineFusionAPI "D:\apps\skyline-fusion-api\run-uvicorn.bat"
    D:\apps\nssm\nssm.exe set SkylineFusionAPI AppDirectory D:\apps\skyline-fusion-api
    D:\apps\nssm\nssm.exe set SkylineFusionAPI Start SERVICE_AUTO_START
    D:\apps\nssm\nssm.exe set SkylineFusionAPI AppStdout D:\apps\skyline-fusion-api\logs\stdout.log
    D:\apps\nssm\nssm.exe set SkylineFusionAPI AppStderr D:\apps\skyline-fusion-api\logs\stderr.log

    D:\apps\nssm\nssm.exe start SkylineFusionAPI
    D:\apps\nssm\nssm.exe status SkylineFusionAPI
    type D:\apps\skyline-fusion-api\logs\stderr.log
    ```
11. next we need to setup the reverse proxy so it runs through IIS via HTTPS and via the domain of you iis server first install the Application Request Routing from
  - ARR Installer: `https://www.iis.net/downloads/microsoft/application-request-routing`
12. create an iis application in IIS with:
    - alias: skyline-fusion-api
    - physical path: C:\apps\skyline-fusion-api
13. make sure iis can read that folder so go in and set the security to grant access to IIS_IUSRS
14. the correct web.config is already in this application repo so just use that but make sure its in that application folder.
15. next in IIS click on the server node then: 
    `Application Request Routing > server proxy settings > enable proxy`
16. Go into the IIS Default Web Site > application URL rewrite and add the below server variables:
    ```Default Web Site → URL Rewrite → View Server Variables → Add…
    HTTP_X_FORWARDED_PROTO
    HTTP_X_FORWARDED_HOST
    HTTP_X_FORWARDED_FOR```
17. next go into configuration Editor under default website and unlock:
    - system.webServer/webSocket
    - system.webServer/rewrite/rules
    - system.webServer/rewrite/allowedServerVariables
18. Now I had to also rebind the site to HTTPS
    ```Site → Bindings…

    HTTP 80: hostname skyline.ngis.com.au (or blank if catch-all)

    HTTPS 443: hostname skyline.ngis.com.au, select the correct cert. probably wildcard 2025```
19. now restart IIS and test it
