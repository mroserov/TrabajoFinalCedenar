import os
from flask import Flask, jsonify, render_template, flash, request, redirect, url_for, send_from_directory
from flask_swagger import swagger
from werkzeug.utils import secure_filename
from joblib import load
from sqlalchemy import create_engine
import pandas as pd
import xgboost

#from .helper import eval_modelo, response_upload, allowed_file, ALLOWED_EXTENSIONS

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = os.environ.get('ALLOWED_EXTENSIONS','dat,csv').split(',')
POSTGRES_URI = os.environ.get('POSTGRES_URI', 'postgresql+psycopg2://')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH',200)) * 1024 * 1024 # 100MB

@app.route('/doc')
def doc():
    """
    Documentación de Swagger
    """
    swagger_app = swagger(app, from_file_keyword='swagger_from_file')
    swagger_app['info']['title'] = 'CEDENAR Api'
    swagger_app['info']['description'] = 'Api para CEDENAR S.A. E.S.P.'
    swagger_app['info']['version'] = '1.0.0'    
    swagger_app['schemes'] = [os.environ.get('SCHEMES','http')]
    
    return jsonify(swagger_app)

@app.route('/modelo/<path:nombre_archivo>')
def load_model(nombre_archivo):
    """
    Cargar Modelo
    swagger_from_file: docs/modelo.yml    
    """
    response = {}
    try:
        # load model from file    
        model = None
        if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)):
            model = load(os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo))
            #print("Loaded model from: pima.joblib.dat")    
            # get data of DB
            prod= create_engine(POSTGRES_URI)
            id_bitacora = request.args.get('id_bitacora',-1)
            df = pd.read_sql_query(f"select tipo, responsable,nivel,zona,subestacion,circuito,transformador, elemento_corte, tipo_apertura, motivo_apertura, afectacion, carga_padre, acumulado_fallas,clase as clase from ds_bitacoras where clase IS NOT null and id_bitacora = {id_bitacora} order by id", prod)
            response = dict(model=str(model), data=df.to_dict())
        else:
            response['error'] = 'Archivo no existe'
        
    except Exception as ex:
        response['error'] = str(ex)
    
    return response

@app.route('/archivo', methods=['POST'])
def upload_file():
    """
    Subir Archivo
    swagger_from_file: docs/upload.yml
    """
    try:
        # check if the post request has the file part
        if 'file' not in request.files:
            return response_upload('No existe el archivo')
            #return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return response_upload('Seleccione un archivo')
            #return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            if not os.path.isdir(app.config['UPLOAD_FOLDER']):
                return response_upload(f'Directorio no existe')
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return response_upload(f'Archivo <i>{filename}</i> cargado exitosamente')
        else:
            return response_upload(f'Archivo <i>{file.filename}</i> no permitido<br>formatos permitidos {str(ALLOWED_EXTENSIONS)}')
    except Exception as ex:
        return response_upload(str(ex))

@app.route('/archivo', methods=['GET'])
def upload_file_get():
    """
    Subir Archivo
    """
    return f'''
    <!doctype html>
    <title>Cargar archivo</title>
    <h1>Cargar archivo</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file value=Archivo>
      <input type=submit value=Cargar>
    </form>
    '''

@app.route('/archivo/<path:nombre_archivo>')
def download_file(nombre_archivo):
    """
    Descargar Archivo
    ---    
    tags:
        - Archivos
    parameters:
      - in: path
        name: nombre_archivo
        required: true
        type: string
    responses:
        200:
            description: Archivo
    """
    if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)):
        return send_from_directory(app.config['UPLOAD_FOLDER'], nombre_archivo, as_attachment=True)
    else:
        return response_upload(f'El archivo <i>{nombre_archivo}</i> no existe, <br>lista de archivos: <i>{os.listdir(UPLOAD_FOLDER)}</i>')

@app.route('/archivos')
def get_files():
    """
    Listar archivos
    ---
    tags:
        - Archivos        
    responses:
        200:
            description: Archivo
    """
    response = []
    for file in os.listdir(UPLOAD_FOLDER):
        info = os.stat(os.path.join(app.config['UPLOAD_FOLDER'],file))
        response.append(dict(archivo=file, tamano="{:.2f} MB".format(info.st_size/1024/1024)))
    return jsonify(response)

@app.route('/archivo/<path:nombre_archivo>', methods=['DELETE'])
def delete_files(nombre_archivo):
    """
    Borrar archivo
    ---
    tags:
        - Archivos   
    parameters:
      - in: path  
        name: nombre_archivo
        required: true
        type: string     
    responses:
        200:
            description: Archivo borrado
    """
    if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo))
    else:
        return response_upload(f'El archivo <i>{nombre_archivo}</i> no existe, <br>lista de archivos: <i>{os.listdir(UPLOAD_FOLDER)}</i>')
    return "Archivo borrado"

@app.route('/')
def hello(name=None):
    return render_template('index.html')


def response_upload(message):
    return f'<h1>{message}</h1><br><form action="/archivo"><button type="submit">Regresar</button></form>'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


if __name__ == '__main__':
    app.run()