# db/db_manager.py
import sqlite3
import os
import csv
import math
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from utils.unit_converter import UnitConverter
from utils.date_helpers import parse_date_input, ISO_DATE_FMT

DB_FILE = 'sistema_culinario.db'

class DBManager:
    def __init__(self, db_path=DB_FILE):
        first_time = not os.path.exists(db_path)
        self.conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cur = self.conn.cursor()
        cur.executescript('''
        CREATE TABLE IF NOT EXISTS fornecedores (
            id INTEGER PRIMARY KEY,
            nome TEXT UNIQUE NOT NULL,
            contato TEXT
        );
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY,
            nome TEXT UNIQUE NOT NULL,
            unidade_base TEXT NOT NULL,
            quantidade REAL DEFAULT 0,
            ultima_compra_unitaria REAL DEFAULT 0,
            reorder_level REAL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY,
            produto_id INTEGER,
            fornecedor_id INTEGER,
            quantidade REAL,
            unidade TEXT,
            quantidade_base REAL,
            preco_total REAL,
            preco_unitario_base REAL,
            data TEXT,
            lote TEXT,
            validade TEXT,
            FOREIGN KEY(produto_id) REFERENCES produtos(id),
            FOREIGN KEY(fornecedor_id) REFERENCES fornecedores(id)
        );
        CREATE TABLE IF NOT EXISTS lotes (
            id INTEGER PRIMARY KEY,
            produto_id INTEGER,
            quantidade_base REAL,
            data_compra TEXT,
            data_validade TEXT,
            lote TEXT,
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        );
        CREATE TABLE IF NOT EXISTS receitas (
            id INTEGER PRIMARY KEY,
            nome TEXT UNIQUE NOT NULL,
            rendimento REAL NOT NULL,
            unidade_resultado TEXT DEFAULT 'un'
        );
        CREATE TABLE IF NOT EXISTS receita_ingredientes (
            id INTEGER PRIMARY KEY,
            receita_id INTEGER,
            produto_id INTEGER,
            quantidade_usada REAL,
            unidade TEXT,
            quantidade_base REAL,
            FOREIGN KEY(receita_id) REFERENCES receitas(id),
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        );
        CREATE TABLE IF NOT EXISTS producoes (
            id INTEGER PRIMARY KEY,
            receita_id INTEGER,
            quantidade_produzida REAL,
            data TEXT,
            FOREIGN KEY(receita_id) REFERENCES receitas(id)
        );
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY,
            produto_id INTEGER,
            quantidade REAL,
            quantidade_base REAL,
            preco_unitario REAL,
            data TEXT,
            local TEXT,
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        );
        CREATE TABLE IF NOT EXISTS despesas (
            id INTEGER PRIMARY KEY,
            data TEXT,
            descricao TEXT,
            valor REAL
        );
        CREATE TABLE IF NOT EXISTS stock_adjustments (
            id INTEGER PRIMARY KEY,
            produto_id INTEGER,
            data TEXT,
            before_qty REAL,
            after_qty REAL,
            motivo TEXT
        );
        CREATE TABLE IF NOT EXISTS wastes (
            id INTEGER PRIMARY KEY,
            produto_id INTEGER,
            quantidade REAL,
            quantidade_base REAL,
            unidade TEXT,
            motivo TEXT,
            data TEXT
        );
        ''')
        self.conn.commit()

    # ---------------- Suppliers ----------------
    def add_or_get_fornecedor(self, nome, contato=None):
        cur = self.conn.cursor()
        cur.execute('SELECT id FROM fornecedores WHERE nome = ?', (nome,))
        r = cur.fetchone()
        if r:
            return r['id']
        cur.execute('INSERT INTO fornecedores (nome, contato) VALUES (?,?)', (nome, contato))
        self.conn.commit()
        return cur.lastrowid

    def get_fornecedores(self):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM fornecedores ORDER BY nome')
        return cur.fetchall()

    # ---------------- Produtos ----------------
    def add_or_get_produto(self, nome, unidade_base='un'):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM produtos WHERE nome = ?', (nome,))
        row = cur.fetchone()
        if row:
            return row['id']
        cur.execute('INSERT INTO produtos (nome, unidade_base) VALUES (?,?)', (nome, unidade_base))
        self.conn.commit()
        return cur.lastrowid

    def get_produtos(self, like=None):
        cur = self.conn.cursor()
        if like:
            cur.execute('SELECT * FROM produtos WHERE nome LIKE ? ORDER BY nome', (f'%{like}%',))
        else:
            cur.execute('SELECT * FROM produtos ORDER BY nome')
        return cur.fetchall()

    def get_produto(self, produto_id):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,))
        return cur.fetchone()

    def set_produto_reorder(self, produto_id, reorder_level):
        cur = self.conn.cursor()
        cur.execute('UPDATE produtos SET reorder_level = ? WHERE id = ?', (reorder_level, produto_id))
        self.conn.commit()

    # ---------------- Compras e lotes ----------------
    def add_compra(self, produto_nome, quantidade, unidade, preco_total, data_str, lote=None, validade=None, fornecedor_nome=None):
        cur = self.conn.cursor()
        try:
            data_iso = parse_date_input(data_str)
            validade_iso = parse_date_input(validade) if (validade and str(validade).strip()) else None
            quantidade_base, unidade_base = UnitConverter.to_base(quantidade, unidade)
            produto_id = self.add_or_get_produto(produto_nome, unidade_base)
            fornecedor_id = None
            if fornecedor_nome:
                fornecedor_id = self.add_or_get_fornecedor(fornecedor_nome)
            preco_unitario_base = 0
            if quantidade_base > 0:
                try:
                    preco_dec = (Decimal(str(preco_total)) / Decimal(str(quantidade_base))).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
                    preco_unitario_base = float(preco_dec)
                except Exception:
                    preco_unitario_base = float(preco_total) / float(quantidade_base)
            cur.execute('INSERT INTO compras (produto_id, fornecedor_id, quantidade, unidade, quantidade_base, preco_total, preco_unitario_base, data, lote, validade) VALUES (?,?,?,?,?,?,?,?,?,?)',
                        (produto_id, fornecedor_id, quantidade, unidade, quantidade_base, preco_total, preco_unitario_base, data_iso, lote, validade_iso))
            compra_id = cur.lastrowid
            # criar lote
            cur.execute('INSERT INTO lotes (produto_id, quantidade_base, data_compra, data_validade, lote) VALUES (?,?,?,?,?)', (produto_id, quantidade_base, data_iso, validade_iso, lote))
            # atualizar quantidade do produto (soma lotes)
            cur.execute('SELECT SUM(quantidade_base) as total FROM lotes WHERE produto_id = ?', (produto_id,))
            total = cur.fetchone()['total'] or 0
            cur.execute('UPDATE produtos SET quantidade = ?, ultima_compra_unitaria = ? WHERE id = ?', (total, preco_unitario_base, produto_id))
            self.conn.commit()
            return compra_id
        except Exception:
            self.conn.rollback()
            raise

    def get_compras_recent(self, months=3):
        cur = self.conn.cursor()
        since = (datetime.now() - timedelta(days=30*months)).strftime(ISO_DATE_FMT)
        cur.execute('SELECT c.*, p.nome as produto_nome, f.nome as fornecedor_nome FROM compras c LEFT JOIN produtos p ON c.produto_id=p.id LEFT JOIN fornecedores f ON c.fornecedor_id = f.id WHERE date(c.data) >= ? ORDER BY c.data DESC', (since,))
        return cur.fetchall()

    def get_last_price_for_produto(self, produto_id):
        cur = self.conn.cursor()
        cur.execute('SELECT preco_unitario_base FROM compras WHERE produto_id = ? ORDER BY id DESC LIMIT 1', (produto_id,))
        r = cur.fetchone()
        return r['preco_unitario_base'] if r and r['preco_unitario_base'] is not None else 0

    def get_average_price_last_months(self, produto_id, months=3):
        cur = self.conn.cursor()
        since = (datetime.now() - timedelta(days=30*months)).strftime(ISO_DATE_FMT)
        cur.execute('SELECT AVG(preco_unitario_base) as media FROM compras WHERE produto_id = ? AND date(data) >= ?', (produto_id, since))
        r = cur.fetchone()
        return r['media'] if r and r['media'] is not None else 0

    # ---------------- Lotes consumption (FEFO/FIFO) ----------------
    def _ensure_lotes_exist_for_produto(self, produto_id):
        cur = self.conn.cursor()
        cur.execute('SELECT COUNT(*) as cnt FROM lotes WHERE produto_id = ?', (produto_id,))
        if cur.fetchone()['cnt'] == 0:
            prod = self.get_produto(produto_id)
            if prod and prod['quantidade'] > 0:
                cur.execute('INSERT INTO lotes (produto_id, quantidade_base, data_compra, data_validade, lote) VALUES (?,?,?,?,?)', (produto_id, prod['quantidade'], None, None, 'legacy'))
                self.conn.commit()

    def consume_from_lotes(self, produto_id, quantidade_base, motivo=None):
        if quantidade_base <= 0:
            return
        self._ensure_lotes_exist_for_produto(produto_id)
        cur = self.conn.cursor()
        try:
            cur.execute('SELECT SUM(quantidade_base) as total FROM lotes WHERE produto_id = ?', (produto_id,))
            before_total = float(cur.fetchone()['total'] or 0)
            need = float(quantidade_base)
            cur.execute('SELECT id, quantidade_base FROM lotes WHERE produto_id = ? AND quantidade_base > 0 ORDER BY CASE WHEN data_validade IS NULL THEN 1 ELSE 0 END, data_validade ASC, data_compra ASC', (produto_id,))
            rows = cur.fetchall()
            for r in rows:
                if need <= 1e-9:
                    break
                take = min(r['quantidade_base'], need)
                cur.execute('UPDATE lotes SET quantidade_base = quantidade_base - ? WHERE id = ?', (take, r['id']))
                need -= take
            if need > 1e-6:
                self.conn.rollback()
                raise ValueError('Estoque insuficiente (por lotes). Necessário: {:.4f}'.format(quantidade_base))
            cur.execute('SELECT SUM(quantidade_base) as total FROM lotes WHERE produto_id = ?', (produto_id,))
            after_total = float(cur.fetchone()['total'] or 0)
            cur.execute('UPDATE produtos SET quantidade = ? WHERE id = ?', (after_total, produto_id))
            cur.execute('INSERT INTO stock_adjustments (produto_id, data, before_qty, after_qty, motivo) VALUES (?,?,?,?,?)', (produto_id, datetime.now().strftime(ISO_DATE_FMT), before_total, after_total, motivo or 'consumo'))
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    # ---------------- Waste tracking ----------------
    def add_waste(self, produto_id, quantidade, unidade, motivo, data_str=None):
        cur = self.conn.cursor()
        try:
            data_iso = parse_date_input(data_str or datetime.now().strftime('%d/%m/%Y'))
            quantidade_base, _ = UnitConverter.to_base(quantidade, unidade)
            prod = self.get_produto(produto_id)
            if not prod:
                raise ValueError('Produto não encontrado')
            if (prod['quantidade'] or 0) < quantidade_base - 1e-9:
                raise ValueError('Estoque insuficiente para registrar desperdício')
            self.consume_from_lotes(produto_id, quantidade_base, motivo='waste:'+ (motivo or ''))
            cur.execute('INSERT INTO wastes (produto_id, quantidade, quantidade_base, unidade, motivo, data) VALUES (?,?,?,?,?,?)', (produto_id, quantidade, quantidade_base, unidade, motivo, data_iso))
            self.conn.commit()
            return cur.lastrowid
        except Exception:
            self.conn.rollback()
            raise

    def get_waste_recent(self, days=30):
        cur = self.conn.cursor()
        since = (datetime.now() - timedelta(days=days)).strftime(ISO_DATE_FMT)
        cur.execute('SELECT w.*, p.nome FROM wastes w JOIN produtos p ON w.produto_id=p.id WHERE date(w.data) >= ? ORDER BY w.data DESC', (since,))
        return cur.fetchall()

    # ---------------- Receitas / ingredientes ----------------
    def add_receita(self, nome, rendimento, unidade_resultado='un'):
        cur = self.conn.cursor()
        try:
            # verifica duplicado
            cur.execute('SELECT id FROM receitas WHERE nome = ?', (nome,))
            if cur.fetchone():
                raise ValueError(f"A receita '{nome}' já existe")
            cur.execute('INSERT INTO receitas (nome, rendimento, unidade_resultado) VALUES (?,?,?)', (nome, rendimento, unidade_resultado))
            self.conn.commit()
            return cur.lastrowid
        except Exception:
            self.conn.rollback()
            raise

    def update_receita(self, receita_id, nome, rendimento):
        cur = self.conn.cursor()
        cur.execute('UPDATE receitas SET nome=?, rendimento=? WHERE id=?', (nome, rendimento, receita_id))
        self.conn.commit()

    def delete_receita(self, receita_id):
        cur = self.conn.cursor()
        cur.execute('DELETE FROM receita_ingredientes WHERE receita_id=?', (receita_id,))
        cur.execute('DELETE FROM receitas WHERE id=?', (receita_id,))
        self.conn.commit()

    def add_receita_ingrediente(self, receita_id, produto_nome, quantidade, unidade):
        cur = self.conn.cursor()
        try:
            quantidade_base, unidade_base = UnitConverter.to_base(quantidade, unidade)
            produto_id = self.add_or_get_produto(produto_nome, unidade_base)
            cur.execute('INSERT INTO receita_ingredientes (receita_id, produto_id, quantidade_usada, unidade, quantidade_base) VALUES (?,?,?,?,?)', (receita_id, produto_id, quantidade, unidade, quantidade_base))
            self.conn.commit()
            return cur.lastrowid
        except Exception:
            self.conn.rollback()
            raise

    def get_receitas(self):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM receitas ORDER BY nome')
        return cur.fetchall()

    def get_receita_ingredientes(self, receita_id):
        cur = self.conn.cursor()
        cur.execute('''SELECT ri.*, p.nome as produto_nome, p.unidade_base as produto_unidade_base, p.quantidade as produto_qtd_atual, p.ultima_compra_unitaria as preco_unit_base, p.reorder_level as reorder_level
                       FROM receita_ingredientes ri JOIN produtos p ON ri.produto_id = p.id WHERE ri.receita_id = ?''', (receita_id,))
        return cur.fetchall()

    def compute_recipe_cost(self, receita_id, use_avg_months=3):
        cur = self.conn.cursor()
        cur.execute('SELECT rendimento FROM receitas WHERE id = ?', (receita_id,))
        r = cur.fetchone()
        if not r:
            raise ValueError('Receita não encontrada')
        rendimento = float(r['rendimento'])
        total_cost = 0.0
        ingredientes = self.get_receita_ingredientes(receita_id)
        for ing in ingredientes:
            preco = ing['preco_unit_base'] or 0
            if preco == 0:
                media = self.get_average_price_last_months(ing['produto_id'], months=use_avg_months)
                preco = media or 0
            total_cost += float(ing['quantidade_base'] or 0) * float(preco or 0)
        cost_per_unit = total_cost / rendimento if rendimento else total_cost
        return {'total_cost': total_cost, 'cost_per_unit': cost_per_unit}

    # ---------------- Produção ----------------
    def add_producao(self, receita_id, quantidade_produzida, data_str):
        cur = self.conn.cursor()
        try:
            data_iso = parse_date_input(data_str)
            cur.execute('SELECT rendimento, nome, unidade_resultado FROM receitas WHERE id=?', (receita_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError('Receita não encontrada')
            rendimento = row['rendimento']
            receita_nome = row['nome']
            unidade_resultado = row['unidade_resultado'] or 'un'
            factor = float(quantidade_produzida) / float(rendimento) if rendimento else 1
            ingredientes = self.get_receita_ingredientes(receita_id)
            if not ingredientes:
                raise ValueError('Receita sem ingredientes')
            faltando = []
            for ing in ingredientes:
                need = ing['quantidade_base'] * factor
                if (ing['produto_qtd_atual'] or 0) < need - 1e-9:
                    faltando.append(f"{ing['produto_nome']} (necessário {need:.4f}, disponível {ing['produto_qtd_atual'] or 0:.4f})")
            if faltando:
                raise ValueError('Estoque insuficiente para produção:\n' + '\n'.join(faltando))
            # consumir insumos
            for ing in ingredientes:
                need = ing['quantidade_base'] * factor
                self.consume_from_lotes(ing['produto_id'], need, motivo=f'Produção {receita_nome}')
            # registrar produção e criar lote do produto final (nome da receita)
            cur.execute('INSERT INTO producoes (receita_id, quantidade_produzida, data) VALUES (?,?,?)', (receita_id, quantidade_produzida, data_iso))
            produto_id = self.add_or_get_produto(receita_nome, unidade_resultado)
            cur.execute('INSERT INTO lotes (produto_id, quantidade_base, data_compra, data_validade, lote) VALUES (?,?,?,?,?)', (produto_id, quantidade_produzida, data_iso, None, 'producao'))
            cur.execute('SELECT SUM(quantidade_base) as total FROM lotes WHERE produto_id = ?', (produto_id,))
            total = cur.fetchone()['total'] or 0
            cur.execute('UPDATE produtos SET quantidade = ? WHERE id = ?', (total, produto_id))
            cur.execute('INSERT INTO stock_adjustments (produto_id, data, before_qty, after_qty, motivo) VALUES (?,?,?,?,?)', (produto_id, data_iso, 0, total, 'producao'))
            self.conn.commit()
            return cur.lastrowid
        except Exception:
            self.conn.rollback()
            raise

    # ---------------- Vendas ----------------
    def add_venda(self, produto_id, quantidade, unidade, preco_unitario, data_str, local=None):
        cur = self.conn.cursor()
        try:
            data_iso = parse_date_input(data_str)
            quantidade_base, _ = UnitConverter.to_base(quantidade, unidade)
            prod = self.get_produto(produto_id)
            if not prod:
                raise ValueError('Produto não encontrado')
            if (prod['quantidade'] or 0) < quantidade_base - 1e-9:
                raise ValueError('Estoque insuficiente')
            self.consume_from_lotes(produto_id, quantidade_base, motivo='venda')
            cur.execute('INSERT INTO vendas (produto_id, quantidade, quantidade_base, preco_unitario, data, local) VALUES (?,?,?,?,?,?)', (produto_id, quantidade, quantidade_base, preco_unitario, data_iso, local))
            self.conn.commit()
            return cur.lastrowid
        except Exception:
            self.conn.rollback()
            raise

    def get_vendas_por_data(self, date_str):
        cur = self.conn.cursor()
        date_iso = parse_date_input(date_str)
        cur.execute('SELECT v.*, p.nome FROM vendas v JOIN produtos p ON v.produto_id = p.id WHERE date(v.data) = ? ORDER BY v.id', (date_iso,))
        return cur.fetchall()

    # ---------------- Relatórios / util ----------------
    def total_stock_value(self):
        cur = self.conn.cursor()
        cur.execute('SELECT SUM(p.quantidade * COALESCE(p.ultima_compra_unitaria,0)) as valor FROM produtos p')
        r = cur.fetchone()
        return float(r['valor'] or 0)

    def lots_expiring_within(self, days=7):
        cur = self.conn.cursor()
        limit_date = (datetime.now() + timedelta(days=days)).strftime(ISO_DATE_FMT)
        cur.execute('SELECT l.*, p.nome FROM lotes l JOIN produtos p ON l.produto_id=p.id WHERE l.data_validade IS NOT NULL AND date(l.data_validade) <= ? AND l.quantidade_base>0 ORDER BY l.data_validade ASC', (limit_date,))
        return cur.fetchall()

    def generate_reorder_csv(self, filename):
        cur = self.conn.cursor()
        cur.execute('SELECT id,nome,quantidade,reorder_level,unidade_base FROM produtos WHERE reorder_level > 0 AND quantidade < reorder_level ORDER BY nome')
        rows = cur.fetchall()
        if not rows:
            return False
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['produto_id','nome','quantidade_atual','reorder_level','sugerido_para_compra','unidade_base'])
            for r in rows:
                suggested = max(math.ceil((r['reorder_level'] * 2) - r['quantidade']), 0)
                writer.writerow([r['id'], r['nome'], r['quantidade'], r['reorder_level'], suggested, r['unidade_base']])
        return True

    def export_table_csv(self, table, filename):
        cur = self.conn.cursor()
        cur.execute(f'SELECT * FROM {table}')
        rows = cur.fetchall()
        if not rows:
            return False
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(rows[0].keys())
            for r in rows:
                writer.writerow([r[k] for k in r.keys()])
        return True

    def compute_sales_and_cogs(self, start_date=None, end_date=None):
        cur = self.conn.cursor()
        if start_date:
            s = parse_date_input(start_date)
        else:
            s = (datetime.now() - timedelta(days=30)).strftime(ISO_DATE_FMT)
        if end_date:
            e = parse_date_input(end_date)
        else:
            e = datetime.now().strftime(ISO_DATE_FMT)
        cur.execute('''
            SELECT 
                SUM(v.preco_unitario * v.quantidade) as revenue,
                SUM(v.quantidade_base * COALESCE(p.ultima_compra_unitaria,0)) as cogs
            FROM vendas v
            JOIN produtos p ON v.produto_id=p.id
            WHERE date(v.data) BETWEEN ? AND ?
        ''', (s, e))
        r = cur.fetchone()
        return {'revenue': float(r['revenue'] or 0), 'cogs_est': float(r['cogs'] or 0)}
