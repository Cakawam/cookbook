# ui/app.py
import tkinter as tk
from tkinter import ttk
from db.db_manager import DBManager
from ui.dashboard import DashboardTab
from ui.compras import ComprasTab
from ui.estoque import EstoqueTab
from ui.receitas import ReceitasTab
from ui.producao import ProducaoTab
from ui.vendas import VendasTab

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Sistema Culinário — Gestão')
        self.geometry('1100x720')
        self.minsize(1000,650)

        self.db = DBManager()

        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('.', font=('Segoe UI', 10))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=6, pady=6)

        self.frame_dashboard = DashboardTab(self.notebook, self.db)
        self.frame_compras = ComprasTab(self.notebook, self.db)
        self.frame_estoque = EstoqueTab(self.notebook, self.db)
        self.frame_receitas = ReceitasTab(self.notebook, self.db)
        self.frame_producao = ProducaoTab(self.notebook, self.db)
        self.frame_vendas = VendasTab(self.notebook, self.db)

        self.notebook.add(self.frame_dashboard, text='Dashboard')
        self.notebook.add(self.frame_compras, text='Compras')
        self.notebook.add(self.frame_estoque, text='Estoque')
        self.notebook.add(self.frame_receitas, text='Receitas')
        self.notebook.add(self.frame_producao, text='Produção')
        self.notebook.add(self.frame_vendas, text='Vendas')
