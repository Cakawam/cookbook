# ui/vendas.py
import tkinter as tk
from tkinter import ttk, messagebox
from utils.unit_converter import UnitConverter

class VendasTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, padding=8)
        self.db = db
        self.produtos = []
        self._build_ui()
        self.refresh_products()
        self.refresh_list()

    def _build_ui(self):
        ttk.Label(self, text='💰 Vendas', font=('Segoe UI', 14)).pack(anchor='w')
        frm = ttk.Frame(self); frm.pack(fill='x', padx=6, pady=6)
        ttk.Label(frm, text='Produto:').grid(row=0,column=0); self.cmb_prod = ttk.Combobox(frm, values=[], width=40); self.cmb_prod.grid(row=0,column=1)
        ttk.Label(frm, text='Qtd:').grid(row=1,column=0); self.ent_qtd = ttk.Entry(frm, width=12); self.ent_qtd.grid(row=1,column=1)
        ttk.Label(frm, text='Unid:').grid(row=1,column=2); self.cmb_un = ttk.Combobox(frm, values=UnitConverter.common_units(), width=6); self.cmb_un.set('un'); self.cmb_un.grid(row=1,column=3)
        ttk.Label(frm, text='Preço unit. (R$):').grid(row=2,column=0); self.ent_preco = ttk.Entry(frm, width=12); self.ent_preco.grid(row=2,column=1)
        ttk.Label(frm, text='Data (DD/MM/AAAA opt):').grid(row=3,column=0); self.ent_data = ttk.Entry(frm, width=12); self.ent_data.grid(row=3,column=1)
        ttk.Button(frm, text='Registrar venda', command=self.on_venda).grid(row=4,column=0, columnspan=2, pady=8)

        ttk.Label(self, text='Produtos cadastrados (duplo-clique para usar):').pack(anchor='w', padx=6)
        cols = ('nome','qtd','un_base','preco_unit')
        self.prod_tree = ttk.Treeview(self, columns=cols, show='headings', height=6)
        for c,t in [('nome','Produto'),('qtd','Qtd (base)'),('un_base','Unid base'),('preco_unit','Últ. preço')]:
            self.prod_tree.heading(c, text=t)
        self.prod_tree.pack(fill='x', padx=6, pady=(0,6))
        self.prod_tree.bind('<Double-1>', self.on_prod_tree_double)

        self.vendas_tree = ttk.Treeview(self, columns=('produto','qtd','un','preco','data'), show='headings')
        for c,t in [('produto','Produto'),('qtd','Quantidade'),('un','Unidade'),('preco','Preço unit.'),('data','Data')]:
            self.vendas_tree.heading(c, text=t)
        self.vendas_tree.pack(fill='both', expand=True, padx=6, pady=6)

    def refresh_products(self):
        self.produtos = list(self.db.get_produtos())
        names = [p['nome'] for p in self.produtos]
        self.cmb_prod['values'] = names
        for r in self.prod_tree.get_children(): self.prod_tree.delete(r)
        for p in self.produtos:
            last_price = p['ultima_compra_unitaria'] or 0
            self.prod_tree.insert('', 'end', iid=str(p['id']), values=(p['nome'], f"{p['quantidade']:.4f}", p['unidade_base'], f"{float(last_price):.4f}"))

    def on_prod_tree_double(self, event):
        sel = self.prod_tree.selection()
        if not sel:
            return
        pid = int(sel[0])
        prod = next((p for p in self.produtos if p['id'] == pid), None)
        if not prod:
            return
        self.cmb_prod.set(prod['nome'])
        last_price = prod['ultima_compra_unitaria'] or 0
        if last_price:
            self.ent_preco.delete(0,'end'); self.ent_preco.insert(0, f"{last_price:.2f}")
        self.ent_qtd.focus_set()

    def on_venda(self):
        nome = self.cmb_prod.get().strip()
        if not nome:
            messagebox.showwarning('Erro','Selecione produto'); return
        prod = next((p for p in self.produtos if p['nome'] == nome), None)
        if not prod:
            messagebox.showerror('Erro','Produto não encontrado'); return
        try:
            qtd = float(self.ent_qtd.get())
        except Exception:
            messagebox.showwarning('Erro','Qtd inválida'); return
        unidade = self.cmb_un.get()
        try:
            preco = float(self.ent_preco.get())
        except Exception:
            messagebox.showwarning('Erro','Preço inválido'); return
        data = self.ent_data.get() or None
        try:
            self.db.add_venda(prod['id'], qtd, unidade, preco, data, local='loja')
            messagebox.showinfo('Ok','Venda registrada')
            self.refresh_products()
            self.refresh_list()
        except Exception as e:
            messagebox.showerror('Erro', str(e))

    def refresh_list(self):
        for r in self.vendas_tree.get_children(): self.vendas_tree.delete(r)
        rows = self.db.get_vendas_por_data(self.ent_data.get() or None)
        for r in rows:
            self.vendas_tree.insert('', 'end', values=(r['nome'], f"{float(r['quantidade']):.4f}", r['quantidade_base'], f"{float(r['preco_unitario']):.2f}", r['data']))
