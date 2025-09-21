# ui/compras.py
import tkinter as tk
from tkinter import ttk, messagebox
from utils.unit_converter import UnitConverter
from datetime import datetime

class ComprasTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, padding=8)
        self.db = db
        self._build_ui()
        self.refresh_list()

    def _build_ui(self):
        ttk.Label(self, text='🛒 Compras', font=('Segoe UI', 14)).pack(anchor='w')
        form = ttk.Frame(self); form.pack(fill='x', padx=6, pady=6)
        ttk.Label(form, text='Produto:').grid(row=0, column=0); self.ent_produto = ttk.Entry(form, width=30); self.ent_produto.grid(row=0,column=1)
        ttk.Label(form, text='Quantidade:').grid(row=1, column=0); self.ent_qtd = ttk.Entry(form, width=12); self.ent_qtd.grid(row=1,column=1)
        self.cmb_un = ttk.Combobox(form, values=UnitConverter.common_units(), width=6); self.cmb_un.set('kg'); self.cmb_un.grid(row=1,column=2)
        ttk.Label(form, text='Preço total (R$):').grid(row=2,column=0); self.ent_preco = ttk.Entry(form, width=12); self.ent_preco.grid(row=2,column=1)
        ttk.Label(form, text='Data (DD/MM/AAAA):').grid(row=3,column=0); self.ent_data = ttk.Entry(form, width=12); self.ent_data.insert(0, datetime.now().strftime("%d/%m/%Y")); self.ent_data.grid(row=3,column=1)
        ttk.Label(form, text='Lote:').grid(row=4,column=0); self.ent_lote = ttk.Entry(form, width=12); self.ent_lote.grid(row=4,column=1)
        ttk.Label(form, text='Validade (DD/MM/AAAA):').grid(row=4,column=2); self.ent_validade = ttk.Entry(form, width=12); self.ent_validade.grid(row=4,column=3)
        ttk.Button(form, text='Registrar Compra', command=self.on_add_compra).grid(row=5,column=0, pady=8)
        ttk.Button(form, text='Atualizar Lista', command=self.refresh_list).grid(row=5,column=1, padx=6)

        self.tree = ttk.Treeview(self, columns=('produto','quantidade','unidade','preco','data','lote'), show='headings')
        for c in ('produto','quantidade','unidade','preco','data','lote'):
            self.tree.heading(c, text=c.capitalize())
        self.tree.pack(fill='both', expand=True, padx=6, pady=6)

    def on_add_compra(self):
        produto = self.ent_produto.get().strip()
        if not produto:
            messagebox.showwarning('Erro','Informe o nome do produto'); return
        try:
            qtd = float(self.ent_qtd.get())
        except Exception:
            messagebox.showwarning('Erro','Quantidade inválida'); return
        unidade = self.cmb_un.get()
        try:
            preco = float(self.ent_preco.get())
        except Exception:
            messagebox.showwarning('Erro','Preço inválido'); return
        data = self.ent_data.get() or None
        lote = self.ent_lote.get().strip() or None
        validade = self.ent_validade.get().strip() or None
        try:
            self.db.add_compra(produto, qtd, unidade, preco, data, lote=lote, validade=validade)
            messagebox.showinfo('Sucesso','Compra registrada')
            self.refresh_list()
        except Exception as e:
            messagebox.showerror('Erro', str(e))

    def refresh_list(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        rows = self.db.get_compras_recent(months=6)
        for r in rows:
            fornecedor = r['fornecedor_nome'] if 'fornecedor_nome' in r.keys() else ''
            try:
                qtd_s = f"{float(r['quantidade'] or 0):.4f}"
            except Exception:
                qtd_s = str(r['quantidade'] or '')
            preco_s = f"{float(r['preco_total'] or 0):.2f}"
            self.tree.insert('', 'end', values=(r['produto_nome'], qtd_s, r['unidade'] or '', preco_s, r['data'], r['lote']))
