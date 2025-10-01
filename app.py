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
