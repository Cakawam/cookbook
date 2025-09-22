# Salve este arquivo como population.py

import sqlite3
import random
from datetime import date, timedelta

DB_FILE = "sistema_culinario.db"

def limpar_dados_antigos(conn):
    """Apaga todos os dados das tabelas para evitar duplicatas ao rodar o script novamente."""
    cursor = conn.cursor()
    print("🧹 Limpando dados antigos...")
    
    tabelas = [
        "wastes", "stock_adjustments", "despesas", "vendas", "producoes",
        "receita_ingredientes", "lotes", "compras", "receitas",
        "produtos", "fornecedores"
    ]
    
    for tabela in tabelas:
        try:
            cursor.execute(f"DELETE FROM {tabela};")
            print(f"  - Dados da tabela '{tabela}' removidos.")
        except sqlite3.OperationalError as e:
            print(f"Aviso: Não foi possível limpar a tabela {tabela}. Erro: {e}")
            
    conn.commit()
    print("Limpeza concluída.\n")

def popular_banco():
    """Conecta ao banco de dados e insere dados de exemplo."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    limpar_dados_antigos(conn)

    print("🌱 Começando a popular o banco de dados...")

    # --- 1. Dados Base ---
    fornecedores = [
        ('Distribuidora Sabor Real', 'compras@saborreal.com'),
        ('Fazenda Orgânica Sol Nascente', 'contato@fazendasol.com'),
        ('Embalagens & Cia', 'vendas@embalagenscia.com')
    ]
    cursor.executemany("INSERT INTO fornecedores (nome, contato) VALUES (?, ?)", fornecedores)
    print("✅ Fornecedores inseridos.")

    produtos = [
        ('Farinha de Trigo', 'kg', 10.0, 5.50, 5.0), ('Ovos Orgânicos', 'un', 30.0, 0.80, 12.0),
        ('Chocolate Amargo 70%', 'kg', 5.0, 45.0, 2.0), ('Leite Integral', 'L', 12.0, 4.20, 6.0),
        ('Manteiga sem Sal', 'kg', 4.0, 35.0, 1.0), ('Caixa para Bolo (un)', 'un', 50.0, 1.50, 20.0),
        ('Bolo de Chocolate Pronto', 'un', 0.0, 0.0, 5.0)
    ]
    cursor.executemany("INSERT INTO produtos (nome, unidade_base, quantidade, ultima_compra_unitaria, reorder_level) VALUES (?, ?, ?, ?, ?)", produtos)
    print("✅ Produtos inseridos.")

    receitas = [('Bolo de Chocolate', 12.0, 'fatias'), ('Massa de Panqueca', 8.0, 'un')]
    cursor.executemany("INSERT INTO receitas (nome, rendimento, unidade_resultado) VALUES (?, ?, ?)", receitas)
    print("✅ Receitas inseridas.")

    ingredientes_receita = [
        (1, 1, 0.5, 'kg', 0.5), (1, 2, 3.0, 'un', 3.0), (1, 3, 0.3, 'kg', 0.3),
        (2, 1, 0.2, 'kg', 0.2), (2, 2, 2.0, 'un', 2.0), (2, 4, 0.3, 'L', 0.3),
    ]
    cursor.executemany("INSERT INTO receita_ingredientes (receita_id, produto_id, quantidade_usada, unidade, quantidade_base) VALUES (?, ?, ?, ?, ?)", ingredientes_receita)
    print("✅ Ingredientes das receitas inseridos.")
    
    # --- 2. Dados Dinâmicos ---
    print("\n🔄 Simulando atividades dos últimos 90 dias...")
    hoje = date.today()
    for i in range(90, -1, -1):
        data_atual = hoje - timedelta(days=i)
        data_str = data_atual.strftime('%Y-%m-%d')

        if i % 5 == 0:
            produto_id, fornecedor_id = random.randint(1, 6), random.randint(1, 3)
            quantidade = round(random.uniform(5, 20), 2)
            preco_total = round(quantidade * random.uniform(2, 10), 2)
            lote = f"L{random.randint(1000, 9999)}"
            validade = (data_atual + timedelta(days=180)).strftime('%Y-%m-%d')
            cursor.execute("INSERT INTO compras (produto_id, fornecedor_id, quantidade_base, preco_total, data, lote, validade) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (produto_id, fornecedor_id, quantidade, preco_total, data_str, lote, validade))
            cursor.execute("INSERT INTO lotes (produto_id, quantidade_base, data_compra, data_validade, lote) VALUES (?, ?, ?, ?, ?)",
                           (produto_id, quantidade, data_str, validade, lote))

        if i % 3 == 0:
            cursor.execute("INSERT INTO producoes (receita_id, quantidade_produzida, data) VALUES (?, ?, ?)",
                           (1, random.choice([1, 2]), data_str))

        if random.random() > 0.3:
            # AQUI ESTÁ A CORREÇÃO PRINCIPAL
            quantidade_venda = random.randint(1, 5) # Define a quantidade
            cursor.execute(
                "INSERT INTO vendas (produto_id, quantidade, quantidade_base, preco_unitario, data, local) VALUES (?, ?, ?, ?, ?, ?)",
                (7, quantidade_venda, quantidade_venda, round(random.uniform(8.50, 12.00), 2), data_str, 'Balcão')
            )
    
    print("✅ Compras, produções e vendas simuladas.")

    # --- 3. Dados Pontuais ---
    despesas = [
        ((hoje - timedelta(days=20)).strftime('%Y-%m-%d'), 'Conta de Luz', 350.45),
        ((hoje - timedelta(days=15)).strftime('%Y-%m-%d'), 'Marketing Digital', 200.00),
        ((hoje - timedelta(days=5)).strftime('%Y-%m-%d'), 'Aluguel', 1500.00)
    ]
    cursor.executemany("INSERT INTO despesas (data, descricao, valor) VALUES (?, ?, ?)", despesas)
    print("✅ Despesas inseridas.")

    perdas = [(2, 2.0, 2.0, 'un', 'Ovos quebraram na entrega', (hoje - timedelta(days=10)).strftime('%Y-%m-%d'))]
    cursor.executemany("INSERT INTO wastes (produto_id, quantidade, quantidade_base, unidade, motivo, data) VALUES (?, ?, ?, ?, ?, ?)", perdas)
    print("✅ Registros de perdas inseridos.")

    ajuste = (1, (hoje - timedelta(days=2)).strftime('%Y-%m-%d'), 10.0, 9.8, 'Ajuste de contagem')
    cursor.execute("INSERT INTO stock_adjustments (produto_id, data, before_qty, after_qty, motivo) VALUES (?, ?, ?, ?, ?)", ajuste)
    print("✅ Ajustes de estoque inseridos.")

    conn.commit()
    conn.close()
    print("\n🎉 Banco de dados populado com sucesso!")


if __name__ == '__main__':
    popular_banco()