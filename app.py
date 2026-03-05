from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector, base64, os
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = 'local_secret_key'


DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "railinedb-haru-270f.k.aivencloud.com"),
    "user": os.environ.get("DB_USER", "avnadmin"),
    "password": os.environ.get("DB_PASSWORD", "AVNS_MuzXZBW8I2iVk46Xknn"),
    "database": os.environ.get("DB_NAME", "defaultdb"),
    "port": int(os.environ.get("DB_PORT", 22306)),
    "charset": "utf8mb4",
    "ssl_disabled": False  # AivenはSSL接続が必須のため False に設定
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.route("/")
def home():
    return render_template("login.html", data = None) 

@app.route("/login", methods=["GET","POST"])
def login():
    
    conn = None
    cursor = None

    try:
        mail =  request.form.get("mail","")
        password = request.form.get("password","")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        sql = ('SELECT id, mail, password FROM users WHERE mail=%s')
        cursor.execute(sql,(mail,))
        exist = cursor.fetchone()

        if not exist or not check_password_hash(exist['password'], password):
            data = "メールアドレスまたはパスワードが正しくありません。"
        
        else:
            session.clear()
            session['user_id'] = exist['id']
            return redirect(url_for("timeline"))

    except Exception as e:
            print(f"エラーが発生しました: {e}")
            data = "ログイン処理中にエラーが発生しました。"
    finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template("login.html", data=data)

@app.route("/new")
def new():
    return render_template("new.html", data=None)

@app.route("/register", methods=["POST"])
def register():

    conn = None
    cursor = None

    try:
        name = request.form.get("name","")
        username = request.form.get("username","")
        mail =  request.form.get("mail","")
        password = request.form.get("password","")

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = ('SELECT id FROM users WHERE mail=%s OR username=%s')
        values = (mail,username)
        cursor.execute(sql, values)
        exists = cursor.fetchone()

        if exists:
            data = "このメールアドレスまたはユーザー名は既に使用されています。"

            return render_template("new.html",data=data)

        else:
            pwhash = generate_password_hash(password)

            sql = ('INSERT INTO users (name,username,mail,password) '
                'VALUES (%s, %s, %s, %s)')
            values = (name,username,mail,pwhash)
            cursor.execute(sql, values)
            conn.commit()

    except Exception as e:
        print(f"エラーが発生しました: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/timeline",methods=["GET","POST"])
def timeline():

    conn = None
    cursor = None

    try:
        user_id = session.get("user_id","")

        if not user_id:
            return redirect(url_for("home"))
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)


        user_sql = 'SELECT username FROM users WHERE id = %s'
        cursor.execute(user_sql, (user_id,))
        user_result = cursor.fetchone()

        if user_result:
            username = user_result['username']


        sql = ('SELECT id,username,text,photodata,timenow FROM text')
        cursor.execute(sql)
        texts = cursor.fetchall()
        sql = ('SELECT replyid,reply FROM reply')
        cursor.execute(sql)
        replies = cursor.fetchall()


        for row in texts:
            if row['photodata']:
                row['photo_b64'] = base64.b64encode(row['photodata']).decode('utf-8')
            else:
                row['photo_b64'] = None
            
            row['replies_list'] = [r for r in replies if r['replyid'] == row['id']]

    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        texts = []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template("timeline.html" , texts=texts, username=username)

@app.route("/reply",methods=["GET","POST"])
def reply():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        reply = request.form.get("reply","")
        id = request.form.get("id","")
        sql = ('SELECT * FROM text WHERE id = %s')
        cursor.execute(sql, (id,))
        text = cursor.fetchone()

        if not text:
            return redirect(url_for("timeline"))
        
        textid = text['id']

        sql = ('INSERT INTO reply (replyid,reply) VALUES (%s,%s)')
        values = (textid,reply)
        cursor.execute(sql,values)
        conn.commit()

    except Exception as e:
        print(f"エラーが発生しました: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for("timeline"))




@app.route("/newpost")
def newpost():
        
    user_id = session.get("user_id","")
    if not user_id:
        return redirect(url_for("home"))
    return render_template("newpost.html", data=None)

@app.route("/post", methods=["POST"])
def post():

    conn =None
    cursor = None

    try:
        user_id = session.get("user_id","")
        if not user_id:
            return redirect(url_for("home"))
        
        text = request.form.get("text","")
        photo_file = request.files.get("photo")
        photo_binary = None
        if photo_file and photo_file.filename != "":
            photo_binary = photo_file.read()

        conn = get_db_connection()
        cursor =conn.cursor(dictionary=True)

        usersql = 'SELECT username FROM users WHERE id = %s'
        cursor.execute(usersql,(user_id,))
        userresult = cursor.fetchone()
        if userresult:
            username = userresult['username']

        sql = ('INSERT INTO text (username,text,photodata) VALUES (%s,%s,%s)')
        values = (username,text,photo_binary)
        cursor.execute(sql,values)
        conn.commit()


    except Exception as e:
        print(f"エラーが発生しました: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for("timeline"))

@app.route("/search",methods=["POST"])
def search():

    conn = None
    cursor = None

    try:
        user_id = session.get("user_id","")

        if not user_id:
            return redirect(url_for("home"))
        
        search = request.form.get("search","")
        search = f"%{search}%"
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)


        user_sql = 'SELECT username FROM users WHERE id = %s'
        cursor.execute(user_sql, (user_id,))
        user_result = cursor.fetchone()

        if user_result:
            username = user_result['username']


        sql = ('SELECT username,text,photodata,timenow FROM text WHERE text LIKE %s or username LIKE %s ')
        cursor.execute(sql,(search,search))
        texts = cursor.fetchall()
        for row in texts:
            if row['photodata']:
                row['photo_b64'] = base64.b64encode(row['photodata']).decode('utf-8')
            else:
                row['photo_b64'] = None
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        texts = []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template("timeline.html" , mode="search" , texts=texts, username=username)

@app.route("/mypage",methods=["GET","POST"])
def mypage():

    conn = None
    cursor = None

    try:
        user_id = session.get("user_id","")

        if not user_id:
            return redirect(url_for("home"))
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)


        user_sql = ('SELECT username FROM users WHERE id = %s')
        cursor.execute(user_sql, (user_id,))
        user_result = cursor.fetchone()

        if user_result:
            username = user_result['username']


        sql = ('SELECT * FROM text WHERE username = %s ')
        cursor.execute(sql, (username,))
        texts = cursor.fetchall()
        for row in texts:
            if row['photodata']:
                row['photo_b64'] = base64.b64encode(row['photodata']).decode('utf-8')
            else:
                row['photo_b64'] = None
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        texts = []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template("mypage.html", texts=texts, username=username)

@app.route("/stations",methods=["GET"])
def stations():
    conn = None
    cursor = None

    try:
        user_id = session.get("user_id","")

        if not user_id:
            return redirect(url_for("home"))
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        user_sql = 'SELECT username FROM users WHERE id = %s'
        cursor.execute(user_sql, (user_id,))
        user_result = cursor.fetchone()
        if user_result:
            username = user_result['username']

        sql = ('SELECT line_id,line_name FROM train')
        cursor.execute(sql)
        trains = cursor.fetchall()
        sql = ('SELECT line_id, station_name, checked FROM stations')
        cursor.execute(sql)
        stations = cursor.fetchall()

        for row in trains:
            row['stations_list'] = [s for s in stations if s['line_id'] == row['line_id']]



    except Exception as e:
        print(f"エラーが発生しました: {e}")
        stations = []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template("stations.html", stations=stations, trains=trains, username=username)

@app.route("/stationsearch",methods=["POST","GET"])
def stationsearch():
    pass

if __name__ == "__main__":
    app.run(debug=True)