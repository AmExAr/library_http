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
                cur.execute(f'CALL add_book(\'{author}\', \'{publisher}\', \'{creation_date}\', \'{name_book}\', \'{genre}\', \'{all_count}\')')
                #cur.callproc('add_book', [author, publisher, creation_date, name_book, genre, all_count])
                result = cur.statusmessage
                conn.commit()
                cur.close()
                return render_template('add_book.html', result=result)
        return render_template('add_book.html')
    else:
        return redirect(url_for('login'))

@app.route('/change_book', methods=['GET', 'POST'])
def change_book():
    if 'db_user' in session:
        if session.get('db_user') == 'admin':
            if request.method == 'POST':
                author = request.form['author']
                publisher = request.form['publisher']
                name_book = request.form['name_book']
                new_author = request.form['new_author']
                new_publisher = request.form['new_publisher']
                new_creation_date = request.form['new_creation_date']
                new_name_book = request.form['new_name_book']
                new_genre = request.form['new_genre']

                # SQL-запрос для обновления книги
                update_query = """
                    UPDATE books
                    SET author = %s, publisher = %s, creation_date = %s, name_book = %s, genre = %s
                    WHERE author = %s
                    AND publisher = %s
                    AND name_book = %s;
                """
                values = (new_author, new_publisher, new_creation_date, new_name_book, new_genre, author, publisher, name_book)
                
                db_user = session.get('db_user')
                db_pass = session.get('db_pass')
                try:
                    conn = psycopg2.connect(
                        host="localhost",
                        database="library_db",
                        user=db_user,
                        password=db_pass
                    )
                    cur = conn.cursor()
                    cur.execute(update_query, values)
                    conn.commit()
                    cur.close()
                    result = "Книга успешно обновлена."
                except (Exception, psycopg2.Error) as error:
                    result = f"Ошибка при обновлении книги: {error}"        
                return render_template('change_book.html', result=result)
            return render_template('change_book.html')
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/delete_book', methods=['GET', 'POST'])
def delete_book():
    if 'db_user' in session:
        if session.get('db_user') == 'admin':
            if request.method == 'POST':
                author = request.form['author']
                publisher = request.form['publisher']
                name_book = request.form['name_book']

                query1 = """DELETE FROM book_info WHERE id_number = (SELECT id_number FROM books WHERE author = %s AND publisher = %s AND name_book = %s);"""
                query2 = """DELETE FROM books WHERE id_number = (SELECT id_number FROM books WHERE author = %s AND publisher = %s AND name_book = %s);"""

                values = (author, publisher, name_book)

                db_user = session.get('db_user')
                db_pass = session.get('db_pass')
                try:
                    conn = psycopg2.connect(
                        host="localhost",
                        database="library_db",
                        user=db_user,
                        password=db_pass
                    )
                    cur = conn.cursor()
                    cur.execute(query1, (author, publisher, name_book))
                    cur.execute(query2, (author, publisher, name_book))
                    conn.commit()
                    cur.close()
                    result = "Книга успешно удалена."
                except (Exception, psycopg2.Error) as error:
                    result = f"Ошибка при удалении книги: {error}"        
                return render_template('delete_book.html', result=result)
            return render_template('delete_book.html')
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/list_books', methods=['GET', 'POST'])
def list_books():
    if 'db_user' in session:
        if request.method == 'POST':
            student_name = request.form['student_name']

            query = """
                SELECT author, name_book
                FROM books
                WHERE id_number = (
                    SELECT id_number
                    FROM book_info
                    WHERE BUID = (
                        SELECT BUID
                        FROM reserved_books
                        WHERE UUID_ = (
                            SELECT UUID_
                            FROM students_info
                            WHERE FIO = %s
                        )
                    )
                );
            """
            
            db_user = session.get('db_user')
            db_pass = session.get('db_pass')
            try:
                conn = psycopg2.connect(
                    host="localhost",
                    database="library_db",
                    user=db_user,
                    password=db_pass
                )
                cur = conn.cursor()
                cur.execute(query, (student_name,))
                result = cur.fetchall()
                column_names = [desc[0] for desc in cur.description]
                conn.commit()
                cur.close()
                
                return render_template('book_list.html', result=result, column_names=column_names)
            except (Exception, psycopg2.Error) as error:
                print("Ошибка при получении содержимого представления:", error)
                return """<h1>Ошибка вывода списка: </h1>
                <p>""" + str(error) + """ </p><br><br><a href="/dashboard">Назад</a>"""
        return render_template('book_list.html')
    else:
        return redirect(url_for('login'))

@app.route('/give_book', methods=['GET', 'POST'])
def give_book():
    if 'db_user' in session:
        if request.method == 'POST':
            author = request.form['author']
            publisher = request.form['publisher']
            book_name = request.form['book_name']
            student_name = request.form['student_name']
            start_date = request.form['start_date']
            end_date = request.form['end_date']

            # SQL-запрос для обновления книги
            query = """
                INSERT INTO reserved_books (BUID, UUID_, first_day, last_day)
                VALUES (
                    (SELECT BUID FROM book_info WHERE status is TRUE AND id_number = (SELECT id_number FROM books
                    WHERE author = %s
                    AND publisher = %s
                    AND name_book = %s) LIMIT 1),
                    (SELECT UUID_ FROM students_info WHERE FIO = %s),
                    %s, %s
                );
                UPDATE book_info SET status = FALSE
                WHERE BUID = (
                    SELECT BUID FROM reserved_books 
                    WHERE UUID_ = (
                        SELECT UUID_ FROM students_info 
                        WHERE FIO = %s) LIMIT 1);
            """
            values = (author, publisher, book_name, student_name, start_date, end_date, student_name)
            
            db_user = session.get('db_user')
            db_pass = session.get('db_pass')
            try:
                conn = psycopg2.connect(
                    host="localhost",
                    database="library_db",
                    user=db_user,
                    password=db_pass
                )
                cur = conn.cursor()
                cur.execute(query, values)
                conn.commit()
                cur.close()
                result = "Книга успешно выдана."
            except (Exception, psycopg2.Error) as error:
                result = f"Ошибка при выдачи книги: {error}"        
            return render_template('give_book.html', result=result)
        return render_template('give_book.html')
    else:
        return redirect(url_for('login'))

@app.route('/get_book', methods=['GET', 'POST']) 
def get_book():
    if 'db_user' in session:
        if request.method == 'POST':
            book_name = request.form['book_name']
            book_author = request.form['book_author']
            creation_date = request.form['creation_date']
            student_name = request.form['student_name']

            # SQL-запрос для обновления книги
            query = """
                UPDATE book_info bi
                SET status = FALSE
                FROM books b
                JOIN reserved_books rb ON b.id_number = bi.id_number
                WHERE b.name_book = %s
                    AND b.author = %s
                    AND b.creation_date = %s
                    AND rb.UUID_ = (
                        SELECT UUID_
                        FROM students_info
                        WHERE FIO = %s
                );
            """
            values = (book_name, book_author, creation_date, student_name)
            
            db_user = session.get('db_user')
            db_pass = session.get('db_pass')
            try:
                conn = psycopg2.connect(
                    host="localhost",
                    database="library_db",
                    user=db_user,
                    password=db_pass
                )
                cur = conn.cursor()
                cur.execute(query, values)
                conn.commit()
                cur.close()
                result = "Книга успешно сдана."
            except (Exception, psycopg2.Error) as error:
                result = f"Ошибка при сдачи книги: {error}"        
            return render_template('get_book.html', result=result)
        return render_template('get_book.html')
    else:
        return redirect(url_for('login'))

@app.route('/update_class_name', methods=['GET', 'POST'])
def update_class_name():
    if 'db_user' in session:
        if session.get('db_user') == 'admin':
            if request.method == 'POST':
                old_class_name = request.form['old_class_name']
                new_class_name = request.form['new_class_name']
                query = "UPDATE class_number SET class_name = %s WHERE class_name = %s"
                
                db_user = session.get('db_user')
                db_pass = session.get('db_pass')
                
                try:
                    conn = psycopg2.connect(
                        host="localhost",
                        database="library_db",
                        user=db_user,
                        password=db_pass
                    )
                    cur = conn.cursor()
                    cur.execute(query, (new_class_name, old_class_name))
                    conn.commit()
                    cur.close()
                    result = f"Название класса '{old_class_name}' было изменено на '{new_class_name}'"
                except (Exception, psycopg2.Error) as error:
                    result = f"Ошибка при изменении названия: {error}"
                return render_template('update_class_name.html', result=result)       
            return render_template('update_class_name.html')
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/new_student', methods=['GET', 'POST'])
def new_student():
    if 'db_user' in session:
        if session.get('db_user') == 'admin':
            if request.method == 'POST':
                fio = request.form['fio']
                email = request.form['email']
                tel = request.form['tel']
                cname = request.form['cname']
                
                db_user = session.get('db_user')
                db_pass = session.get('db_pass')
                
                try:
                    conn = psycopg2.connect(
                        host="localhost",
                        database="library_db",
                        user=db_user,
                        password=db_pass
                    )
                    cur = conn.cursor()
                    cur.execute(f'SELECT create_student(\'{fio}\', \'{email}\', \'{tel}\', \'{cname}\');')
                    conn.commit()
                    cur.close()
                    result = f"Школьник успешно добавлен"
                except (Exception, psycopg2.Error) as error:
                    result = f"Ошибка при добавлении нового школьник: {error}"
                return render_template('new_student.html', result=result)
                
            return render_template('new_student.html')
        else:
            return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/edit_student', methods=['GET', 'POST'])
def edit_student():
    if 'db_user' in session:
        if session.get('db_user') == 'admin':
            if request.method == 'POST':
                fio = request.form['fio']
                email = request.form['email']
                tel = request.form['tel']
                old_email = request.form['old_email']
                query = "UPDATE students_info SET FIO = %s, email = %s, tel = %s WHERE email = %s;"
                
                db_user = session.get('db_user')
                db_pass = session.get('db_pass')
                
                try:
                    conn = psycopg2.connect(
                        host="localhost",
                        database="library_db",
                        user=db_user,
                        password=db_pass
                    )
                    cur = conn.cursor()
                    cur.execute(query, (fio, email, tel, old_email))
                    conn.commit()
                    cur.close()
                    result = f"Информация о школьнике успешно обновлена"
                except (Exception, psycopg2.Error) as error:
                    result = f"Ошибка при изменении информации: {error}"
                return render_template('edit_student.html', result=result)
                
            return render_template('edit_student.html')
        else:
            return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/occupied_books_view', methods=['GET'])
def occupied_books_view():
    if 'db_user' in session:
        db_user = session.get('db_user')
        db_pass = session.get('db_pass')
        
        try:
            conn = psycopg2.connect(
                host="localhost",
                database="library_db",
                user=db_user,
                password=db_pass
            )
            cur = conn.cursor()
            cur.execute('SELECT * FROM occupied_books_view;')
            view_content = cur.fetchall()
            conn.commit()
            cur.close()
            column_names = [desc[0] for desc in cur.description]
            return render_template('view_content.html', view_content=view_content, column_names=column_names)
        except (Exception, psycopg2.Error) as error:
            print("Ошибка при получении содержимого представления:", error)
            return str(error), 500
    else:
        return redirect(url_for('login'))

# Маршрут для страницы с формой запроса к базе данных
@app.route('/query', methods=['GET', 'POST'])
def query():
    if 'db_user' in session:
        if session.get('db_user') == 'admin':
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
            return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

# Обработчик для выхода из системы
@app.route('/logout')
def logout():
    session.pop('db_user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port="8080", debug=True)