from flask import Flask
from flask import render_template
import dmslibs as dl
import os
import comum


if dl.IN_HASSIO():
    WEB_SERVER = True
    template_dir = os.path.abspath(comum.PATH_TEMPLATE_HAS)
else:
    template_dir = os.path.abspath(comum.PATH_TEMPLATE)



app = Flask(__name__, template_folder=template_dir)

@app.route('/')
def hello():

    resposta = dl.loadJsonFile(comum.FILE_COMM, True)

    html = render_template('index.html', title='Home', user='usuário', itens=resposta)

    return html

@app.route('/xx')
def xx():

    html = '<HR>TESTE<HR>'

    return html



@app.route('/index')
def index():

    resposta = dl.loadJsonFile(comum.FILE_COMM)

    user = {'username': 'Daniel'}
    user = {'username': resposta} 
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index copy.html',title='Home', user=user, posts=posts)


if __name__ == "__main__":
    #app.run()
    app.run(debug=True, host="0.0.0.0")

