from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import os
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)

# Маршрут для главной страницы с формой авторизации
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        session['db_user'] = username
        session['db_pass'] = password
        
        try:
            # Попытка подключения к базе данных с учетными данными пользователя
            
            
            conn = psycopg2.connect(
                host="localhost",
                database="library_db",
                user=username,
                password=password
            )
            cur = conn.cursor()
            return redirect(url_for('dashboard'))
        except psycopg2.Error as e:
            error = "Неверное имя пользователя или пароль"
            return render_template('./login.html', error=error)

    return render_template('login.html')

# Маршрут для страницы с выбором функционала базы данных
@app.route('/dashboard')
def dashboard():
    if 'db_user' in session:
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login'))
    
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'db_user' in session:
        if request.method == 'POST':
            author = request.form['author'].strip()
            publisher = request.form['publisher'].strip()
            creation_date = request.form['creation_date']
            name_book = request.form['name_book'].strip()
            genre = request.form['genre'].strip()
            all_count = request.form['all_count']

            if not all([author, publisher, creation_date, name_book, genre, all_count]):
                error = "Пожалуйста, заполните все поля."
                return render_template('add_book.html', error=error, author=author, publisher=publisher,
                                    creation_date=creation_date, name_book=name_book, genre=genre, all_count=all_count)
            db_user = session.get('db_user')
            db_pass = session.get('db_pass')
                
            if db_user and db_pass:
                conn = psycopg2.connect(
                    host="localhost",
                    database="library_db",
                    user=db_user,
                    password=db_pass
                )
                cur = conn.cursor()
                cur.callproc('add_book', [author, publisher, creation_date, name_book, genre, all_count])
                column_names = [desc[0] for desc in cur.description]
                result = cur.statusmessage
                conn.commit()
                cur.close()
                return render_template('add_book.html', result=result)
        return render_template('add_book.html')
    else:
        return redirect(url_for('login'))
        

# Маршрут для страницы с формой запроса к базе данных
@app.route('/query', methods=['GET', 'POST'])
def query():
    if 'db_user' in session:
        if request.method == 'POST':
            db_user = session.get('db_user')
            db_pass = session.get('db_pass')
            
            if db_user and db_pass:
                try:
                    query = request.form['query']
                    
                    # Выполнение запроса к базе данных
                    conn = psycopg2.connect(
                        host="localhost",
                        database="library_db",
                        user=db_user,
                        password=db_pass
                    )
                    cur = conn.cursor()
                    cur.execute(query)
                    column_names = [desc[0] for desc in cur.description]
                    conn.commit()
                    result = cur.fetchall()
                    return render_template('query.html', result=[dict(zip(column_names, row)) for row in result])
                except (Exception, psycopg2.Error) as error:
                    print("Ошибка при выполнении запроса SQL", error)
                    return str(error), 500
        else:
            return render_template('query.html')
    else:
        return redirect(url_for('login'))

# Обработчик для выхода из системы
@app.route('/logout')
def logout():
    session.pop('db_user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port="8080", debug=True)