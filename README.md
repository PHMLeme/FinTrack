# FinTrack

Um estudo de caso para treinar habilidades Python e SQL.

O Fintrack é uma aplicação desktop de controle financeiro pessoal desenvolvida em Python. O projeto salva os dados localmente para garantir a privacidade e segurança dos seus dados sem dependência de servidores externos ou nuvem.

---

## Tecnologias Utilizadas:

- **Python 3** (Linguagem principal)
- **Streamlit** (Interface gráfica interativa)
- **SQLite3** (Banco de dados local)
- **Pandas & Plotly** (Manipulação de dados e visualização de gráficos)

---

## Decisões de arquitetura

- **Abordagem Offline-First:** Todos os dados financeiros são armazenados localmente em um arquivo chamado (`Fintrack.db`), garantindo que só você tem acesso aos seus dados e não depende de conexão.
- **Separação de Responsabilidades:** A lógica de manipulação do banco de dados está isolada em módulos dedicados (`database.py`), mantendo a interface (`app.py`) limpa e focada na experiência do usuário.

---

### Como Executar o Projeto:

Siga os passos abaixo para rodar o FinTrack na sua máquina:

### 1. Pré-requisitos

Certifique-se de ter o **Python** instalado no seu computador.

### 2. Clonar o repositório

```bash
git clone [https://github.com/SEU-USUARIO/fintrack.git](https://github.com/SEU-USUARIO/fintrack.git)
cd fintrack
```

### 3. Instalar os pré requisitos

```bash
pip install -r requisitos.txt
```

### 4. Executar a aplicação

```bash
streamlit run app.py
```
