import tkinter as tk
from tkinter import ttk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Importa as 4 funções de plotagem do seu arquivo de utilitários
from utils.dash import plot_sales_trend, plot_top_products, plot_stock_levels, plot_purchases_by_supplier

class DashboardTab(ttk.Frame):
    def __init__(self, parent, db):
        """
        Inicializa a aba do Dashboard.

        Args:
            parent: O widget pai (geralmente um ttk.Notebook).
            db: A instância do gerenciador de banco de dados (DBManager).
        """
        super().__init__(parent, padding=8)
        self.db = db

        # Inicializa as quatro figuras do Matplotlib que conterão os gráficos
        self.fig1 = Figure(dpi=100)
        self.fig2 = Figure(dpi=100)
        self.fig3 = Figure(dpi=100)
        self.fig4 = Figure(dpi=100)

        # Constrói a interface gráfica e carrega os dados iniciais
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        """Constrói todos os widgets da interface do dashboard."""
        
        # --- Painel Superior: Estatísticas e Botão ---
        top_frame = ttk.Frame(self)
        top_frame.pack(side="top", fill="x", anchor="n", pady=(0, 10))

        stats_frame = ttk.Frame(top_frame)
        stats_frame.pack(side="left", fill="x", expand=True)

        ttk.Label(stats_frame, text='📊 Dashboard', font=('Segoe UI', 14, 'bold')).pack(anchor='w')
        self.lbl_rev = ttk.Label(stats_frame, text='Receita (30d): R$ 0.00')
        self.lbl_rev.pack(anchor='w', pady=1)
        self.lbl_cogs = ttk.Label(stats_frame, text='COGS (estimado 30d): R$ 0.00')
        self.lbl_cogs.pack(anchor='w', pady=1)
        self.lbl_stock = ttk.Label(stats_frame, text='Valor estoque: R$ 0.00')
        self.lbl_stock.pack(anchor='w', pady=1)
        
        self.btn_refresh = ttk.Button(top_frame, text='Atualizar', command=self.refresh)
        self.btn_refresh.pack(side="right", anchor="ne", pady=6)
        
        # --- Painel Inferior: Grade de Gráficos ---
        charts_frame = ttk.Frame(self)
        charts_frame.pack(expand=True, fill='both')

        # Configura a grade (2 colunas, 2 linhas) para expandir com a janela
        charts_frame.grid_columnconfigure(0, weight=1)
        charts_frame.grid_columnconfigure(1, weight=1)
        charts_frame.grid_rowconfigure(0, weight=1)
        charts_frame.grid_rowconfigure(1, weight=1)

        # Cria os 4 "canvas" (áreas de desenho) para os gráficos
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=charts_frame)
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=charts_frame)
        self.canvas3 = FigureCanvasTkAgg(self.fig3, master=charts_frame)
        self.canvas4 = FigureCanvasTkAgg(self.fig4, master=charts_frame)

        # Posiciona cada gráfico na sua célula da grade 2x2
        # 'sticky' faz com que o widget se expanda para preencher a célula
        self.canvas1.get_tk_widget().grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        self.canvas2.get_tk_widget().grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        self.canvas3.get_tk_widget().grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        self.canvas4.get_tk_widget().grid(row=1, column=1, sticky='nsew', padx=5, pady=5)

    def refresh(self):
        """Busca os dados mais recentes do banco e atualiza todos os elementos da tela."""
        
        # 1. Atualiza os labels de estatísticas
        try:
            stats = self.db.compute_sales_and_cogs()
            stock_val = self.db.total_stock_value()
            self.lbl_rev.config(text=f"Receita (30d): R$ {stats['revenue']:.2f}")
            self.lbl_cogs.config(text=f"COGS (estimado 30d): R$ {stats['cogs_est']:.2f}")
            self.lbl_stock.config(text=f"Valor estoque: R$ {stock_val:.2f}")
        except Exception as e:
            print(f"Erro ao atualizar estatísticas: {e}")
            self.lbl_rev.config(text="Receita (30d): Erro")
            self.lbl_cogs.config(text="COGS (estimado 30d): Erro")
            self.lbl_stock.config(text="Valor estoque: Erro")


        # 2. Atualiza os gráficos
        try:
            conn = self.db.get_connection()

            # Gráfico 1 (Canto Superior Esquerdo)
            plot_sales_trend(conn, self.fig1)
            self.canvas1.draw()

            # Gráfico 2 (Canto Superior Direito)
            plot_top_products(conn, self.fig2)
            self.canvas2.draw()

            # Gráfico 3 (Canto Inferior Esquerdo)
            plot_stock_levels(conn, self.fig3)
            self.canvas3.draw()

            # Gráfico 4 (Canto Inferior Direito)
            plot_purchases_by_supplier(conn, self.fig4)
            self.canvas4.draw()
        except Exception as e:
            print(f"Erro ao desenhar gráficos: {e}")