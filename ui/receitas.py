# ui/receitas.py
import tkinter as tk
from tkinter import ttk, messagebox
from utils.unit_converter import UnitConverter

class ReceitasTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, padding=8)
        self.db = db
        self.current_items = []  # list of (produto_nome, quantidade, unidade)
        self._build_ui()
        self.refresh_recipes()

    def _build_ui(self):
        ttk.Label(self, text='📜 Receitas', font=('Segoe UI', 14)).pack(anchor='w')
        frm = ttk.Frame(self); frm.pack(fill='x', padx=6, pady=6)
        ttk.Label(frm, text='Nome:').grid(row=0,column=0); self.ent_nome = ttk.Entry(frm, width=30); self.ent_nome.grid(row=0,column=1)
        ttk.Label(frm, text='Rendimento:').grid(row=0,column=2); self.ent_rend = ttk.Entry(frm, width=10); self.ent_rend.grid(row=0,column=3)
        ttk.Label(frm, text='Unid resultado:').grid(row=0,column=4); self.ent_un_res = ttk.Combobox(frm, values=UnitConverter.common_units(), width=6); self.ent_un_res.set('un'); self.ent_un_res.grid(row=0,column=5)

        # ingredientes
        ttk.Label(frm, text='Ingrediente:').grid(row=1,column=0); self.ent_ing = ttk.Combobox(frm, values=[p['nome'] for p in self.db.get_produtos()], width=40); self.ent_ing.grid(row=1,column=1)
        ttk.Label(frm, text='Qtd:').grid(row=1,column=2); self.ent_ing_qtd = ttk.Entry(frm, width=10); self.ent_ing_qtd.grid(row=1,column=3)
        ttk.Label(frm, text='Unid:').grid(row=1,column=4); self.cmb_ing_un = ttk.Combobox(frm, values=UnitConverter.common_units(), width=6); self.cmb_ing_un.set('g'); self.cmb_ing_un.grid(row=1,column=5)
        ttk.Button(frm, text='Adicionar ingrediente', command=self.add_ingredient).grid(row=1,column=6, padx=6)

        # listagem de ingredientes temporária
        self.items_tree = ttk.Treeview(self, columns=('produto','qtd','un'), show='headings', height=6)
        for c,t in [('produto','Produto'),('qtd','Quantidade'),('un','Unidade')]:
            self.items_tree.heading(c, text=t)
        self.items_tree.pack(fill='x', padx=6, pady=(0,6))

        ttk.Button(self, text='Salvar Receita (com ingredientes)', command=self.save_recipe).pack(padx=6, pady=6)

        # receitas existentes
        ttk.Label(self, text='Receitas existentes (duplo clique para ver ingredientes)').pack(anchor='w', padx=6)
        self.recipes_tree = ttk.Treeview(self, columns=('nome','rendimento','un'), show='headings')
        for c,t in [('nome','Nome'),('rendimento','Rendimento'),('un','Unid result.')]:
            self.recipes_tree.heading(c, text=t)
        self.recipes_tree.pack(fill='both', expand=True, padx=6, pady=6)
        self.recipes_tree.bind('<Double-1>', self.open_recipe)

    def add_ingredient(self):
        prod = self.ent_ing.get().strip()
        if not prod:
            messagebox.showwarning('Erro','Informe o nome do ingrediente'); return
        try:
            qtd = float(self.ent_ing_qtd.get())
        except Exception:
            messagebox.showwarning('Erro','Quantidade inválida'); return
        un = self.cmb_ing_un.get()
        self.current_items.append((prod, qtd, un))
        self.items_tree.insert('', 'end', values=(prod, f"{qtd}", un))
        self.ent_ing.delete(0,'end'); self.ent_ing_qtd.delete(0,'end')

    def save_recipe(self):
        nome = self.ent_nome.get().strip()
        if not nome:
            messagebox.showwarning('Erro','Informe o nome da receita'); return
        try:
            rendimento = float(self.ent_rend.get())
        except Exception:
            messagebox.showwarning('Erro','Rendimento inválido'); return
        un_res = self.ent_un_res.get() or 'un'
        if not self.current_items:
            messagebox.showwarning('Erro','Adicione ao menos um ingrediente'); return
        try:
            # cria receita e adiciona ingredientes
            rid = self.db.add_receita(nome, rendimento, un_res)
        except Exception as e:
            messagebox.showerror('Erro', str(e)); return
        # adicionar ingredientes (cria produto se necessário)
        try:
            for prod, qtd, un in self.current_items:
                self.db.add_receita_ingrediente(rid, prod, qtd, un)
        except Exception as e:
            messagebox.showerror('Erro ao adicionar ingrediente: ' + str(e)); return
        messagebox.showinfo('OK','Receita salva')
        # limpar UI
        self.current_items = []
        for i in self.items_tree.get_children(): self.items_tree.delete(i)
        self.ent_nome.delete(0,'end'); self.ent_rend.delete(0,'end')
        self.refresh_recipes()

    def refresh_recipes(self):
        for r in self.recipes_tree.get_children(): self.recipes_tree.delete(r)
        for rec in self.db.get_receitas():
            self.recipes_tree.insert('', 'end', iid=rec['id'], values=(rec['nome'], rec['rendimento'], rec['unidade_resultado']))

    def open_recipe(self, event):
        sel = self.recipes_tree.selection()
        if not sel:
            return
        rid = int(sel[0])
        dlg = tk.Toplevel(self)
        dlg.title('Ingredientes da receita')
        tree = ttk.Treeview(dlg, columns=('produto','qtd','unidade'), show='headings')
        for c,t in [('produto','Produto'),('qtd','Quantidade'),('unidade','Unidade')]:
            tree.heading(c, text=t)
        tree.pack(fill='both', expand=True, padx=6, pady=6)
        ings = self.db.get_receita_ingredientes(rid)
        for ing in ings:
            tree.insert('', 'end', values=(ing['produto_nome'], f"{ing['quantidade_usada']}", ing['unidade']))
