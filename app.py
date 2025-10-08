from flask import Flask, render_template, request, redirect, url_for, session
from mysql.connector import connection, Error as MySQLError
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'galadinhos.com' 

def conectar_db():
    try:
        return connection.MySQLConnection(
            user='root',
            password='labinfo',
            database='setembroAmarelo',
            host='127.0.0.1'
        )
    except MySQLError as err:
        print(f"ERRO DE CONEXÃO CRÍTICO: {err}")
        return None 

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('tela_login')) 
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["POST"])
def tela_login():
    if request.method == "POST":
        nome_usuario = request.form.get("nome_usuario", "").strip()
        senha = request.form.get("senha", "")
        
        conn = conectar_db()
        if not conn:
             return render_template("index.html", mensagem="Erro crítico de conexão com o banco de dados.")
        
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True) 
            sql = "SELECT id, nome_usuario FROM usuarios WHERE nome_usuario = %s AND senha = %s"
            cursor.execute(sql, (nome_usuario, senha))
            usuario = cursor.fetchone()

            if usuario:
                session['user_id'] = usuario['id']
                session['nome_usuario'] = usuario['nome_usuario']
                return redirect(url_for("mural"))
            else:
                return render_template("index.html", mensagem="Usuário ou senha inválidos.")

        except MySQLError as err:
            print(f"Erro de DB no Login: {err}")
            return render_template("index.html", mensagem="Erro interno ao tentar fazer login.")
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    return render_template("index.html")

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome_usuario = request.form.get("nome_usuario", "").strip()
        senha = request.form.get("senha", "")
        
        if not nome_usuario or not senha:
            return render_template("cadastro.html", mensagem="Preencha todos os campos.")

        conn = conectar_db()
        if not conn: return render_template("cadastro.html", mensagem="Erro crítico de conexão com o banco de dados.")

        cursor = None
        try:
            cursor = conn.cursor()
            sql = "INSERT INTO usuarios (nome_usuario, senha) VALUES (%s, %s)"
            cursor.execute(sql, (nome_usuario, senha))
            conn.commit()
            
            return render_template ("index.html")

        except MySQLError as err:
            if err.errno == 1062: 
                return render_template("cadastro.html", mensagem="Nome de usuário já existe.")
            
            print(f"ERRO DE DB NO CADASTRO: {err}")
            return render_template("cadastro.html", mensagem="Erro interno ao tentar cadastrar.")
            
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    return render_template("cadastro.html")

@app.route("/postar_frase", methods=["POST"])
@login_required
def postar_frase():
    user_id = session['user_id']
    conteudo_frase = request.form.get("conteudo_frase", "").strip() 
    
    if not conteudo_frase:
        return redirect(url_for('mural')) 
    
    conn = conectar_db()
    if not conn: return redirect(url_for('mural')) 
    
    cursor = None
    try:
        cursor = conn.cursor()
        sql = "INSERT INTO frases (usuario_id, conteudo, data_postagem) VALUES (%s, %s, %s)"
        cursor.execute(sql, (user_id, conteudo_frase, datetime.now())) 
        conn.commit()
        
    except MySQLError as err:
        print(f"ERRO AO POSTAR FRASE: {err}")
        
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
        
    return redirect(url_for("mural"))

@app.route("/mural")
@login_required
def mural():
    conn = conectar_db()
    if not conn:
        return render_template("principal.html", nome_usuario=session.get('nome_usuario', 'Usuário'), frases=[], ranking=[], mensagem_erro="Erro ao conectar ao banco de dados.")
    
    cursor = None
    frases = []
    ranking = []
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        sql_frases = """
            SELECT 
                f.id, 
                f.conteudo AS texto_frase,     
                f.data_postagem, 
                u.nome_usuario AS autor,
                COUNT(c.frase_id) AS curtidas_count  
            FROM frases f
            JOIN usuarios u ON f.usuario_id = u.id   
            LEFT JOIN curtidas c ON f.id = c.frase_id
            GROUP BY f.id, f.conteudo, f.data_postagem, u.nome_usuario
            ORDER BY f.data_postagem DESC;
        """
        cursor.execute(sql_frases)
        frases = cursor.fetchall()

        sql_ranking = """
            SELECT 
                f.conteudo AS texto_frase,     
                u.nome_usuario AS autor,
                COUNT(c.frase_id) AS curtidas_count  
            FROM frases f
            JOIN usuarios u ON f.usuario_id = u.id   
            LEFT JOIN curtidas c ON f.id = c.frase_id
            GROUP BY f.id, f.conteudo, u.nome_usuario
            ORDER BY curtidas_count DESC
            LIMIT 5; 
        """
        cursor.execute(sql_ranking)
        ranking = cursor.fetchall()
        
    except MySQLError as err:
        print(f"ERRO AO BUSCAR FRASES NO MURAL: {err}")
        
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    
    return render_template(
        "principal.html", 
        nome_usuario=session['nome_usuario'], 
        frases=frases,
        ranking=ranking
    )

@app.route("/curtir/<int:frase_id>", methods=["POST"])
@login_required
def curtir_frase(frase_id):
    user_id = session['user_id']
    conn = conectar_db()
    if not conn: return redirect(url_for('mural')) 
    
    cursor = None
    try:
        cursor = conn.cursor()
        
        sql_check = "SELECT usuario_id FROM curtidas WHERE usuario_id = %s AND frase_id = %s"
        cursor.execute(sql_check, (user_id, frase_id))
        curtida_existe = cursor.fetchone()
        
        if curtida_existe:
            sql_action = "DELETE FROM curtidas WHERE usuario_id = %s AND frase_id = %s"
        else:
            sql_action = "INSERT INTO curtidas (usuario_id, frase_id) VALUES (%s, %s)"
            
        cursor.execute(sql_action, (user_id, frase_id))
        conn.commit()
        
    except MySQLError as err:
        print(f"ERRO AO CURTIR: {err}")
        
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
        
    return redirect(url_for("mural"))

@app.route("/perfil/<nome>")
@login_required
def perfil(nome):
    if session['nome_usuario'] != nome:
        return redirect(url_for('perfil', nome=session['nome_usuario']))

    usuario_id = session['user_id'] 
    
    frases_usuario = []
    total_curtidas = 0
    conn = conectar_db()
    if not conn:
         return render_template("perfil.html", nome_usuario=nome, total_frases=0, total_curtidas=0, frases=[])

    cursor = None
    
    try:
        cursor = conn.cursor(dictionary=True)

        sql_frases = """
            SELECT 
                f.conteudo AS texto_frase,    
                f.data_postagem, 
                COUNT(c.frase_id) AS curtidas_count
            FROM frases f
            LEFT JOIN curtidas c ON f.id = c.frase_id
            WHERE f.usuario_id = %s               
            GROUP BY f.id, f.conteudo, f.data_postagem
            ORDER BY f.data_postagem DESC
        """
        cursor.execute(sql_frases, (usuario_id,))
        frases_usuario = cursor.fetchall()
        
        total_frases = len(frases_usuario)
        total_curtidas = sum(f.get('curtidas_count', 0) for f in frases_usuario)

    except MySQLError as err:
        print(f"ERRO DE DB NO PERFIL: {err}")
        
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
        
    return render_template(
        "perfil.html",
        nome_usuario=nome,
        total_frases=total_frases,
        total_curtidas=total_curtidas,
        frases=frases_usuario
    )

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    session.pop('nome_usuario', None)
    return redirect(url_for('tela_login'))

if __name__ == '__main__':
    app.run(debug=True)