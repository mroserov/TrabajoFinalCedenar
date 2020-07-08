# TrabajoFinalCedenar
Trabajo De Grado

[Url API de Cedenar](https://trabajofinalcedenar.herokuapp.com/)

## Presentación
Abre el archivo `presentacion.ipynb` que contiene la presentacion realizada en jupyter notebook con la biblioteca RISE y que corre en binder 

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/mroserov/TrabajoFinalCedenar/master?filepath=presentacion.ipynb)

## Configurar env

Create env
virtualenv cedenar

Activar env
```bash
source cedenar/bin/activate
```

Install requirements
```bash
pip install -r requirements.txt
```

Update requirements.txt
```bash
pip freeze > requirements.txt
```

Run App localhost on http://127.0.0.1:5000/ 
```bash
python api.py
```

## Publicar en heroku

Para publicar automáticamente en heroku se debe hacer push en la rama master de GitHub
```bash
$ git add .
# Agrega el archivo a tu repositorio local y lo presenta para la confirmación. Para deshacer un archivo, usa 'git reset HEAD YOUR-FILE'.
$ git commit -m "Agregar archivo"
# Para eliminar esta confirmación y modificar el archivo, usa 'git reset --soft HEAD~1' y confirma y agrega nuevamente el archivo.
git push  origin master
```

Para configurar git con la cuenta de github
