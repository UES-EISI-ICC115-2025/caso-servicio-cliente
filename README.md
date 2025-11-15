### Universidad de El Salvador
### Facultad de Ingeniería y Arquitectura
### Escuela de Ingeniería Sistemas Informáticos

![Logo Universidad de El Salvador](imagenes/universidad-de-el-salvador.png "Universidad de El Salvador")

#### Tema:
### Infraestructura en la Nube para Soportar Servicios de Inteligencia Artificial Enfocados en la Atención al Cliente de Internet Residencial
#### Docente:
### MSc. Damián Morales
#### Estudiantes:

| Carnet  | Apellido              | Nombre           |
|---------|-----------------------|------------------|
| HC07003 | Herrera Cañas         | Jared Wilfredo   |
| MM18057 | Monterrosa Morales    | Andrea Melissa   |

### Ciudad Universitaria, noviembre 2025

## Caracteristicas VM

| Componente       | Especificación                                                                 |
|-----------------|-------------------------------------------------------------------------------|
| **Sistema Operativo** | Ubuntu Server 24.04.3 LTS                                                    |
| **Imagen ISO**   | `ubuntu-24.04.3-live-server-amd64.iso`                                        |
| **Enlace de Descarga** | [Ubuntu 24.04.3 Server ISO](https://ubuntu.com/download/server/thank-you?version=24.04.3&architecture=amd64&lts=true) |
| **Virtualización** | QEMU / KVM                                                                 |
| **vCPUs**       | 4                                                                             |
| **Memoria**     | 8192 MiB (8 GiB)                                                               |
| **Tamaño de Disco**   | 25 GB                                                                         |


## Diagrama de componentes
![Diagrama de Componentes de Arquitectura para Entrenamiento de IA](imagenes/diagrama_de_componentes.png "Diagrama de Componentes de Arquitectura para Entrenamiento de IA")

*Diagrama de Componentes de Arquitectura para Entrenamiento de IA*  

# **Manual de Despliegue de Stack en Ubuntu Server 22.04**

El presente documento detalla el procedimiento para la instalación y configuración del stack de para Inteligencia Artificial que se compone de Apache Airflow, Ollama, Postgresql, Chroma DB, RASA API Rest y Frontend App en un entorno de servidor Ubuntu 22.04, utilizando un entorno virtual de Python y PostgreSQL como base de datos de metadatos de producción

1. ##  **Requisitos del Sistema**

   Se recomienda cumplir con los siguientes requisitos mínimos para un despliegue de producción:

   * **Sistema Operativo:** Ubuntu Server 22.04 LTS.  
   * **Memoria RAM:** Mínimo 4 GB.  
   * **Python:** Versión 3.8 o superior (Python 3.10 es la versión predeterminada en Ubuntu 22.04).  
   * **Base de Datos:** PostgreSQL (requisito indispensable para entornos de producción, ya que SQLite se limita a entornos de desarrollo y pruebas).

2. ##  **Configuración Inicial del Entorno**

   Se establece un entorno virtual de Python para garantizar el aislamiento de las dependencias de Airflow y se instalan las librerías de desarrollo necesarias para la conexión con PostgreSQL.

   1. ### **Instalación de Dependencias y Entorno Virtual**

   Ejecute los siguientes comandos en la terminal del servidor:

   ```bash

   \# Actualización del índice de paquetes e instalación de dependencias  
   sudo apt update  
   sudo apt install python3-venv libpq-dev \-y

   \# Creación del entorno virtual para Airflow  
   python3 \-m venv airflow\_env

   \# Activación del entorno virtual  
   source airflow\_env/bin/activate
   ```
   El *prompt* de la terminal debe reflejar la activación del entorno mediante el prefijo (airflow\_env).

3. ### **Instalación y Configuración de PostgreSQL**

Airflow requiere una base de datos robusta para el almacenamiento de sus metadatos. Se configura PostgreSQL para este propósito.

1. **Instalación de PostgreSQL**

```bash

sudo apt install postgresql postgresql-contrib \-y  
sudo systemctl start postgresql
```
2. **Creación de Usuario y Base de Datos para Airflow**

Acceda a la consola de PostgreSQL y configure las credenciales. **Es crucial utilizar una contraseña robusta y segura**.

```bash

sudo \-u postgres psql
```
Dentro de la consola (postgres=\#), ejecute las sentencias SQL. Reemplace \[CONTRASEÑA\_FUERTE\] por el valor seleccionado:

```SQL

CREATE USER airflow PASSWORD '\[CONTRASEÑA\_FUERTE\]';  
CREATE DATABASE airflowdb;  
ALTER DATABASE airflowdb OWNER TO airflow;  
GRANT ALL PRIVILEGES ON DATABASE airflowdb TO airflow;  
\\q
```
4. ### **Instalación de Apache Airflow**

Se define el directorio *home* de Airflow y se procede con la instalación a través de pip, utilizando el mecanismo de *constraint files* para garantizar la compatibilidad de las dependencias.

1. **Definición del AIRFLOW\_HOME e Instalación**

```bash

\# Definición del directorio raíz de Airflow (AIRFLOW\_HOME)  
export AIRFLOW\_HOME=\~/airflow

\# Variables de la versión de Airflow y Python para la URL de constraints  
AIRFLOW\_VERSION=2.9.3 \# Ajustar a la versión requerida  
PYTHON\_VERSION="$(python3 \-c 'import sys; print(f"{sys.version\_info.major}.{sys.version\_info.minor}")')"  
CONSTRAINT\_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW\_VERSION}/constraints-${PYTHON\_VERSION}.txt"

\# Instalación de Apache Airflow con el extra de PostgreSQL  
pip install "apache-airflow\[postgres\]==${AIRFLOW\_VERSION}" \--constraint "${CONSTRAINT\_URL}"
```
2. **Configuración del Backend de la Base de Datos**

   1. **Inicialización de la Base de Datos (Generación de airflow.cfg):**  
      ```bash  
      airflow db init
```
      2. Modificación del Archivo de Configuración:  
         Edite el archivo $AIRFLOW\_HOME/airflow.cfg (ej., nano \~/airflow/airflow.cfg). Localice la sección \[database\] y actualice el parámetro sql\_alchemy\_conn con la cadena de conexión de PostgreSQL, reemplazando \[CONTRASEÑA\_FUERTE\] con el valor real:
```
         \[database\]  
         sql\_alchemy\_conn \= postgresql+psycopg2://airflow:\[CONTRASEÑA\_SEGURA\]@localhost/airflowdb
```
      3. **Aplicación de Migraciones a la Base de Datos:**  
         ```bash  
         airflow db migrate
```
   3. ### **Creación del Usuario Administrador**

Se requiere un usuario con el rol de Administrador para el acceso y gestión inicial a través de la interfaz web.

```bash

airflow users create \\  
    \--username admin \\  
    \--firstname Administrador \\  
    \--lastname Airflow \\  
    \--role Admin \\  
    \--email administrador@dominio.com \\  
    \--password \[CONTRASEÑA\_ADMIN\]
```
4. ### **Inicio de los Componentes de Airflow**

Para una validación funcional inmediata, inicie los componentes en sesiones de terminal separadas (o en segundo plano mediante nohup):  
**Sesión 1: Servidor Web (Webserver)**

```bash

airflow webserver \-p 8080
```
**Sesión 2: Planificador (Scheduler)**

```bash

airflow scheduler
```
5. **Acceso a la Interfaz de Usuario**

Una vez que ambos componentes estén activos, la interfaz web de Airflow será accesible a través del puerto 8080 de la dirección IP del servidor (ej.., http://\[IP\_DEL\_SERVIDOR\]:8080).  
Utilice las credenciales del usuario administrador creadas en el **Paso 5** para el inicio de sesión.

6. ## **Configuración de Airflow como Servicios Systemd**

Para garantizar que el **Webserver** y el **Scheduler** de Airflow se ejecuten de manera persistente en segundo plano y se reinicien automáticamente tras fallos o reboots, se configuran como servicios **Systemd**.

7. ### **Creación del Servicio Systemd para el Webserver**

Cree el archivo de definición del servicio:

```bash

sudo nano /etc/systemd/system/airflow-webserver.service
```
Pegue la siguiente configuración. **Asegúrese de reemplazar** \[USUARIO\] con su nombre de usuario de Linux y \[RUTA\_HOME\] con la ruta absoluta de su directorio personal (ej: /home/miusuario).
```

\[Unit\]  
Description=Apache Airflow Webserver Daemon  
After=network.target postgresql.service  
Wants=postgresql.service

\[Service\]  
Environment=AIRFLOW\_HOME=\[RUTA\_HOME\]/airflow  
User=\[USUARIO\]  
Group=\[USUARIO\]  
Type=simple  
ExecStart=\[RUTA\_ENV\]/airflow\_env/bin/airflow webserver  
Restart=on-failure  
RestartSec=5s  
StandardOutput=journal  
StandardError=journal

\[Install\]  
WantedBy=multi-user.target
```
8. ### **Creación del Servicio Systemd para el Scheduler**

Cree el archivo de definición del servicio para el planificador:

```bash

sudo nano /etc/systemd/system/airflow-scheduler.service
```
Pegue la siguiente configuración, ajustando nuevamente \[USUARIO\] y \[RUTA\_HOME\]:

```

\[Unit\]  
Description=Apache Airflow Scheduler Daemon  
After=network.target airflow-webserver.service  
Wants=airflow-webserver.service

\[Service\]  
Environment=AIRFLOW\_HOME=\[RUTA\_HOME\]/airflow  
User=\[USUARIO\]  
Group=\[USUARIO\]  
Type=simple  
ExecStart=\[RUTA\_HOME\]/airflow\_env/bin/airflow scheduler  
Restart=always  
RestartSec=5s  
StandardOutput=journal  
StandardError=journal

\[Install\]  
WantedBy=multi-user.target
```
9. ### **Habilitación e Inicio de los Servicios**

Cargue las nuevas definiciones de servicios y actívelas:

```bash

\# Recargar Systemd para leer los nuevos archivos  
sudo systemctl daemon-reload

\# Habilitar los servicios para que inicien automáticamente en el arranque  
sudo systemctl enable airflow-webserver.service  
sudo systemctl enable airflow-scheduler.service

\# Iniciar los servicios  
sudo systemctl start airflow-webserver.service  
sudo systemctl start airflow-scheduler.service

\# Verificar el estado (ambos deben mostrar 'active (running)')  
sudo systemctl status airflow-webserver.service  
sudo systemctl status airflow-scheduler.service
```
5. ### **Configuración de Nginx como Proxy Inverso**

Se configura Nginx para que escuche el tráfico web en el puerto estándar (80) y lo reenvíe internamente al Webserver de Airflow (que opera en el puerto 8080).  
	

1. ### **Instalación de Nginx y Configuración del Firewall**

```bash

\# Instalar Nginx  
sudo apt install nginx \-y

\# Configurar UFW (Uncomplicated Firewall) para permitir tráfico HTTP (puerto 80\)  
sudo ufw allow 'Nginx HTTP'  
sudo ufw reload
```
2. ### **Creación del Archivo de Configuración de Nginx**

Cree un bloque de servidor para Airflow. Reemplace airflow.dominio.com con el dominio público o IP de su servidor.

```bash

sudo nano /etc/nginx/sites-available/airflow
```
Pegue el siguiente bloque de configuración, que maneja el *proxying* y las cabeceras necesarias:

```Nginx

server {  
    listen 80;  
    server\_name dominio.com \[IP\_DEL\_SERVIDOR\]; \# El dominio o IP principal

    \# Bloque de ubicación para manejar la subruta /airflow/  
    location /airflow/ {  
        \# Se requiere el trailing slash ('/') aquí y en base\_url de Airflow  
        proxy\_pass http://127.0.0.1:8080/airflow/; 

        \# Cabeceras estándar para proxy  
        proxy\_set\_header Host $host;  
        proxy\_set\_header X-Real-IP $remote\_addr;  
        proxy\_set\_header X-Forwarded-For $proxy\_add\_x\_forwarded\_for;  
        proxy\_set\_header X-Forwarded-Proto $scheme;  
        proxy\_redirect off;

        \# Directivas requeridas para la subruta de Airflow  
        proxy\_read\_timeout 150;  
        proxy\_connect\_timeout 150;  
    }

    \# Otros bloques 'location' para otros servicios:  
    \# location /servicio\_b/ { ... }  
}
```
3. ### **Activación y Aplicación de la Configuración**

   1. **Crear el enlace simbólico** para activar el sitio:  
      ```bash  
      sudo ln \-s /etc/nginx/sites-available/airflow /etc/nginx/sites-enabled/
```
      2. **Verificar la sintaxis** de la configuración de Nginx:  
         ```bash  
         sudo nginx \-t
```
      3. **Reiniciar Nginx** para aplicar los cambios:  
         ```bash  
         sudo systemctl reload nginx
```
Airflow ahora es accesible a través del puerto 80 estándar de su servidor.

6. ## **Despliegue de Frontend**

Este manual detalla la configuración del servidor de aplicaciones Gradio/Python como un servicio persistente mediante systemd y su exposición pública a través de un proxy inverso NGINX.

1. ### **Requisitos y Preparación** 

Antes de iniciar la configuración del servicio, asegúrese de que:

2. **Entorno Python:** El entorno virtual (app\_env) y todas sus dependencias (Gradio, Flask, requests) estén instaladas.  
   3. **Rutas Absolutas:** Conozca la ruta exacta a su proyecto y al ejecutable de Python.  
      1. **Ejecutable Python:** /home/demo/caso-servicio-cliente/app\_env/bin/python  
      2. **Archivo app.py:** /home/demo/caso-servicio-cliente/app.py

   4. ### **Configuración del Servicio Systemd (Persistencia)**

Crearemos el archivo de servicio que iniciará el script app.py directamente, obligando a Gradio a escuchar en el puerto 8081\.

5. #### **Creación del Archivo de Servicio**

Cree el archivo /etc/systemd/system/app-frontend.service con privilegios de sudo:

```bash

sudo nano /etc/systemd/system/app-frontend.service
```
6. #### **Contenido del Servicio**

Asegúrese de reemplazar las rutas absolutas (/home/demo/...) con las rutas correctas de su servidor.

```bash

\[Unit\]  
Description=Servidor Frontend Gradio/Rasa  
After=network.target

\[Service\]  
\# Usuario bajo el cual se ejecuta el servicio (debe tener permisos en el directorio)  
User=demo  
Group=demo

\# Ruta absoluta al directorio donde reside app.py  
WorkingDirectory=/home/demo/caso-servicio-cliente/

\# Comando de Inicio: Ejecuta el script app.py con el intérprete de Python del venv  
\# Gradio está configurado internamente para usar el puerto 8081\.  
ExecStart=/home/demo/caso-servicio-cliente/app\_env/bin/python /home/demo/caso-servicio-cliente/app.py

StandardOutput=journal  
StandardError=journal  
\# El servicio debe reiniciarse automáticamente en caso de fallo  
Restart=always

\[Install\]  
WantedBy=multi-user.target
```
7. ### **Gestión y Activación del Servicio 🚀**

Ejecute los siguientes comandos para registrar e iniciar el servicio:

1. **Recargar Systemd:**  
   ```bash  
   sudo systemctl daemon-reload
```
   2. **Habilitar el Servicio** (para inicio automático al boot):  
      ```bash  
      sudo systemctl enable app-frontend.service
```
      3. **Iniciar el Servicio:**  
         ```bash  
         sudo systemctl start app-frontend.service
```
#### **Verificación**

Verifique el estado y los logs para confirmar que Gradio se inició en el puerto 8081:

```bash

sudo systemctl status app-frontend.service  
\# Para ver logs en tiempo real:  
sudo journalctl \-u app-frontend.service \-f
```
8. ### **Configuración de NGINX (Proxy Inverso)**

El servidor Gradio ahora corre internamente en el puerto 8081\. NGINX debe redirigir el tráfico público (puerto 80\) a ese puerto.

9. ### **Edición del Bloque de Servidor**

Edite su archivo de configuración de NGINX (ejemplo: /etc/nginx/sites-available/airflow).  
Asegúrese de que el bloque location / utilice proxy\_pass http://localhost:8081;:

```Nginx

server {  
    listen 80;  
    server\_name dominio.com \[IP\_DEL\_SERVIDOR\]; \# El dominio o IP principal

    \# Bloque de ubicación para manejar la subruta /airflow/  
    location /airflow/ {  
        \# Se requiere el trailing slash ('/') aquí y en base\_url de Airflow  
        proxy\_pass http://127.0.0.1:8080/airflow/; 

        \# Cabeceras estándar para proxy  
        proxy\_set\_header Host $host;  
        proxy\_set\_header X-Real-IP $remote\_addr;  
        proxy\_set\_header X-Forwarded-For $proxy\_add\_x\_forwarded\_for;  
        proxy\_set\_header X-Forwarded-Proto $scheme;  
        proxy\_redirect off;

        \# Directivas requeridas para la subruta de Airflow  
        proxy\_read\_timeout 150;  
        proxy\_connect\_timeout 150;  
    }

    \# Otros bloques 'location' para otros servicios:  
     location / {  
        \# Se requiere el trailing slash ('/') aquí y en base\_url de Airflow  
        proxy\_pass http://127.0.0.1:8081; 

        \# Cabeceras estándar para proxy  
        proxy\_set\_header Host $host;  
        proxy\_set\_header X-Real-IP $remote\_addr;  
        proxy\_set\_header X-Forwarded-For $proxy\_add\_x\_forwarded\_for;  
        proxy\_set\_header X-Forwarded-Proto $scheme;  
        proxy\_redirect off;

        \# Directivas requeridas para la subruta de Airflow  
        proxy\_read\_timeout 150;  
        proxy\_connect\_timeout 150;  
    }

}
```
10. ### **Aplicar la Configuración**

    1. **Verificar Sintaxis:**  
       ```bash  
       sudo nginx \-t
```
       2. **Reiniciar NGINX:**  
          ```bash  
          sudo systemctl restart nginx
```
Con estos pasos, su aplicación Gradio está ejecutándose de forma persistente como un servicio, y es accesible para los usuarios a través del puerto 80 de su dominio.

7. ##  **Despliegue de RASA API Rest y RASA Actions** 

   1. **Requisitos**

Antes de crear los servicios, debes encontrar y verificar las rutas exactas de su proyecto y entorno virtual. Esto es vital para que systemd pueda iniciar los programas.

1. **Ruta del Proyecto:** La ruta absoluta a la carpeta raíz de tu proyecto Rasa (ej: /home/demo/caso-servicio-cliente).  
   2. **Ruta del Ejecutable de Python/Rasa:** La ruta al ejecutable de rasa dentro de tu entorno virtual.  
      * Para encontrarla, activa tu entorno (source .venv/bin/activate) y ejecuta:  
        ```bash  
        which rasa
```
      * *Ejemplo de resultado:* ```/home/demo/caso-servicio-cliente/.venv/bin/rasa```

   2. ### **Creación de DB**

```bash

sudo \-u postgres psql
```
Dentro de la consola (postgres=\#), ejecute las sentencias SQL. Reemplace \[CONTRASEÑA\_FUERTE\] por el valor seleccionado:

```SQL

CREATE USER demo PASSWORD '\[CONTRASEÑA\_FUERTE\]';  
CREATE DATABASE rasa\_conversations;  
ALTER DATABASE rasa\_conversations OWNER TO demo;  
GRANT ALL PRIVILEGES ON DATABASE rasa\_conversations TO demo;  
\\q
```
Modificar la contraseña en endpoints.yml \> tracker\_store \> url

3. ### **Creación de Archivos de Servicio Systemd**

Crearás dos archivos en el directorio de configuración del sistema (/etc/systemd/system/). Esto requiere privilegios de sudo.

4. ### **Servicio Principal de Rasa (/etc/systemd/system/rasa-core.service)**

Este servicio ejecuta el motor de diálogo principal y la API REST, conectado a tu PostgreSQL (endpoints.yml).

```bash

\[Unit\]  
Description=Servidor Central de Rasa  
After=network.target

\[Service\]  
\# Usuario bajo el cual se ejecutará el servicio (cambia a tu usuario)  
User=demo  
Group=demo

\# Directorio de trabajo: la raíz de tu proyecto Rasa  
WorkingDirectory=/home/demo/caso-servicio-cliente/

\# Comando de Inicio: Usa la ruta absoluta al ejecutable de Rasa  
ExecStart=/home/demo/caso-servicio-cliente/.venv/bin/rasa run \\  
    \--m models \\  
    \--enable-api \\  
    \--endpoints endpoints.yml \\  
    \--port 5005

StandardOutput=journal  
StandardError=journal  
Restart=always

\[Install\]  
WantedBy=multi-user.target
```
5. ### **Servicio de Acciones Personalizadas (/etc/systemd/system/rasa-actions.service)**

Este servicio ejecuta tu lógica personalizada de Python (actions.py) en el puerto 5055\.

```bash

\[Unit\]  
Description=Servidor de Acciones de Rasa  
After=network.target

\[Service\]  
User=demo  
Group=demo

WorkingDirectory=/home/demo/caso-servicio-cliente/

\# Comando de Inicio: Asegura que se ejecuta el 'rasa run actions'  
ExecStart=/home/demo/caso-servicio-cliente/.venv/bin/rasa run actions \\  
    \--actions actions

StandardOutput=journal  
StandardError=journal  
Restart=always

\[Install\]  
WantedBy=multi-user.target
```
6. ### **Habilitación e Inicio de los Servicios**

Una vez que hayas guardado los dos archivos .service (usando sudo), sigue estos pasos para activarlos:

1. **Recargar Systemd:** Informa al sistema sobre los nuevos archivos.  
   ```bash  
   sudo systemctl daemon-reload
```
   2. **Habilitar Servicios:** Configura los servicios para que inicien automáticamente después de un reinicio del servidor.  
      ```bash  
      sudo systemctl enable rasa-core.service  
      sudo systemctl enable rasa-actions.service
```
      3. **Iniciar Servicios:** Lanza los procesos de Rasa inmediatamente.  
         ```bash  
         sudo systemctl start rasa-core.service  
         sudo systemctl start rasa-actions.service
```
   7. ### **Verificación y Monitoreo (Debugging)** 

Para confirmar que los servicios están activos y para ver si hay errores (como fallas de conexión a PostgreSQL), usa estos comandos:

* **Verificar el estado:**  
  ```bash  
  sudo systemctl status rasa-core.service  
  sudo systemctl status rasa-actions.service
```
  (Busca la línea Active: active (running))  
* **Ver logs en tiempo real:** Utiliza journalctl para ver el *output* de Rasa.  
  ```bash  
  sudo journalctl \-u rasa-core.service \-f
```
8. ## **Despliegue de Ollama**

   1. ## **Requisitos Previos**

* Acceso con privilegios sudo a su VM.  
* El paquete curl (necesario para Ollama).  
* Python 3 y el gestor de paquetes pip (necesario para ChromaDB).

  2. ## **Instalación y Configuración de Ollama**

El *script* oficial de instalación de Ollama ya se encarga de crear el servicio systemd por usted.

3. ### **Instalar Ollama**

Ejecute el comando de instalación de Ollama. Si ya lo tenía instalado, este proceso confirmará la configuración del servicio.

```bash

curl \-fsSL https://ollama.com/install.sh | sh
```
4. ### **Verificar y Habilitar el Servicio de Ollama**

El *script* anterior crea automáticamente el archivo /etc/systemd/system/ollama.service, lo habilita y lo inicia. Verifique el estado:

```bash

sudo systemctl status ollama
```
**Salida esperada:** Verá Active: active (running).

5. ### **Configurar Ollama para que sea Accesible**

Por defecto, Ollama solo escucha en localhost (127.0.0.1), lo cual impide que ChromaDB o su aplicación web se conecten si se ejecutan como usuarios diferentes o en contenedores. Debe modificar el archivo de servicio para que escuche en todas las interfaces (0.0.0.0).

1. **Editar el Archivo de Servicio:**  
   ```bash  
   sudo systemctl edit ollama.service
```
   2. **Agregar Variables de Entorno:** Se abrirá un editor de texto (como nano o vim). Agregue las siguientes líneas bajo la sección \[Service\]:  
     ```  
      \[Service\]  
      Environment="OLLAMA\_HOST=0.0.0.0"  
      Environment="OLLAMA\_ORIGINS=\*"
```
      3. **Recargar y Reiniciar el Servicio:** Aplique los cambios.  
         ```bash  
         sudo systemctl daemon-reload  
         sudo systemctl restart ollama
```
         **Ollama ya está configurado para ejecutarse automáticamente como un servicio y es accesible en el puerto 11434 de su VM.**

9. ## **Instalación de ChromaDB**

Este manual le permite instalar y configurar ChromaDB como un servicio persistente que inicia automáticamente, utilizando la variable **$(whoami)** para insertar el nombre de usuario de forma segura.

1. ### **Requisitos**

* Tener **Python 3** y venv instalados.  
* Tener privilegios de **sudo**.

  2. ### **Preparación del Entorno Virtual y Directorios**

Ejecute este bloque de comandos para configurar el proyecto y las dependencias.

```bash

\# 1\. Crear directorios  
mkdir \-p $HOME/chroma\_server/data  
cd $HOME/chroma\_server

\# 2\. Crear e instalar ChromaDB en el VENV  
python3 \-m venv \~/chroma\_ev  
source \~/chroma\_env/bin/activate  
pip install chromadb  
deactivate

\# 3\. Asignar dueños y permisos  
USER\_NAME=$(whoami)  
sudo chown \-R $USER\_NAME:$USER\_NAME $HOME/chroma\_server  
sudo chown \-R $USER\_NAME:$USER\_NAME $HOME/chroma\_server/data

echo "Entorno virtual y permisos listos para $USER\_NAME."
```
3. ### **Creación y Activación del Servicio Systemd**

Este bloque obtiene la ruta del usuario y utiliza el comando echo con sudo tee para escribir el archivo de servicio de forma segura, evitando errores de permisos.

```bash

\# Obtiene el nombre de usuario y la ruta $HOME para el script  
USER\_NAME=$(whoami)  
USER\_HOME=$(eval echo \~$USER\_NAME) \# Obtiene la ruta /home/nombre\_usuario

\# 1\. Definir y escribir el archivo de servicio (chroma.service)  
sudo sh \-c "cat \> /etc/systemd/system/chroma.service" \<\<EOF  
\[Unit\]  
Description=ChromaDB Vector Store Server  
After=network.target

\[Service\]  
\# Usuario que ejecuta el servicio  
User=$USER\_NAME  
Group=$USER\_NAME

\# Directorio de trabajo y configuracion del entorno virtual  
WorkingDirectory=$USER\_HOME/chroma\_server/

\# Definicion del PATH completo al VENV (necesario para encontrar el binario 'chroma')  
Environment=PATH=$USER\_HOME/chroma\_env/bin:\\$PATH

\# Comando de Ejecucion: Inicia el servidor Chroma  
\# La ruta de persistencia se fija dentro de $HOME/chroma\_server/data  
ExecStart=$USER\_HOME/chroma\_env/bin/chroma run \--host 0.0.0.0 \--port 8000 \--path $USER\_HOME/chroma\_server/data

\# Opciones de reinicio  
Restart=always  
RestartSec=5

\[Install\]  
WantedBy=multi-user.target  
EOF

\# 2\. Recargar Systemd Daemon  
sudo systemctl daemon-reload

\# 3\. Habilitar e Iniciar el Servicio  
sudo systemctl enable chroma.service  
sudo systemctl start chroma.service

\# 4\. Verificar el Estado  
sudo systemctl status chroma.service
```
4. ### **Verificación Final**

Tras ejecutar el bloque anterior, la salida final de sudo systemctl status chroma.service debería ser **Active: active (running)** sin errores de usuario o de ruta.  
**ChromaDB ahora es un servicio persistente** que se inicia automáticamente al arrancar la VM y es accesible en http://\[su\_ip\]:8000. 

10. ## **Instalación Completa de Locust para Pruebas de Carga**

    1. ### **Preparación del Entorno Virtual y Script**

Este bloque crea la estructura de directorios y el entorno virtual (venv) donde residirá Locust y el script de prueba (ollama\_stress\_test.py).

```bash

\# 1\. Definir variables de usuario para la automatización  
USER\_NAME=$(whoami)  
USER\_HOME=$(eval echo \~$USER\_NAME)

\# 2\. Crear directorio dedicado para Locust y scripts  
mkdir \-p $USER\_HOME/locust\_scripts  
cd $USER\_HOME/locust\_scripts

\# 3\. Crear e instalar Locust en el VENV  
python3 \-m venv venv  
source venv/bin/activate  
pip install locust

\# 4\. Crear un script de prueba de ejemplo (ollama\_stress\_test.py)  
\#    (Reemplaza el contenido con tu código real de Locust)  
echo "  
from locust import HttpUser, task, between  
import json

MODELO\_A\_PROBAR \= 'llama3.2:1b'  
PROMPT\_BASE \= '¿Cómo funciona la base de datos vectorial?'  
MAX\_TOKENS \= 128

class OllamaInferenceUser(HttpUser):  
    wait\_time \= between(0.5, 2\)  
    host \= 'http://localhost:11434' \# Target: Ollama Service

    @task  
    def generate\_content(self):  
        payload \= {  
            'model': MODELO\_A\_PROBAR,  
            'prompt': PROMPT\_BASE,  
            'stream': False,  
            'options': {'num\_predict': MAX\_TOKENS}  
        }  
        self.client.post('/api/generate', json=payload, name='/api/generate LLM')  
" \> ollama\_stress\_test.py

\# 5\. Desactivar VENV y Asignar Dueños (Necesario para Systemd)  
deactivate  
sudo chown \-R $USER\_NAME:$USER\_NAME $USER\_HOME/locust\_scripts

echo "Entorno de Locust y script base listos en $USER\_HOME/locust\_scripts/."
```
2. ### **Creación y Activación del Servicio Systemd**

Este bloque usa un *template* para inyectar su usuario y rutas en el archivo de servicio locust.service, garantizando la ejecución persistente.

```bash

\# 1\. Definir y escribir el archivo de servicio (locust.service)  
sudo sh \-c "cat \> /etc/systemd/system/locust.service" \<\<EOF  
\[Unit\]  
Description=Locust Load Testing Service for Ollama  
After=network.target

\[Service\]  
\# Usuario que ejecuta el servicio  
User=$USER\_NAME  
Group=$USER\_NAME

\# Directorio de trabajo: donde se encuentra el script ollama\_stress\_test.py  
WorkingDirectory=$USER\_HOME/locust\_scripts/

\# Definicion del PATH completo al VENV para encontrar el binario 'locust'  
Environment=PATH=$USER\_HOME/locust\_scripts/venv/bin:\\$PATH

\# Comando de Ejecucion (Modo web):   
\# Ejecuta locust sin interfaz de terminal, escuchando solo en localhost (127.0.0.1) por seguridad  
ExecStart=$USER\_HOME/locust\_scripts/venv/bin/locust \-f ollama\_stress\_test.py \--web-host 127.0.0.1 \--web-port 8089

\# Opciones de reinicio  
Restart=always  
RestartSec=5

\[Install\]  
WantedBy=multi-user.target  
EOF

\# 2\. Recargar Systemd Daemon  
sudo systemctl daemon-reload

\# 3\. Habilitar e Iniciar el Servicio  
sudo systemctl enable locust.service  
sudo systemctl start locust.service

\# 4\. Verificar el Estado (Debe ser 'active (running)')  
echo "Estado del servicio de Locust:"  
sudo systemctl status locust.service

echo "Servicio Locust iniciado. Ahora está escuchando internamente en el puerto 8089."
```
3. ### **Configuración de Nginx como Reverse Proxy (Acceso Público)**

Para acceder al *dashboard* de Locust de forma externa a través del puerto 80, usaremos Nginx como *reverse proxy*.

4. ### **Instalar y Verificar Nginx**

```bash

\# Instalar Nginx (si no está instalado)  
sudo apt install nginx \-y  
sudo systemctl enable nginx  
sudo systemctl start nginx
```
5. ### **Crear el Archivo de Configuración del Proxy**

```bash

sudo nano /etc/nginx/sites-available/locust\_proxy
```
Pegue el siguiente contenido, reemplazando tu\_dominio.com por la IP o dominio de tu VM.

```

server {  
    listen 80;  
    listen \[::\]:80;  
    server\_name tu\_dominio.com tu\_ip\_publica; \# AJUSTAR ESTO

    \# Redirige el tráfico de /locust/ al puerto interno 8089 (Locust)  
    location /locust/ {  
        \# El proxy apunta a localhost ya que Locust ahora escucha solo internamente  
        proxy\_pass http://127.0.0.1:8089/;   
          
        \# Configuración estándar para un proxy web y manejo de WebSocket (necesario para Locust UI)  
        proxy\_set\_header Host $host;  
        proxy\_set\_header X-Real-IP $remote\_addr;  
        proxy\_set\_header X-Forwarded-For $proxy\_add\_x\_forwarded\_for;  
        proxy\_http\_version 1.1;  
        proxy\_set\_header Upgrade $http\_upgrade;  
        proxy\_set\_header Connection "upgrade";  
    }  
}
```
6. ### **Activar y Reiniciar Nginx**

Cree el archivo de configuración de Nginx y active el sitio.

1. Contenido del archivo `/etc/nginx/sites-available/locust_proxy`

```nginx
server {
   listen 80;
   listen [::]:80;
   server_name tu_dominio.com tu_ip_publica; # AJUSTAR ESTO

   # Redirige el tráfico de /locust/ al puerto interno 8089 (Locust)
   location /locust/ {
      # El proxy apunta a localhost ya que Locust ahora escucha solo internamente
      proxy_pass http://127.0.0.1:8089/;

      # Configuración estándar para un proxy web y manejo de WebSocket (necesario para Locust UI)
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection "upgrade";
   }
}
```

2. Comandos para activar y aplicar la configuración

```bash
# Guardar el archivo en /etc/nginx/sites-available/locust_proxy (usando sudo/nano o tee)

# Crear el enlace simbólico para activar la configuración
sudo ln -s /etc/nginx/sites-available/locust_proxy /etc/nginx/sites-enabled/

# Quitar la configuración default de Nginx (si existe)
sudo rm -f /etc/nginx/sites-enabled/default

# Verificar la sintaxis de Nginx
sudo nginx -t

# Reiniciar Nginx para aplicar los cambios
sudo systemctl restart nginx
sudo ln \-s /etc/nginx/sites-available/locust\_proxy /etc/nginx/sites-enabled/

\# Quitar la configuración default de Nginx (si existe)  
sudo rm \-f /etc/nginx/sites-enabled/default

\# Verificar la sintaxis de Nginx  
sudo nginx \-t

\# Reiniciar Nginx para aplicar los cambios  
sudo systemctl restart nginx
```

7. ### **Acceso Final**

Acceda al *dashboard* de pruebas de Locust a través de:  
**http://\[IP\_de\_tu\_VM\]/locust/** (o http://tu\_dominio.com/locust/)  
Desde allí, puede iniciar, monitorear y detener todas sus pruebas de carga.


## Instalación de Jupyter Notebooks para pruebas de funciones de DAGs
### Pasos
1. Dar permisos de ejecución al archivo init.sh y asignar el usuario actual como propietario
```
sudo chown $USER init.sh
sudo chmod u+x init.sh
```
2. Ejecutar el archivo
```
./init.sh
```
3. Crear entorno de python
```
python3 -m venv icc115-venv
```
4. Activar entorno de python
```
source icc115-venv/bin/activate
```
> **Nota**: Para desactivar el entorno.
```
deactivate
```
5. Instalar paquetes
```
pip install -r requirements.txt
```
6. Guardar paquetes instalados si se actualizan
```
pip freeze > requirements.txt
```
7. Inicializar servidor de Jupyter Notebook
```
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser
```
> Resultado
```
[I 2025-08-24 03:56:05.643 ServerApp] jupyter_lsp | extension was successfully linked.
[I 2025-08-24 03:56:05.647 ServerApp] jupyter_server_terminals | extension was successfully linked.
[I 2025-08-24 03:56:05.652 ServerApp] jupyterlab | extension was successfully linked.
[I 2025-08-24 03:56:05.654 ServerApp] Writing Jupyter server cookie secret to /home/mm18057/.local/share/jupyter/runtime/jupyter_cookie_secret
[I 2025-08-24 03:56:06.037 ServerApp] notebook_shim | extension was successfully linked.
[I 2025-08-24 03:56:06.065 ServerApp] notebook_shim | extension was successfully loaded.
[I 2025-08-24 03:56:06.067 ServerApp] jupyter_lsp | extension was successfully loaded.
[I 2025-08-24 03:56:06.068 ServerApp] jupyter_server_terminals | extension was successfully loaded.
[I 2025-08-24 03:56:06.070 LabApp] JupyterLab extension loaded from /home/mm18057/kubeflow-basic-setup/icc115/lib/python3.12/site-packages/jupyterlab
[I 2025-08-24 03:56:06.071 LabApp] JupyterLab application directory is /home/mm18057/kubeflow-basic-setup/icc115/share/jupyter/lab
[I 2025-08-24 03:56:06.071 LabApp] Extension Manager is 'pypi'.
[I 2025-08-24 03:56:06.133 ServerApp] jupyterlab | extension was successfully loaded.
[I 2025-08-24 03:56:06.133 ServerApp] Serving notebooks from local directory: /home/mm18057/kubeflow-basic-setup
[I 2025-08-24 03:56:06.134 ServerApp] Jupyter Server 2.17.0 is running at:
[I 2025-08-24 03:56:06.134 ServerApp] http://mm18057:8888/lab?token=48d55806869823c6c34105613916c70718abccdbc88d4024
[I 2025-08-24 03:56:06.134 ServerApp]     http://127.0.0.1:8888/lab?token=48d55806869823c6c34105613916c70718abccdbc88d4024
[I 2025-08-24 03:56:06.134 ServerApp] Use Control-C to stop this server and shut down all kernels (twice to skip confirmation).
[C 2025-08-24 03:56:06.137 ServerApp] 
    
    To access the server, open this file in a browser:
        file:///home/mm18057/.local/share/jupyter/runtime/jpserver-2898-open.html
    Or copy and paste one of these URLs:
        http://mm18057:8888/lab?token=48d55806869823c6c34105613916c70718abccdbc88d4024
        http://127.0.0.1:8888/lab?token=48d55806869823c6c34105613916c70718abccdbc88d4024
[I 2025-08-24 03:56:06.173 ServerApp] Skipped non-installed server(s): bash-language-server, dockerfile-language-server-nodejs, javascript-typescript-langserver, jedi-language-server, julia-language-server, pyright, python-language-server, python-lsp-server, r-languageserver, sql-language-server, texlab, typescript-language-server, unified-language-server, vscode-css-languageserver-bin, vscode-html-languageserver-bin, vscode-json-languageserver-bin, yaml-language-server
[W 2025-08-24 03:56:53.814 LabApp] Could not determine jupyterlab build status without nodejs

```
8. Copiar URL y abrirlo en un navegador en el host
```
http://HOST_IP_ADDRESS:8888/lab?token=ACCESS_TOKEN_GENERADO
```
## Jupyter Lab Workspace
![Página de Bienvenida de Jupyter Notebook](./imagenes/jupyter-lab-workspace.png "Página de Bienvenida de Jupyter Notebook")
1. Para crear un nuevo Jupiter Notebook
	- Opción 1: Dar clic en notebook
![_](./imagenes/jupyter-launcher.png "Opción 1: Crear notebook desde el launcher")

	- Opción 2: Dar clic en `File > New > Notebook`
![_](./imagenes/crear-nuevo-notebook.png "Opción 2: Crear notebook desde las opciones del menú")
### Elementos del workspace
![_](./imagenes/jupyter-lab-workspace-elementos.png)
1. Menú de opciones
2. Explorador de archivos
3. Opciones de explorador de archivos. 
	1. Nuevo Archivo
	2. Nueva Carpeta
	3. Cargar Archivo
	4. Recargar visualización de archivos
	5. Filtrar
4. Nombre de archivo. Clic derecho > `Rename Notebook...` para cambiar de nombre.
5. Controles del archivo
	1. Guardar
	2. Crear nueva celda
	3. Cortar celda
	4. Copiar celda
	5. Pegar celda
	6. Ejecutar la celda actual
	7. Detener ejecución
	8. Reiniciar
	9. Reiniciar y ejecutar todas las celdas
6. Selector de tipo de celda, puede ser Markdown (Lenguaje de Marcado), Code ó Raw
7. Vista de explorador de archivos
8. Celda de código
9. Celda de lenguaje de marcado
10. Número que indica el orden de ejecución de las celdas
11. Controles de celda
	1. Duplicar celda abajo
	2. Subir celda
	3. Bajar celda
	4. Insertar nueva celda arriba
	5. Insertar nueva celda abajo

## RAG API
1. Instalación
   ```
   python3 -m venv rasa_rag_api  
   source rasa_rag_api/bin/activate 
   pip install -r rasa_rag_requirements.txt
   ```
1. Ejecutar RAG API
   ```
   gunicorn -w 1 -b 0.0.0.0:8000 rasa_rag_api_server:app
   ```
2. Test RAG API
   ```
   curl -X POST http://localhost:8000/rag/query -H "Content-Type: application/json" -d '{"question": "¿Cómo puedo reiniciar mi router para arreglar un problema de internet?", "history": [] }'

   ```