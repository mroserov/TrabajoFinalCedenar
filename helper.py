from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score, precision_score, balanced_accuracy_score
from sklearn.model_selection import train_test_split

ALLOWED_EXTENSIONS = os.environ['ALLOWED_EXTENSIONS'].split(',') if 'ALLOWED_EXTENSIONS' in os.environ else ['dat','csv']

def eval_modelo(X=[], Y=[], modelo, accuracy=balanced_accuracy_score):
    X_train, X_test, y_train, y_test = train_test_split(X, 
                                                        Y, 
                                                        test_size = 0.3, 
                                                        random_state = 2)
    #Predice prueba
    y_pred_test = modelo.predict(X_test)
    #predice train
    y_pred_train = modelo.predict(X_train)

    #n_samples / (n_classes * np.bincount(y))
    print('Test:',confusion_matrix(y_test, y_pred_test))
    print('Train:',confusion_matrix(y_train, y_pred_train))
    
    if accuracy == accuracy_score:
        str_accuracy = 'accuracy_score'
    elif accuracy == balanced_accuracy_score:
        str_accuracy = 'balanced_accuracy_score'
    else:
        str_accuracy = ''
    
    return { f'{str_accuracy} test:', accuracy(y_test, y_pred_test),
             f'{str_accuracy} train:', accuracy(y_train, y_pred_train)}


def response_upload(message):
    return f'<h1>{message}</h1><br><form action="/upload"><button type="submit">Regresar</button></form>'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS