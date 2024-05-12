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

        try:
            # Попытка подключения к базе данных с учетными данными пользователя
            
            
            conn = psycopg2.connect(
                host="localhost",
                database="library_db",
                user=username,
                password=password
            )
            cur = conn.cursor()
            session['username'] = username
            session['password'] = password
            return redirect(url_for('dashboard'))
        except psycopg2.Error as e:
            error = "Неверное имя пользователя или пароль"
            return render_template('./login.html', error=error)

    return render_template('login.html')

# Маршрут для страницы с выбором функционала базы данных
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login'))

# Маршрут для страницы с формой запроса к базе данных
@app.route('/query', methods=['GET', 'POST'])
def query():
    if 'username' in session:
        if request.method == 'POST':
            query = request.form['query']

            # Выполнение запроса к базе данных
            conn = psycopg2.connect(
                host="localhost",
                database="library_db",
                user=session.get('username'),
                password=session.get('password')
            )
            cur = conn.cursor()
            cur.execute(query)
            conn.commit()
            result = cur.fetchall()

            return render_template('query.html', result=result)
        else:
            return render_template('query.html')
    else:
        return redirect(url_for('login'))

# Обработчик для выхода из системы
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)