# ui/estoque.py
import tkinter as tk
from tkinter import ttk
from utils.date_helpers import iso_to_display

class EstoqueTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, padding=8)
        self.db = db
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        ttk.Label(self, text='📦 Estoque', font=('Segoe UI', 14)).pack(anchor='w')
        toolbar = ttk.Frame(self); toolbar.pack(fill='x', padx=6, pady=6)
        ttk.Button(toolbar, text='Atualizar', command=self.refresh).pack(side='left')
        ttk.Button(toolbar, text='Gerar Reorder CSV', command=self._gen_reorder).pack(side='left', padx=6)
        self.tree = ttk.Treeview(self, columns=('nome','qtd','un_base','reorder'), show='headings')
        for k,t in [('nome','Produto'),('qtd','Quantidade (base)'),('un_base','Unidade base'),('reorder','Reorder level')]:
            self.tree.heading(k, text=t)
        self.tree.pack(fill='both', expand=True, padx=6, pady=6)
        ttk.Label(self, text='Lotes próximos do vencimento:').pack(anchor='w', padx=6)
        self.expire_tree = ttk.Treeview(self, columns=('produto','qtd','validade'), show='headings')
        for c,t in [('produto','Produto'),('qtd','Quantidade'),('validade','Validade')]:
            self.expire_tree.heading(c, text=t)
        self.expire_tree.pack(fill='x', padx=6, pady=(0,6))

    def refresh(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        for r in self.expire_tree.get_children(): self.expire_tree.delete(r)
        for p in self.db.get_produtos():
            self.tree.insert('', 'end', values=(p['nome'], f"{p['quantidade']:.4f}", p['unidade_base'], p['reorder_level'] or 0))
        for l in self.db.lots_expiring_within(days=7):
            self.expire_tree.insert('', 'end', values=(l['nome'], f"{l['quantidade_base']:.4f}", iso_to_display(l['data_validade'])))

    def _gen_reorder(self):
        import tkinter.filedialog as fd
        dest = fd.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
        if not dest:
            return
        ok = self.db.generate_reorder_csv(dest)
        if ok:
            tk.messagebox.showinfo('Gerado', f'Pedido de compra salvo em {dest}')
        else:
            tk.messagebox.showinfo('Nada', 'Nenhum produto abaixo do reorder level')
