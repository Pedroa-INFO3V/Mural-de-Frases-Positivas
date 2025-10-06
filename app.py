from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from datetime import datetime

app = Flask(__name__)

def conectar_db():
    return mysql.connector.connect(
        user='root',
        password='labinfo',
        database='mural_frases',
        host='127.0.0.1'
    )

def get_user_id_by_name(nome_usuario):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        sql = "SELECT id FROM usuarios WHERE nome_usuario = %s"
        cursor.execute(sql, (nome_usuario,))
        user_id = cursor.fetchone()
        return user_id[0] if user_id else None
    except Exception as e:
        return None
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

@app.route("/")
def tela_login():
    return render_template("index.html")

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome_usuario = request.form.get("nome_usuario", "").strip()
        senha = request.form.get("senha", "")

        if not nome_usuario or not senha:
            return render_template("cadastro.html", mensagem="Preencha nome e senha.")

        try:
            conn = conectar_db()
            cursor = conn.cursor()

            sql = "INSERT INTO usuarios (nome_usuario, senha) VALUES (%s, %s)"
            cursor.execute(sql, (nome_usuario, senha))
            conn.commit()
            
            return redirect(url_for("tela_login"))

        except mysql.connector.Error as err:
            return render_template("cadastro.html", mensagem=f"Erro ao cadastrar: {err}")

        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass
    else:
        return render_template("cadastro.html")

@app.route("/login", methods=["POST"])
def login():
    nome_usuario = request.form.get("nome_usuario", "").strip()
    senha = request.form.get("senha", "")

    if not nome_usuario or not senha:
        return render_template("index.html", mensagem="Preencha nome e senha para entrar.")

    try:
        conn = conectar_db()
        cursor = conn.cursor(dictionary=True)

        sql = "SELECT nome_usuario FROM usuarios WHERE nome_usuario = %s AND senha = %s"
        cursor.execute(sql, (nome_usuario, senha))
        usuario = cursor.fetchone()

        if usuario:
            return redirect(url_for("mural", nome=usuario['nome_usuario']))
        else:
            return render_template("index.html", mensagem="Usuário ou senha inválidos.")

    except mysql.connector.Error as err:
        return render_template("index.html", mensagem=f"Erro ao tentar login: {err}")

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

@app.route("/mural/<nome>")
def mural(nome):
    try:
        conn = conectar_db()
        cursor = conn.cursor(dictionary=True) 

        sql_frases = """
            SELECT 
                f.id,
                f.conteudo AS texto_frase, 
                u.nome_usuario AS autor, 
                f.data_postagem, 
                COALESCE(SUM(c.quantidade), 0) AS curtidas_count
            FROM frases f
            JOIN usuarios u ON f.usuario_id = u.id
            LEFT JOIN curtidas c ON f.id = c.frase_id
            GROUP BY f.id, f.conteudo, u.nome_usuario, f.data_postagem
            ORDER BY f.data_postagem DESC
        """
        cursor.execute(sql_frases)
        frases = cursor.fetchall()
        
        return render_template("principal.html", frases=frases, nome_usuario=nome)

    except mysql.connector.Error as err:
        return render_template("principal.html", frases=[], nome_usuario=nome)
    
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

@app.route("/postar_frase/<nome>", methods=["POST"])
def postar_frase(nome):
    conteudo = request.form.get("conteudo_frase", "").strip()
    
    if not conteudo:
        return redirect(url_for("mural", nome=nome))

    usuario_id = get_user_id_by_name(nome)
    
    if usuario_id is None:
        return redirect(url_for("tela_login"))

    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        sql = "INSERT INTO frases (usuario_id, conteudo, data_postagem) VALUES (%s, %s, NOW())"
        cursor.execute(sql, (usuario_id, conteudo))
        conn.commit()
        
    except mysql.connector.Error as err:
        pass

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass
            
    return redirect(url_for("mural", nome=nome))
            
@app.route("/perfil/<nome>")
def perfil(nome):
    usuario_id = get_user_id_by_name(nome)
    
    if usuario_id is None:
        return redirect(url_for("tela_login"))
    
    frases_usuario = []
    total_frases = 0
    total_curtidas = 0
    
    try:
        conn = conectar_db()
        cursor = conn.cursor(dictionary=True)

        sql_frases = """
            SELECT 
                f.conteudo AS texto_frase, 
                f.data_postagem, 
                COALESCE(SUM(c.quantidade), 0) AS curtidas_count
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
        
    except mysql.connector.Error as err:
        pass

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass
            
    return render_template("perfil.html", 
                           nome_usuario=nome,
                           frases=frases_usuario,
                           total_frases=total_frases,
                           total_curtidas=total_curtidas)

if __name__ == "__main__":
    app.run(debug=True)