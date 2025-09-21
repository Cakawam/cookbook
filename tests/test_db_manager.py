# tests/test_db_manager.py
import pytest
from db.db_manager import DBManager
from datetime import datetime

@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "test_sistema.db")
    dbm = DBManager(db_path=path)
    return dbm

def test_compra_and_lote_and_stock(db):
    pid = db.add_compra("Farinha", 10, "kg", 200.0, datetime.now().strftime("%d/%m/%Y"), lote="L001", validade=None)
    prods = db.get_produtos()
    assert any(p['nome']=="Farinha" for p in prods)
    p = next(p for p in prods if p['nome']=="Farinha")
    assert p['quantidade'] > 0

def test_consumo_venda_waste(db):
    db.add_compra("Ovo", 30, "un", 15.0, datetime.now().strftime("%d/%m/%Y"))
    prod = next(p for p in db.get_produtos() if p['nome']=="Ovo")
    db.add_venda(prod['id'], 5, "un", 1.5, datetime.now().strftime("%d/%m/%Y"), local="loja")
    db.add_waste(prod['id'], 2, "un", motivo="quebrado", data_str=datetime.now().strftime("%d/%m/%Y"))
    p2 = db.get_produto(prod['id'])
    assert p2['quantidade'] <= prod['quantidade'] - 7 + 1e-6

def test_receita_producao_cost(db):
    db.add_compra("Açúcar", 5, "kg", 100.0, datetime.now().strftime("%d/%m/%Y"))
    db.add_compra("Manteiga", 2, "kg", 120.0, datetime.now().strftime("%d/%m/%Y"))
    rid = db.add_receita("Bolo", 10, "un")
    db.add_receita_ingrediente(rid, "Açúcar", 0.5, "kg")
    db.add_receita_ingrediente(rid, "Manteiga", 0.2, "kg")
    cost = db.compute_recipe_cost(rid)
    assert cost['total_cost'] > 0
    db.add_producao(rid, 10, datetime.now().strftime("%d/%m/%Y"))
    prods = db.get_produtos()
    assert any(p['nome']=="Bolo" for p in prods)
