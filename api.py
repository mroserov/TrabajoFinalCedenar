import os
from flask import Flask, jsonify, render_template, flash, request, redirect, url_for, send_from_directory
from flask_swagger import swagger
from werkzeug.utils import secure_filename
from joblib import load
from sqlalchemy import create_engine
import pandas as pd
import xgboost
import sqlite3

from db import init_db_command
from user import User
from words import get_frecuency_words, get_n_grama

import json
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests

FLASK_APP = os.environ.get("USERS","webapp")

# Configuration
UPLOAD_FOLDER = 'uploads'
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH',200)) * 1024 * 1024 # 100MB

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", '595522474871-j8tiio3u9791jkdod61ovfto96sv40ol.apps.googleusercontent.com')
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", 'UZ6HVz-lHiEN2BNWmnqZvYLu')
ALLOWED_EXTENSIONS = os.environ.get('ALLOWED_EXTENSIONS','dat,csv').split(',')
POSTGRES_URI = os.environ.get('POSTGRES_URI', 'postgresql+psycopg2://postgres:cedenarfinal@186.85.149.39:5432/cedenar')
app.secret_key = os.environ.get("GOOGLE_CLIENT_SECRET", 'UZ6HVz-lHiEN2BNWmnqZvYLu') or os.urandom(24)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# Naive database setup
#try:
    #init_db_command()
#except sqlite3.OperationalError as ex:
    # Assume it's already been created
#    pass

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

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
@login_required
def load_model(nombre_archivo):
    """
    Cargar Modelo
    swagger_from_file: docs/modelo.yml    
    """
    response = {}
    try:
        #query = f"select id_bitacora, tipo, responsable,nivel,zona,subestacion,circuito,transformador, elemento_corte, tipo_apertura, motivo_apertura, afectacion, carga_padre, acumulado_fallas from ds_bitacoras where clase IS NOT null order by id"
        query = "select id_consignacion, responsable,supervisor,zona,subestacion,circuito,transformador, carga, prioridad, carga_afectada ,acumulado_fallas from ds_consignaciones where clase3 IS NOT null order by id"
        # load model from file    
        model = None
        if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)):
            model = load(os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo))
            #print("Loaded model from: pima.joblib.dat")    
            # get data of DB
            prod= create_engine(POSTGRES_URI)
            
            transformador = request.args.get('transformador','')
            if transformador:
                df_cons = pd.read_sql_query(f"select id_consignacion from ds_consignaciones where clase3 IS NOT null and transformador like '{transformador}' order by acumulado_fallas desc limit(1)", prod)
                if len(df_cons.id_consignacion) == 0:
                    return jsonify({'error':'El transformador no tiene consiganciones para evaluar'})
                id_consignacion = int(df_cons.id_consignacion[0])
            else:
                id_consignacion = request.args.get('id_consignacion',-1)
            df = pd.read_sql_query(query, prod)
            response['data']=df[df.id_consignacion == int(id_consignacion)].to_dict('records')
            if len(response['data']) == 0:
                response['error'] = 'Consignacion no existe'
            else:
                df_transformado = pd.read_pickle(os.path.join(app.config['UPLOAD_FOLDER'],'df_texto_transformado.dat'))
                df_dummie=pd.get_dummies(df,drop_first=True)

                df_transformado['id_consignacion']=df_transformado.index
                df_dummie= pd.merge(df_transformado, df_dummie, on='id_consignacion')
                
                df_dummie=df_dummie[df_dummie.id_consignacion == int(id_consignacion)]
                #borro id_consignacion
                X1 = df_dummie.drop(labels=['id_consignacion'],axis=1)
                res = model.predict_proba(X1)
                response['model'] = []
                response['model'].append(dict(clase=1, valor=str(res[0][0])))
                response['model'].append(dict(clase=2, valor=str(res[0][1])))
                response['model'].append(dict(clase=3, valor=str(res[0][2])))
        else:
            response['error'] = 'Archivo no existe'
        
    except Exception as ex:
        response['error'] = str(ex)
    
    return jsonify(response)

@app.route('/words/frecuencia', methods=['GET'])
def frecuency():
    response = {}
    response['error'] = []
    try:
        file_name = 'df_texto.dat' if request.args.get('tipo') == 'texto' else 'df_texto_limpiar.dat'
        count = int(request.args.get('count') or 20)
        numero = int(request.args.get('numero') or 1)
        if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], file_name)):            
            df_texto = pd.read_pickle(os.path.join(app.config['UPLOAD_FOLDER'], file_name))                        
            response = get_frecuency_words(count, df_texto) if numero == 1 else get_n_grama(numero, count, df_texto)
        else:
            response['error'] = 'Archivo no existe'
    except Exception as ex:
        response['error'].append(str(ex))

    return jsonify(response)

@app.route('/transformador', methods=['GET'])
def transformador():
    response = {}
    response['error'] = []
    try:
        file_name = 'df_transformador.dat'
        search = request.args.get('search')
        if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], file_name)):            
            df_trans = pd.read_pickle(os.path.join(app.config['UPLOAD_FOLDER'], file_name))                        
            res = df_trans.transformador[df_trans.transformador.str.contains(search)][:100]
            response = res.to_json(orient='values')
            return response
        else:
            response['error'] = 'Archivo no existe'
    except Exception as ex:
        response['error'].append(str(ex))

    return jsonify(response)

@app.route('/archivo', methods=['POST'])
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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

@app.route('/web')
def web(name=None):
    if current_user.is_authenticated:
        return render_template('web.html', data=current_user.email)
    else:
        return redirect(url_for("login"))

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/auth",
        scope=["openid", "email", "profile"],
        state=request.args.get('url')
    )
    return render_template('login.html', data={'url':request_uri, 'msg':request.args.get('msg')})

@app.route("/login/auth")
def callback():
    try:
        # Get authorization code Google sent back to you
        code = request.args.get("code")

        google_provider_cfg = get_google_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]

        # Prepare and send a request to get tokens! Yay tokens!
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=request.base_url,
            code=code
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        # Parse the tokens!
        client.parse_request_body_response(json.dumps(token_response.json()))

        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        if userinfo_response.json().get("email_verified"):
            unique_id = userinfo_response.json()["sub"]
            users_email = userinfo_response.json()["email"]
            picture = userinfo_response.json()["picture"]
            users_name = userinfo_response.json()["given_name"]
        else:
            return "User email not available or not verified by Google.", 400

        # Create a user in your db with the information provided
        # by Google
        user = User(
            id_=unique_id, name=users_name, email=users_email, profile_pic=picture
        )

        # Doesn't exist? Add it to the database.
        if not User.valid(users_email):
            return "Usuario no permitido"

        # Doesn't exist? Add it to the database.
        if not User.get(unique_id):
            User.create(unique_id, users_name, users_email, picture)

        # Begin user session by logging the user in
        login_user(user)

        # Send user back to homepage
        return redirect(url_for("web"))
    
    except Exception as ex:
        return "Error: " + str(ex)

@app.route('/')
def hello(name=None):
    if current_user.is_authenticated:
        return render_template('index.html')
    else:
        return redirect(url_for("login",msg="No Authorizado por favor ingrese"))    

@app.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for("web"))    

@login_manager.unauthorized_handler
def unauthorized():
    # do stuff
    return redirect(url_for("login",msg="No Authorizado por favor ingrese"))

def response_upload(message):
    return f'<h1>{message}</h1><br><form action="/archivo"><button type="submit">Regresar</button></form>'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    app.run(ssl_context='adhoc')