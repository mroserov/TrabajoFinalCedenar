import os
from flask import Flask, jsonify, render_template, flash, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = os.environ['ALLOWED_EXTENSIONS'].split(',') if 'ALLOWED_EXTENSIONS' in os.environ else ['dat','csv']

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024 # 100MB


@app.route('/data')
def hello_world():
    """Example Api
    """
    return jsonify({'data':[1,2,3,4,5,6,7,8,9,10]})

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
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
    return f'''
    <!doctype html>
    <title>Cargar archivo</title>
    <h1>Cargar archivo</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file value=Archivo>
      <input type=submit value=Cargar>
    </form>
    '''
@app.route('/uploads/<path:filename>')
def download_file(filename):
    if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    else:
        return response_upload(f'El archivo <i>{filename}</i> no existe, <br>lista de archivos: <i>{os.listdir(UPLOAD_FOLDER)}</i>')

def response_upload(message):
    return f'<h1>{message}</h1><br><form action="/upload"><button type="submit">Regresar</button></form>'

@app.route('/')
def hello(name=None):
    return render_template('index.html')

if __name__ == '__main__':
    app.run()