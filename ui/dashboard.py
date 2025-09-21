# ui/dashboard.py
import tkinter as tk
from tkinter import ttk

class DashboardTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, padding=8)
        self.db = db
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        ttk.Label(self, text='📊 Dashboard', font=('Segoe UI', 14)).pack(anchor='w')
        self.lbl_rev = ttk.Label(self, text='Receita (30d): R$ 0.00'); self.lbl_rev.pack(anchor='w', pady=2)
        self.lbl_cogs = ttk.Label(self, text='COGS (estimado 30d): R$ 0.00'); self.lbl_cogs.pack(anchor='w', pady=2)
        self.lbl_stock = ttk.Label(self, text='Valor estoque: R$ 0.00'); self.lbl_stock.pack(anchor='w', pady=2)
        self.btn_refresh = ttk.Button(self, text='Atualizar', command=self.refresh); self.btn_refresh.pack(anchor='e', pady=6)

    def refresh(self):
        stats = self.db.compute_sales_and_cogs()
        stock_val = self.db.total_stock_value()
        self.lbl_rev.config(text=f"Receita (30d): R$ {stats['revenue']:.2f}")
        self.lbl_cogs.config(text=f"COGS (estimado 30d): R$ {stats['cogs_est']:.2f}")
        self.lbl_stock.config(text=f"Valor estoque: R$ {stock_val:.2f}")
