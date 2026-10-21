import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import database as db
from dateutil.relativedelta import relativedelta

# Definindo regras css para estilizar o projeto
def local_css(regras):
    with open(regras, "r", encoding = "utf-8") as css:
        st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html = True)
local_css("regras.css")

st.set_page_config(
    page_title = "Fintrack",
    page_icon = "$",
    layout = "wide",
    initial_sidebar_state = "expanded"
)

db.inicializar_banco()

PAGINAS = [
    "Relatorios",
    "Nova transação",
    "Histórico",
    "Categorias",
    "Formas de pagamento",
]

with st.sidebar:
    st.title("Fintrack")
    st.markdown("---")

    pagina = st.radio("Navegação", PAGINAS, index=0, label_visibility="collapsed")

    st.markdown("---")
    st.caption("Gestão financeira pessoal local.")

def formatar_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",","X").replace(".",",").replace("X", ".")

MESES = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6:  "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
}


# Página 1: Dashboard
def pagina_dashboard():
    st.title("Relatórios")
    st.markdown(f"**Mês atual:** {MESES[date.today().month]}/{date.today().year}")
    st.markdown("---")

    resumo = db.resumo_mes_atual()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label = "Total de Receitas",
            value = formatar_brl(resumo["receitas"])
        )
    with col2:
        st.metric(
            label = "Total de Despesas",
            value = formatar_brl(resumo["despesas"])
        )
    with col3:
        saldo = resumo["saldo"]
        st.metric(
            label = "Saldo atual",
            value = formatar_brl(saldo),
            delta = formatar_brl(saldo) if saldo !=0 else None,
            delta_color = "normal"
        )
    st.markdown("---")
    st.subheader("Fluxo de caixa")
    fluxo = db.fluxo_mensal()
    if not fluxo:
        st.info("Nenhuma transação encontrada. Adicione a sua primeira transação em **Nova Transação**.")
    else:
        df_fluxo = pd.DataFrame(fluxo)
        df_pivot = df_fluxo.pivot_table(index = "mes", columns = "tipo", values = "total", fill_value = 0).reset_index()
        for col in ("Receita", "Despesa"):
            if col not in df_pivot.columns:
                df_pivot[col] = 0.0

        df_pivot = df_pivot.rename(columns = {
            "mes" : "Mês",
            "Receita" : "Receitas",
            "Despesa" : "Despesas"
        })
        df_pivot['Saldo Mensal'] = df_pivot['Receitas'] - df_pivot['Despesas']
        df_pivot['Saldo Acumulado'] = df_pivot['Saldo Mensal'].cumsum()

        
    #Grafico de saldo acumulado
        fig = px.line(
            df_pivot,
            x='Mês',
            y=['Receitas', 'Despesas', 'Saldo Acumulado'],
            labels={'value': 'Valor (R$)', 'variable': 'Métrica'},
            title='Evolução Financeira Mensal',
            color_discrete_map = {"Receitas": "#2ecc71", "Despesas": "#e74c3c", "Saldo Acumulado": "#3498db"}
        )

        fig.update_layout(
            xaxis_title="Mês",
            yaxis_title="R$ (Reais)",
            hovermode="x unified",
            legend_title="Legenda"
        )
        st.plotly_chart(fig, use_container_width=True)

        col4, col5 = st.columns(2)
        with col4:
            # Grafico despesa por categoria
                st.subheader("Despesas por categoria - Mês atual")
                desp_cat = db.despesas_por_categoria_mes_atual()
                if not desp_cat:
                    st.info("Sem despesas registradas esse mês.")
                else:
                    df_cat = pd.DataFrame(desp_cat)
            
                    fig_pizza = px.pie(
                        df_cat,
                        names = "categoria",
                        values = "total",
                        hole = 0.2,
                        title= "Distribuição de despesas por categoria",
                        color_discrete_sequence = px.colors.qualitative.G10_r
                    )
                    fig_pizza.update_traces(textposition = "inside", textinfo = "percent+label")
                    fig_pizza.update_layout(
                        showlegend = True,
                        paper_bgcolor = "rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig_pizza, use_container_width = True)

                with col5:
                    # Grafico receita/despesa
                    fig_fluxo = px.bar(
                        df_pivot,
                        x = "Mês",
                        y = ["Receitas", "Despesas"],
                        barmode = "group",
                        color_discrete_map = {"Receitas": "#2ecc71", "Despesas": "#e74c3c"},
                        labels = {"value": "Valor(R$)", "variable": "Tipo"},
                        title = "Receitas vs. Despesas por mês"
                    )
                    fig_fluxo.update_layout(
                        legend_title_text = "",
                        plot_bgcolor = "rgba(0,0,0,0)",
                        paper_bgcolor = "rgba(0,0,0,0)",
                        yaxis_tickformat = ",.2f"
                    )
                    st.plotly_chart(fig_fluxo, use_container_width = True)

# Página 2: Nova transação
def pagina_nova_transacao():
    st.title("Nova transação")
    st.markdown("Preencha os campos abaixo para registrar uma nova movimentação financeira.")
    st.markdown ("---")

    tipo = st.radio(
        "Tipo *",
        options = ["Despesa", "Receita"],
        horizontal = True
    )

    categorias = db.listar_categorias(tipo = tipo)
    formas = db.listar_formas()
    with st.form("form_transacao", clear_on_submit = True):
        data_transacao = st.date_input("Data *", value = date.today())
        opcoes_cat = {c["nome"]: c["id"] for c in categorias}
        opcoes_forma = {f["nome"]: f["id"] for f in formas}
        if opcoes_cat:
            categoria_nome = st.selectbox("Categoria *", options = list(opcoes_cat.keys()))
        else:
            st.warning("Nenhuma categoria disponível para este tipo. Adicione em **Gerenciar Categorias**.")
            categoria_nome = None

        forma_nome = st.selectbox("Forma de pagamento *", options = list(opcoes_forma.keys()))
        descricao = st.text_input("Descrição *", placeholder = "Origem da receita/despesa")
        valor = st.number_input(
            "Valor (R$) *",
            min_value=0.01,
            step = 0.01,
            format = "%.2f",
            placeholder= "0.00"
        )
        parcelas = st.number_input(
                    "Numero de parcelas *",
                    min_value=1,
                    step = 1,
                    format = "%.0f",
                    placeholder= "1"
                )
        
        salvar = st.form_submit_button("Salvar transação", use_container_width = True)
        
        if salvar:
            erros = []
    
            if not descricao.strip():
                erros.append("A descrição não pode estar em branco.")
            if not categoria_nome:
                erros.append("Selecione uma categoria válida")
            if not formas:
                erros.append("A forma de pagamento não pode ser nula")
            if valor <= 0:
                erros.append("O valor deve ser maior que zero.")
    
            if erros:
                for e in erros:
                    st.error(e)
            else:
                if parcelas > 1:
                    for i in range(1, parcelas + 1):
                        descricao_parcela = f"{descricao} ({i}/{parcelas})"
                        data_parcela = data_transacao + relativedelta(months = i - 1)
                        db.inserir_transacao(
                                            categoria_id= opcoes_cat[categoria_nome],
                                            descricao= descricao_parcela,
                                            valor= valor,
                                            data= data_parcela,
                                            tipo= tipo,
                                            forma_id= opcoes_forma[forma_nome]
                                        )
                else:
                    db.inserir_transacao(
                        categoria_id= opcoes_cat[categoria_nome],
                        descricao= descricao,
                        valor= valor,
                        data= data_transacao,
                        tipo= tipo,
                        forma_id= opcoes_forma[forma_nome]
                    )
                st.success(f"Transação salva com sucesso!({tipo}: {formatar_brl(valor)})")

# Página 3: Histórico
def pagina_historico():
    st.title("Histórico de transações")
    st.markdown("---")

    hoje = date.today()
    col1, col2, col3 = st.columns(3)

    with col1:
        anos_disponiveis = list(range(hoje.year + 1 , hoje.year - 5, -1))
        ano_sel = st.selectbox("Filtrar por Ano", options = ["Todos"] + [str(a) for a in anos_disponiveis])

    with col2:
            meses_opcoes = {"Todos": None} | {f"{v}/{k:02d}":k for k, v in MESES.items()}
            mes_label = st.selectbox("Filtrar por mês", options = list(meses_opcoes.keys()))
            mes_sel = meses_opcoes[mes_label]

    with col3:
        tipo_sel = st.selectbox("Filtrar por tipo", options = ["Todos", "Receita", "Despesa"])

    mes_param = mes_sel if mes_label != "Todos" else None
    ano_param = int(ano_sel) if ano_sel != "Todos" else None
    tipo_param = tipo_sel if tipo_sel != "Todos" else None

    if mes_param and ano_param:
        transacoes = db.listar_transacoes(mes = mes_param,ano = ano_param, tipo = tipo_param)
    elif ano_param:
        todas = db.listar_transacoes(tipo = tipo_param)
        transacoes = [t for t in todas if str(t["data"])[:4] == str(ano_param)]
    else:
        transacoes = db.listar_transacoes(tipo = tipo_param)

    st.markdown("---")

    if not transacoes:
        st.info("nenhuma transação encontrada com os filtros selecionados")
        return

    df = pd.DataFrame(transacoes)
    df["data"] = pd.to_datetime(df["data"]).dt.strftime("%d/%m/%Y")
    df["valor_fmt"] = df["valor"].apply(formatar_brl)
    df_exibir = df[["id", "data", "tipo", "categoria", "descricao", "valor_fmt"]].rename(columns = {
        "id": "ID",
        "data": "Data",
        "tipo": "Tipo",
        "categoria": "Categoria",
        "descricao": "Descrição",
        "valor_fmt": "Valor"

    })

    st.dataframe(df_exibir, use_container_width=True, hide_index=True)

    total_receitas = df[df["tipo"] == "Receita"]["valor"].sum()
    total_despesas = df[df["tipo"] == "Despesa"]["valor"].sum()
    col_r, col_d, col_s = st.columns(3)
    col_r.metric("Receitas (filtro)", formatar_brl(total_receitas))
    col_d.metric("Despesas (filtro)", formatar_brl(total_despesas))
    col_s.metric("Saldo (filtro)", formatar_brl(total_receitas - total_despesas))

    st.markdown("---")
    st.subheader("Excluir transação")
    st.caption("Informe o ID da transação que deseja remover")

    col_id, col_btn = st.columns([2,1])
    with col_id:
        id_excluir = st.number_input("ID da transação", min_value=1, step=1, label_visibility="collapsed")
    with col_btn:
        if st.button("Excluir", type="primary", use_container_width=True):
            ids_validos = df["id"].tolist()
            if int(id_excluir) in ids_validos:
                db.deletar_transacao(int(id_excluir))
                st.success(f"Transação #{int(id_excluir)} removida com sucesso!")
                st.rerun()
            else:
                st.error("ID não encontrado nas transações exibidas.")

# Página 4: Gerenciar categorias
def pagina_categorias():
    st.title("Gerenciar Categorias")
    st.markdown("---")

    col_form, col_lista = st.columns([1, 2])

    with col_form:
        st.subheader("Nova categoria")
        with st.form("form_categoria", clear_on_submit= True):
            nome_cat = st.text_input("Nome da Categoria *")
            tipo_cat = st.radio("Tipo *", options=["Despesa", "Receita"], horizontal= True)
            adicionar = st.form_submit_button("Salvar Categoria", use_container_width=True)
        if adicionar:
            if not nome_cat.strip():
                st.error("O nome da categoria não pode estar em branco.")
            else:
                nomes_existentes = [c["nome"].lower() for c in db.listar_categorias()]
                if nome_cat.strip().lower() in nomes_existentes:
                    st.warning(f"A categoria {nome_cat} já existe!")
                else:
                    db.inserir_categoria(nome_cat, tipo_cat)
                    st.success(f"Categoria {nome_cat} inserida com sucesso!")
                    st.balloons()
                    st.rerun()

    with col_lista:
        st.subheader("Categorias cadastradas:")
        categorias = db.listar_categorias()

        if not categorias:
            st.info("Não há categoria cadastrada!")
        else:
            df_cat = pd.DataFrame(categorias).rename(columns = {
                "id": "ID", "nome" : "Nome", "tipo" : "Tipo"
            })
            st.dataframe(df_cat, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.caption("Excluir uma categoria remove apenas ela. transações vinculadas continuam salvas.")

            col_cid, col_cbtn = st.columns([2, 1])
            with col_cid:
                id_cat_del = st.number_input(
                    "ID da categoria", min_value=1, step = 1,
                    label_visibility="collapsed", key= "del_cat"
                )
            with col_cbtn:
                if st.button("Excluir", type= "primary", use_container_width= True, key = "btn_del_cat"):
                    ids_cat = df_cat["ID"].tolist()
                    if int(id_cat_del) in ids_cat:
                        db.deletar_categoria(int(id_cat_del))
                        st.success(f"Categoria {int(id_cat_del)} removida!")
                        st.rerun()
                    else:
                        st.error("ID não encontrado.")

# Página 4: Formas de pagamento
def pagina_formas():
    st.title("Gerenciar formas de pagamento")
    st.markdown("---")

    col_form, col_lista = st.columns([1,2])

    with col_form:
        st.subheader("Nova Forma de pagamento")
        selecao = st.radio("Tipo: *", options = ["Conta", "Cartão"], horizontal = True)
        with st.form("form_forma", clear_on_submit = True):
            nome_forma = st.text_input("Nome *")
            if selecao == "Cartão":
                tipo_forma = "Cartao"
            else:
                tipo_forma = "Conta"
            salvar = st.form_submit_button("Salvar forma de pagamento", use_container_width = True)

            if salvar:
                erros = []

                if not nome_forma.strip():
                    erros.append("O nome não pode estar vazio")
                else: db.inserir_forma(
                    tipo = tipo_forma,
                    nome = nome_forma.strip(),
                )
    with col_lista:
            st.subheader("Formas de pagamento cadastradas:")
            formas = db.listar_formas()
    
            if not formas:
                st.info("Não há forma de pagamento cadastrada!")
            else:
                df_form = pd.DataFrame(formas).rename(columns = {
                    "Cartao" : "Cartão"
                })
                st.dataframe(df_form, use_container_width=True, hide_index=True)
    
                st.markdown("---")
                st.caption("Excluir uma forma de pagamento remove apenas ela. transações vinculadas continuam salvas.")
    
                col_cid, col_cbtn = st.columns([2, 1])
                with col_cid:
                    id_form_del = st.number_input(
                        "ID da categoria", min_value=1, step = 1,
                        label_visibility="collapsed", key= "del_cat"
                    )
                with col_cbtn:
                    if st.button("Excluir", type= "primary", use_container_width= True, key = "btn_del_form"):
                        ids_form = df_form["ID"].tolist()
                        if int(id_form_del) in ids_form:
                            db.deletar_forma(int(id_form_del))
                            st.success(f"Categoria {int(id_form_del)} removida!")
                            st.rerun()
                        else:
                            st.error("ID não encontrado.")


# Roteamento
if pagina == PAGINAS[0]:
    pagina_dashboard()
elif pagina == PAGINAS[1]:
    pagina_nova_transacao()
elif pagina == PAGINAS[2]:
    pagina_historico()
elif pagina == PAGINAS[3]:
    pagina_categorias()
elif pagina == PAGINAS[4]:
    pagina_formas()