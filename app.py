from flask import Flask, request, jsonify, render_template
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "gastos.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            metodo TEXT NOT NULL CHECK(metodo IN ('pix', 'credito', 'debito')),
            categoria TEXT,
            data TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def validar_dados(dados):
    dados = dados or {}
    descricao = (dados.get("descricao") or "").strip()
    categoria = (dados.get("categoria") or "Outros").strip() or "Outros"
    metodo = dados.get("metodo")
    data = dados.get("data") or datetime.now().strftime("%Y-%m-%d")

    if not descricao:
        return None, "Descrição é obrigatória"
    if len(descricao) > 120:
        return None, "Descrição deve ter no máximo 120 caracteres"
    try:
        valor = round(float(str(dados.get("valor")).replace(",", ".")), 2)
        if valor <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return None, "Valor inválido"
    if metodo not in ("pix", "credito", "debito"):
        return None, "Método de pagamento inválido"
    try:
        datetime.strptime(data, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None, "Data inválida"
    return {"descricao": descricao, "valor": valor, "metodo": metodo,
            "categoria": categoria[:60], "data": data}, None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/gastos", methods=["GET"])
def listar_gastos():
    conn = get_db()
    gastos = conn.execute("SELECT * FROM gastos ORDER BY data DESC, id DESC").fetchall()
    conn.close()
    return jsonify([dict(g) for g in gastos])


@app.route("/api/gastos", methods=["POST"])
def criar_gasto():
    dados, erro = validar_dados(request.get_json(silent=True))
    if erro:
        return jsonify({"erro": erro}), 400

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO gastos (descricao, valor, metodo, categoria, data) VALUES (?, ?, ?, ?, ?)",
        (dados["descricao"], dados["valor"], dados["metodo"], dados["categoria"], dados["data"]),
    )
    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()

    return jsonify({"id": novo_id, **dados}), 201


@app.route("/api/gastos/<int:gasto_id>", methods=["PUT"])
def editar_gasto(gasto_id):
    dados, erro = validar_dados(request.get_json(silent=True))
    if erro:
        return jsonify({"erro": erro}), 400
    conn = get_db()
    cursor = conn.execute(
        "UPDATE gastos SET descricao = ?, valor = ?, metodo = ?, categoria = ?, data = ? WHERE id = ?",
        (dados["descricao"], dados["valor"], dados["metodo"], dados["categoria"], dados["data"], gasto_id),
    )
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        return jsonify({"erro": "Gasto não encontrado"}), 404
    return jsonify({"id": gasto_id, **dados})


@app.route("/api/gastos/<int:gasto_id>", methods=["DELETE"])
def deletar_gasto(gasto_id):
    conn = get_db()
    cursor = conn.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
    removido = cursor.rowcount
    conn.commit()
    conn.close()
    if not removido:
        return jsonify({"erro": "Gasto não encontrado"}), 404
    return jsonify({"ok": True})


@app.route("/api/resumo", methods=["GET"])
def resumo():
    conn = get_db()
    linhas = conn.execute(
        "SELECT metodo, SUM(valor) as total FROM gastos GROUP BY metodo"
    ).fetchall()
    total_geral = conn.execute("SELECT SUM(valor) as total FROM gastos").fetchone()
    conn.close()

    resumo_por_metodo = {"pix": 0, "credito": 0, "debito": 0}
    for linha in linhas:
        resumo_por_metodo[linha["metodo"]] = linha["total"]

    return jsonify({
        "por_metodo": resumo_por_metodo,
        "total": total_geral["total"] or 0
    })


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
