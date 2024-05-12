from app import app

@app.route('/')
@app.route('/index')
def index():
    user = {'amogus' : 'sussy baka'}
    return '''
<html>
    <head>
        <title>Home Page - Microblog</title>
    </head>
    <body>
        <h1>Hello, ''' + user['amogus'] + '''!</h1>
    </body>
</html>
'''