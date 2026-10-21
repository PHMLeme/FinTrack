import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = Path(__file__).parent / "Fintrack.db"

# Inicializando Categorias

CATEGORIAS_PADRAO = [
    ("Salário", "Receita"),
    ("Freelance", "Receita"),
    ("Rendimentos", "Receita"),
    ("Alimentação", "Despesa"),
    ("Moradia", "Despesa"),
    ("Transporte", "Despesa"),
    ("Saúde", "Despesa"),
    ("Lazer", "Despesa"),
    ("Capacitação", "Despesa"),
]

# Conexão

def _conectar() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout = 30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# Inicialização do BD

def inicializar_banco() -> None:
    
    with _conectar() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS categorias (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        nome            TEXT NOT NULL,
        tipo            TEXT NOT NULL CHECK (tipo IN ('Receita', 'Despesa'))
        );

        CREATE TABLE IF NOT EXISTS transacoes (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria_id    INTEGER NOT NULL REFERENCES categorias(id),
        forma_id        INTEGER NOT NULL REFERENCES formas(id),
        data            DATE NOT NULL,
        valor           REAL NOT NULL CHECK (valor > 0),
        descricao       TEXT NOT NULL,
        tipo            TEXT NOT NULL CHECK (tipo IN ('Receita', 'Despesa'))
        );

        CREATE TABLE IF NOT EXISTS formas (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo            TEXT NOT NULL CHECK (tipo IN ('Conta', 'Cartao')),
        nome            TEXT NOT NULL
        );
        """)
        qtd = conn.execute("SELECT COUNT(*) FROM categorias").fetchone()[0]
        if qtd == 0:
            conn.executemany(
                "INSERT INTO categorias (nome, tipo) VALUES (?,?)", CATEGORIAS_PADRAO
            )

# Trabalhando a tabela Categorias.

def listar_categorias(tipo: str | None = None) -> list[dict]:
    sql = "SELECT * FROM categorias "
    params = []

    if tipo:
        sql += "WHERE tipo = ? "
        params.append(tipo)

    sql += "ORDER BY tipo, nome "

    with _conectar() as conn:
        return[dict(r) for r in conn.execute(sql,params).fetchall()]


def inserir_categoria(nome: str, tipo: str) -> None:
    with _conectar() as conn:
        conn.execute("INSERT INTO categorias (nome, tipo) VALUES (?, ?)", (nome.strip(), tipo))


def deletar_categoria(categoria_id: int) -> None:
    with _conectar() as conn:
        conn.execute("DELETE FROM categorias WHERE id = ?", (categoria_id,))

# Trabalhando as transações.

def inserir_transacao(
        categoria_id: int,
        forma_id: int,
        data: date,
        valor: float,
        descricao: str,
        tipo: str,
) -> None:
    with _conectar() as conn:
        conn.execute("""INSERT INTO transacoes (categoria_id, forma_id, data, valor, descricao, tipo)
                      VALUES (?, ?, ?, ?, ?, ?)""", (categoria_id, forma_id, data, valor, descricao.strip(), tipo))


def listar_transacoes(
        mes: int | None = None,
        ano: int | None = None,
        tipo: str | None = None,
        forma: int | None = None,
) -> list[dict]:
    sql = """SELECT t.id,
                    t.data,
                    t.tipo,
                    c.nome AS categoria,
                    t.descricao,
                    t.valor,
                    t.forma_id
            FROM transacoes t
            JOIN categorias c ON c.id = t.categoria_id
            WHERE 1=1 """
    params: list = []

    if mes and ano:
        sql += " AND strftime('%m', t.data) = ? AND strftime('%Y', t.data) = ? "
        params += [f"{mes:02d}",str(ano)]

    if tipo:
        sql += " AND t.tipo = ? "
        params.append(tipo)

    if forma:
        sql += " AND t.forma_id = ? "
        params.append(forma)

    sql += " ORDER BY t.data DESC, t.forma_id DESC "
    with _conectar() as conn:
        return[dict(r) for r in conn.execute(sql, params).fetchall()]

def deletar_transacao(transacao_id: int) -> None:
    with _conectar() as conn:
            conn.execute("DELETE FROM transacoes WHERE id = ?", (transacao_id,))


# Trabalhando as formas de pagamento.

def listar_formas(tipo: str | None = None) -> list[dict]:
    sql = "SELECT * FROM formas "
    params = []

    if tipo:
        sql = " WHERE tipo = ? "
        params.append(tipo)
    sql += "ORDER BY tipo, nome"

    with _conectar() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def inserir_forma(  tipo: str,
                    nome: str,
) -> None:
    with _conectar() as conn:
        conn.execute(
            """INSERT INTO formas (tipo, nome)
            VALUES (?, ?)""",
            (tipo, nome.strip(),)
        )

def deletar_forma(form_id: int) -> None:
    with _conectar() as conn:
        conn.execute("DELETE FROM formas WHERE id = ?", (form_id,))

# Preparando dados para as Dashboards.

def resumo_mes_atual() -> dict:
    hoje = date.today()
    mes = f"{hoje.month:02d}"
    ano = str(hoje.year)

    with _conectar() as conn:
        receitas = conn.execute(
            """SELECT COALESCE(SUM(valor), 0) FROM transacoes 
            WHERE tipo = 'Receita' 
            AND strftime('%m', data) = ?
            AND strftime('%Y', data) = ?""",
            (mes, ano)
        ).fetchone()[0]
        despesas = conn.execute(
                    """SELECT COALESCE(SUM(valor), 0) FROM transacoes 
                    WHERE tipo = 'Despesa' 
                    AND strftime('%m', data) = ?
                    AND strftime('%Y', data) = ?""",
                    (mes, ano)
                ).fetchone()[0]
    return{
        "receitas" : receitas,
        "despesas" : despesas,
        "saldo" : receitas - despesas
    }

def fluxo_mensal() -> list[dict]:
    with _conectar() as conn:
        rows = conn.execute(
            """SELECT strftime('%Y-%m', data) AS mes,
            tipo,
            sum(valor) AS total
            FROM transacoes
            WHERE data >= date('now', '-12 months')
            GROUP BY mes, tipo
            ORDER BY mes"""
        ).fetchall()
    return [dict(r) for r in rows]

def despesas_por_categoria_mes_atual() -> list[dict]:
    hoje = date.today()
    mes = f"{hoje.month:02d}"
    ano = str(hoje.year)

    with _conectar() as conn:
        rows = conn.execute(
            """SELECT c.nome AS categoria,
            SUM(t.valor) AS total
            FROM transacoes t
            JOIN categorias c
            ON c.id = t.categoria_id
            WHERE t.tipo = 'Despesa'
            AND strftime('%m', t.data) = ?
            AND strftime('%Y', t.data) = ?
            GROUP BY c.nome
            ORDER BY total DESC""",
            (mes, ano)
        ).fetchall()
        return [dict(r) for r in rows]

def filtros_datas() -> list[dict]:
    with _conectar() as conn:
        meses_cadastrados = conn.execute(
            """SELECT strftime('%Y-%m', data) AS mes FROM transacoes"""
        ).fetchall()
        return [dict(r) for r in meses_cadastrados]