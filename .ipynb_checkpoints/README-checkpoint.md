# Kubeflow

Prueba de concepto de Kubeflow Stack, que incluye Kubeflow Pipelines + MLflow + TensorFlow Serving. Instalación mínima para aprendizaje de Kubeflow usando single-node Kubernetes cluster con Minikube.

## Caracteristicas VM

| Componente       | Especificación                                                                 |
|-----------------|-------------------------------------------------------------------------------|
| **Sistema Operativo** | Ubuntu Server 24.04.3 LTS                                                    |
| **Imagen ISO**   | `ubuntu-24.04.3-live-server-amd64.iso`                                        |
| **Enlace de Descarga** | [Ubuntu 24.04.3 Server ISO](https://ubuntu.com/download/server/thank-you?version=24.04.3&architecture=amd64&lts=true) |
| **Virtualización** | QEMU / KVM                                                                 |
| **vCPUs**       | 2                                                                             |
| **Memoria**      | 4096 MiB (4 GB)                                                               |
| **Tamaño de Disco**   | 25 GB                                                                         |

## Instalación
### Pasos
1. Dar permisos de ejecución al archivo init.sh y asignar el usuario actual como propietario
```
sudo chown $USER init.sh
sudo u+x init.sh
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