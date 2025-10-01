<<<<<<< HEAD
from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

# Função para conectar ao banco de dados
def conectar_db():
    return mysql.connector.connect(
        user='root',
        password='labinfo',
        database='mural_frases',
        host='127.0.0.1'
    )

# Rota principal: tela de login (mostra primeiro ao abrir o site)
@app.route("/")
def tela_login():
    return render_template("index.html")

# Rota para cadastro (GET = exibe o formulário, POST = salva no banco)
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

            # Após cadastro, redireciona para a tela de login
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

# Rota para login (POST)
@app.route("/login", methods=["POST"])
def login():
    nome_usuario = request.form.get("nome_usuario", "").strip()
    senha = request.form.get("senha", "")

    if not nome_usuario or not senha:
        return render_template("index.html", mensagem="Preencha nome e senha para entrar.")

    try:
        conn = conectar_db()
        cursor = conn.cursor(dictionary=True)

        sql = "SELECT * FROM usuarios WHERE nome_usuario = %s AND senha = %s"
        cursor.execute(sql, (nome_usuario, senha))
        usuario = cursor.fetchone()

        if usuario:
            return render_template("principal.html", nome=nome_usuario)
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

if __name__ == "__main__":
    app.run(debug=True)
=======
from flask import Flask, render_template, request
import mysql.connector

app = Flask(__name__)

def conectar_db():
    return mysql.connector.connect(
        user='root',
        password='labinfo',
        database='mural_frases',
        host='127.0.0.1'
    )

@app.route("/")
def tela_cadastro():
    return render_template("cadastro.html")

@app.route("/cadastro", methods=["POST"])
def cadastro():
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

        return render_template("principal.html", nome=nome_usuario, mensagem="Cadastro realizado com sucesso!")

    except mysql.connector.Error as err:
        return render_template("cadastro.html", mensagem=f"Erro ao cadastrar: {err}")

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

if __name__ == "__main__":
    app.run(debug=True)
>>>>>>> 07cd6b4f690f4d00f9a608ddd9e937c438b8e361
