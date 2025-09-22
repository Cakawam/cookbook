# utils/dash.py (versão corrigida sem warnings)
import pandas as pd
import seaborn as sns

def plot_sales_trend(db_conn, fig):
    """Gera um gráfico de linha com a tendência de vendas."""
    fig.clear()
    ax = fig.add_subplot(111)
    query = """
    SELECT date(data) as dia, SUM(quantidade_base * preco_unitario) as faturamento
    FROM vendas
    WHERE date(data) >= date('now', '-30 days')
    GROUP BY dia ORDER BY dia;
    """
    df = pd.read_sql_query(query, db_conn)
    if not df.empty:
        sns.lineplot(data=df, x='dia', y='faturamento', ax=ax, marker='o')
        ax.tick_params(axis='x', rotation=45, labelsize=8)
    ax.set_title('Faturamento nos Últimos 30 Dias')
    ax.set_xlabel('')
    ax.set_ylabel('Faturamento (R$)')
    fig.tight_layout()

def plot_top_products(db_conn, fig):
    """Gera um gráfico de barras com os produtos mais vendidos."""
    fig.clear()
    ax = fig.add_subplot(111)
    query = """
    SELECT p.nome, SUM(v.quantidade_base) as total_vendido
    FROM vendas v JOIN produtos p ON v.produto_id = p.id
    GROUP BY p.nome ORDER BY total_vendido DESC LIMIT 5;
    """
    df = pd.read_sql_query(query, db_conn)
    if not df.empty:
        # CORREÇÃO APLICADA AQUI
        sns.barplot(data=df, x='total_vendido', y='nome', ax=ax, palette='viridis', hue='nome', legend=False)
    ax.set_title('Top 5 Produtos (Volume de Vendas)')
    ax.set_xlabel('Unidades Vendidas')
    ax.set_ylabel('')
    fig.tight_layout()

def plot_stock_levels(db_conn, fig):
    """Gera um gráfico de barras com os níveis de estoque."""
    fig.clear()
    ax = fig.add_subplot(111)
    query = "SELECT nome, quantidade, reorder_level FROM produtos WHERE reorder_level > 0 ORDER BY quantidade ASC LIMIT 7;"
    df = pd.read_sql_query(query, db_conn)
    if not df.empty:
        colors = ['#d9534f' if qty < reorder else '#5bc0de' for qty, reorder in zip(df['quantidade'], df['reorder_level'])]
        # CORREÇÃO APLICADA AQUI
        sns.barplot(data=df, x='quantidade', y='nome', ax=ax, palette=colors, hue='nome', legend=False)
    ax.set_title('Níveis de Estoque (Itens Mais Baixos)')
    ax.set_xlabel('Quantidade em Estoque')
    ax.set_ylabel('')
    fig.tight_layout()

def plot_purchases_by_supplier(db_conn, fig):
    """Gera um gráfico de pizza com o valor das compras por fornecedor."""
    fig.clear()
    ax = fig.add_subplot(111)
    query = """
    SELECT f.nome, SUM(c.preco_total) as total_comprado
    FROM compras c
    JOIN fornecedores f ON c.fornecedor_id = f.id
    GROUP BY f.nome
    ORDER BY total_comprado DESC;
    """
    df = pd.read_sql_query(query, db_conn)
    if not df.empty:
        ax.pie(df['total_comprado'], labels=df['nome'], autopct='%1.1f%%', startangle=90)
    ax.set_title('Compras por Fornecedor (Valor Total)')
    fig.tight_layout()