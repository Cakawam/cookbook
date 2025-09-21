# ui/producao.py
import tkinter as tk
from tkinter import ttk, messagebox

class ProducaoTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, padding=8)
        self.db = db
        self._build_ui()

    def _build_ui(self):
        ttk.Label(self, text='👨‍🍳 Produção', font=('Segoe UI', 14)).pack(anchor='w')
        frm = ttk.Frame(self); frm.pack(fill='x', padx=6, pady=6)
        ttk.Label(frm, text='Receita:').grid(row=0,column=0); self.cmb_receitas = ttk.Combobox(frm, values=[], width=40); self.cmb_receitas.grid(row=0,column=1)
        ttk.Label(frm, text='Qtd produzida:').grid(row=1,column=0); self.ent_qtd = ttk.Entry(frm, width=12); self.ent_qtd.grid(row=1,column=1)
        ttk.Label(frm, text='Data (opcional DD/MM/AAAA):').grid(row=2,column=0); self.ent_data = ttk.Entry(frm, width=12); self.ent_data.grid(row=2,column=1)
        ttk.Button(frm, text='Registrar produção', command=self.on_produce).grid(row=3,column=0, columnspan=2, pady=8)
        ttk.Button(frm, text='Atualizar receitas', command=self.refresh_receitas).grid(row=4,column=0, columnspan=2)
        self.refresh_receitas()

    def refresh_receitas(self):
        rows = self.db.get_receitas()
        self.cmb_receitas['values'] = [r['nome'] for r in rows]

    def on_produce(self):
        nome = self.cmb_receitas.get().strip()
        if not nome:
            messagebox.showwarning('Erro','Selecione uma receita'); return
        recs = self.db.get_receitas()
        rec = next((r for r in recs if r['nome'] == nome), None)
        if not rec:
            messagebox.showerror('Erro','Receita não encontrada'); return
        try:
            qtd = float(self.ent_qtd.get())
        except Exception:
            messagebox.showwarning('Erro','Qtd inválida'); return
        data = self.ent_data.get() or None
        try:
            self.db.add_producao(rec['id'], qtd, data)
            messagebox.showinfo('Ok','Produção registrada')
        except Exception as e:
            messagebox.showerror('Erro ao produzir', str(e))
