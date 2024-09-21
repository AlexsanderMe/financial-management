import sys, re
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, 
    QWidget, QPushButton, QHBoxLayout, QLabel, QHeaderView, QDialog, QListWidget, QStyledItemDelegate,
    QGroupBox, QScrollArea, QFrame, QMessageBox
)
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtCore import Qt
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from datetime import datetime, timedelta

date_pattern = re.compile(r"^\d{2}/\d{2}/\d{4}$")

meses_pt = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
            7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}


class CustomDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        editor.setStyleSheet("background-color: #00BFFF; color: black;")  # Cor de fundo para o editor
        return editor


class FinancialManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.graphs_mode = 'united'
        self.setWindowTitle("Gestão Financeira")
        self.setGeometry(100, 100, 1000, 700)
        self.current_date = datetime.now()
        self.current_date = datetime.strftime(self.current_date, "%m/%Y")
        
        # Setup midnight theme
        self.set_midnight_theme()

        self.layout = QVBoxLayout()

        # Tabela de gestão financeira
        self.table = QTableWidget(0, 4)
        self.table.setStyleSheet("background-color: rgb(13, 13, 13)")
        self.table.setHorizontalHeaderLabels(["Data", "Descrição", "Valor", "Tipo"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Faz a coluna "Descrição" ser maior
        self.layout.addWidget(self.table)
        self.table.keyPressEvent = self.handle_key_press

        # Aplicar CustomDelegate ao QTableWidget
        self.table.setItemDelegate(CustomDelegate())

        # Botões para ações
        self.button_layout = QHBoxLayout()
        self.add_button = QPushButton("Adicionar Entrada/Saída")
        self.update_button = QPushButton("Ordenar datas")
        self.navigate_button = QPushButton("Selecionar Mês")
        self.add_button.clicked.connect(self.add_entry)
        self.update_button.clicked.connect(self.sort_table_by_date)
        self.navigate_button.clicked.connect(self.navigate_data)
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.update_button)
        self.button_layout.addWidget(self.navigate_button)
        self.layout.addLayout(self.button_layout)

        # Gráfico
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # Labels para saldo na parte inferior
        self.balance_layout = QHBoxLayout()
        self.current_month_balance_label = QLabel("Saldo Atual do Mês: 0")
        self.total_expenses_label = QLabel("Total de Despesas do Mês: 0")
        self.total_balance_label = QLabel("Saldo Total de Todos os Meses: 0")
        self.balance_layout.addWidget(self.total_expenses_label)
        self.balance_layout.addWidget(self.current_month_balance_label)
        self.balance_layout.addWidget(self.total_balance_label)
        self.layout.addLayout(self.balance_layout)

        # Container principal
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)
        
        # Connect signals
        self.table.cellChanged.connect(self.on_cell_changed)

        # Check if a new month has started
        self.check_new_month()
        
        # Load data from database
        self.load_data()

    def set_midnight_theme(self):
        palette = QPalette()
        # Cores mais escuras para o tema meia-noite
        palette.setColor(QPalette.Window, QColor(15, 15, 15))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(15, 15, 15))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(35, 35, 35))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Highlight, QColor(142, 45, 197).lighter())
        palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(palette)

        # Aplicando o tema ao Matplotlib
        plt.style.use('dark_background')
        
        # Ajuste de estilo dos botões e cabeçalhos
        self.setStyleSheet("""
            QPushButton {
                background-color: #232323;
                color: white;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #202020;
            }
            QHeaderView::section {
                background-color: #232323;
                color: white;
            }
            QTableWidget {
                background-color: #131313;
                color: white;
            }
            QLabel {
                color: white;
            }
            QTableCornerButton::section {
                background-color: #131313;
            }
        """)

    def check_new_month(self):
        self.table.setRowCount(0)
        row_position = self.table.rowCount()
        data = datetime.now().strftime("%d/%m/%Y")
        descricao = "# Sua descrição aqui"


        # Colocar ID na tabela
        item = QTableWidgetItem(data)
        item_desc = QTableWidgetItem(descricao)
        item.setData(Qt.UserRole, 1)
        self.table.setItem(row_position, 0, item)
        self.table.setItem(row_position, 1, item_desc)
        self.update_graphs()


    def add_entry(self):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        
        # Verificar se a entrada é no mês atual
        data = datetime.now().strftime("%m/%Y")
        if data == self.current_date:
            # Adiciona a data atual
            data = datetime.now().strftime("%d/%m/%Y")
        else:
            # Se for em meses anteriores, pegar o último dia do mês em exibição para adicionar a entrada
            month = int(data.split('/')[0])
            year = int(data.split('/')[1])
            next_month = datetime(year, month + 1, 1)
            data = next_month - timedelta(days=1)
            data = str(data.day) + '/' + self.current_date
        descricao = "# Sua descrição aqui"
        valor = 0
        
        self.table.setItem(row_position, 0, QTableWidgetItem(data))
        self.table.setItem(row_position, 1, QTableWidgetItem(descricao))
        self.table.setItem(row_position, 2, QTableWidgetItem(f"{valor:.2f}".replace(".", ",")))
        
        # Determinação do tipo (entrada/saída) e coloração
        self.update_entry_type(row_position)

        # Adicionar input para descrição
        self.table.scrollToItem(self.table.item(row_position, 0))
        self.table.setCurrentCell(row_position, 1)
        self.table.editItem(self.table.item(row_position, 1))

        
        # Colocar o ID na tabela
        item = QTableWidgetItem(data)
        item.setData(Qt.UserRole, 2)
        self.table.setItem(row_position, 0, item)
        self.update_graphs()

    def update_entry_type(self, row):
        try:
            valor = float(self.table.item(row, 2).text().replace('.', '').replace(',', '.'))
        except ValueError:
            valor = 0
    
        tipo_item = QTableWidgetItem("Entrada" if valor > 0 else "***" if valor == 0 else "Saída")
        tipo_item.setFlags(tipo_item.flags() & ~Qt.ItemIsEditable)  # Faz o item não ser editável
        if valor > 0:
            tipo_item.setForeground(QColor(0, 255, 0))  # Verde para entrada
        elif valor == 0:
            tipo_item.setForeground(QColor(255, 255, 0))  # Amarelo para neutro
        else:
            tipo_item.setForeground(QColor(255, 0, 0))  # Vermelho para saída
        
        self.table.setItem(row, 3, tipo_item)

    def on_cell_changed(self, row, column):
        id = self.table.item(row, 0).data(Qt.UserRole)
        if id == None:
            return
        date_item = self.table.item(row, 0)
        description_item = self.table.item(row, 1)
        value_item = self.table.item(row, 2)

        # Verifica e valida o formato da data
        if column == 0 and date_item is not None:
            old_date = "01/01/2001"
            date_text = date_item.text()
            if not date_pattern.match(date_text):
                self.show_error_message("Formato de data inválido. Use dd/mm/aaaa.")
                self.table.blockSignals(True)
                date_item.setText(old_date)
                self.table.blockSignals(False)
                return


        date = date_item.text() if date_item is not None else ""
        try:
            date_obj = datetime.strptime(date, '%d/%m/%Y')
        except ValueError:
            self.show_error_message("Esta data não existe.")
            self.table.blockSignals(True)
            date_item.setText(old_date)
            self.table.blockSignals(False)
            return
        description = description_item.text() if description_item is not None else ""
        try:
            value = float(value_item.text().replace('.', '').replace(',', '.')) if value_item is not None else 0.0
        except ValueError:
            old_value = 0.0
            value = old_value
            self.show_error_message("Formato inválido. Use, por exemplo: 1500,50.")
            self.table.blockSignals(True)
            value_item.setText(f"{old_value:.2f}".replace(".", ","))
            self.table.blockSignals(False)
            return


        if column == 0:  # Se a coluna modificada for a de datas
            self.update_graphs()
        elif column == 1:  # Se a coluna modificada for a de descrições
            pass
        elif column == 2:  # Se a coluna modificada for a de valores
            self.update_entry_type(row)
            self.format_value(row, column)
            self.update_graphs()

    def show_error_message(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(message)
        msg.setWindowTitle("Erro")
        msg.exec_()


    def handle_key_press(self, event):
        if event.key() == Qt.Key_Delete:
            current_row = self.table.currentRow()
            if current_row >= 0:
                self.confirm_and_delete_item(current_row)
        else:
            # Chama o evento original se não for a tecla Delete
            super(QTableWidget, self.table).keyPressEvent(event)

    def confirm_and_delete_item(self, row):
        reply = QMessageBox.question(self.table, 'Confirmação', 
                                     'Tem certeza que deseja deletar o item selecionado?', 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.table.removeRow(row)
            self.update_graphs()


    def format_value(self, row, column):
        item = self.table.item(row, column)
        try:
            value = float(item.text().replace('.', '').replace(',', '.'))
            formatted_value = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            item.setText(formatted_value)
        except ValueError:
            item.setText("0,00")

    def update_graphs(self):
        data = []
        for row in range(self.table.rowCount()):
            date_item = self.table.item(row, 0)
            description_item = self.table.item(row, 1)
            value_item = self.table.item(row, 2)
            
            if date_item and value_item:
                # Obtém o dia (exclui o mês e ano)
                date = date_item.text().split('/')[0]
                description = description_item.text() if description_item is not None else ""
                try:
                    value = float(value_item.text().replace('.', '').replace(',', '.'))
                except ValueError:
                    value = 0.0  # Em caso de erro na conversão, define o valor como 0.0
                data.append({"Data": date, "Descrição": description, "Valor": value})

        if not data:
            self.current_month_balance_label.setText("Saldo Atual do Mês: 0,00")
            self.total_expenses_label.setText("Total de Despesas do Mês: 0,00")
            self.total_balance_label.setText("Saldo Total de Todos os Meses: 0,00")
            self.ax.clear()
            self.canvas.draw()
            return

        df = pd.DataFrame(data)

        # Calcular total de despesas antes de agrupar os dados
        total_expenses = df[df['Valor'] < 0]['Valor'].sum()
        total_gross = df[df['Valor'] > 0]['Valor'].sum()

        if self.graphs_mode == "united":
            # Agrupar valores pelo dia
            df = df.groupby('Data', as_index=False).sum()

        # Atualizar o saldo total atual do mês
        current_month_balance = df['Valor'].sum()
        self.current_month_balance_label.setText(
            f"Saldo Atual do Mês: {current_month_balance:,.2f}   -   Saldo Bruto: {total_gross:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        self.current_month_balance_label.setAlignment(Qt.AlignCenter)
        self.total_expenses_label.setText(
            f"Total de Despesas do Mês: {total_expenses:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        self.total_expenses_label.setAlignment(Qt.AlignLeft)

        # Atualizar o saldo total de todos os meses (Versão atual sem banco de dados - Pegando somente o mês atual)
        total_balance = current_month_balance
        total_balance = total_balance if total_balance is not None else 0.0
        self.total_balance_label.setText(
            f"Saldo Total de Todos os Meses: {total_balance:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        self.total_balance_label.setAlignment(Qt.AlignRight)


        self.ax.clear()

        # Plotting
        colors = ['#90d4c4' if value >= 0 else '#DC143C' for value in df['Valor']]
        df.set_index('Data', inplace=True)
        df['Valor'].plot(ax=self.ax, kind='bar', color=colors)

        title_month = meses_pt[int(self.current_date.split('/')[0])]
        self.ax.set_title(f"Receitas e Despesas - {title_month} de {self.current_date.split('/')[1]}")
        self.ax.set_ylabel("Valor")
        self.ax.set_xlabel("Dia")
        self.ax.tick_params(axis='x', rotation=0)

        for i, (date, value) in enumerate(df['Valor'].items()):
            self.ax.text(i, value, f'{value:,.2f}', ha='center', va='bottom', fontsize=8, color='white')

        self.ax.axhline(0, color='white', linewidth=0.5, linestyle='--')
        self.canvas.draw()



    def navigate_data(self):
        # Janela de navegação dos meses
        dialog = QDialog(self)
        dialog.setWindowTitle("Selecione o Mês Desejado")
        dialog.setGeometry(0, 0, 400, 300)
        dialog.setFixedSize(400, 300)

        # Centralizando a janela
        rect = dialog.frameGeometry()
        rect.moveCenter(self.geometry().center())
        dialog.move(rect.topLeft())


        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(0, 0, 13))
        dialog.setPalette(palette)

        main_layout = QVBoxLayout()

        # Linha adicionada para funcionar esta versão
        self.current_date_navigate = datetime.now()
        self.current_date_navigate = datetime.strftime(self.current_date_navigate, "%d/%m/%Y")

        # Consultando banco de dados (Versão atual sem banco de dados)
        data = [(1, self.current_date_navigate, "", 0.0)]
        dates_by_year = {}

        # Adicionar meses/anos únicos ao dicionário
        for row_data in data:
            try:
                date_value = datetime.strptime(row_data[1], "%d/%m/%Y")
            except ValueError:
                try:
                    date_value = datetime.strptime(row_data[1], "%Y-%m-%d")
                except ValueError:
                    # Pular se o formato não for reconhecido
                    continue

            year = date_value.strftime("%Y")
            month_year = date_value.strftime("%m/%Y")

            if year not in dates_by_year:
                dates_by_year[year] = set()
            dates_by_year[year].add(month_year)

        # Organizar os anos e adicionar eles ao layout com QGroupBox
        sorted_years = sorted(dates_by_year.keys(), reverse=True)
        for year in sorted_years:
            year_button = QPushButton(year)
            year_button.setCheckable(True)
            year_button.setStyleSheet("QPushButton { text-align: left; border: 1px solid gray; border-radius: 10px; padding: 5px; color: white; font-weight: bold; }")

            list_widget = QListWidget()
            list_widget.setVisible(False)
            list_widget.setStyleSheet("QListWidget { text-align: left; border: 1px solid gray; border-radius: 10px; padding: 5px; background-color: #131313; color: white; }")

            sorted_dates = sorted(dates_by_year[year], reverse=True)
            for date_str in sorted_dates:
                ##################
                title_month = meses_pt[int(date_str.split('/')[0])]
                list_widget.addItem(date_str + ' - %s' % title_month)

            # Connect signal
            list_widget.itemClicked.connect(self.on_month_year_selected)
            year_button.clicked.connect(lambda checked, lw=list_widget: lw.setVisible(checked))

            main_layout.addWidget(year_button)
            main_layout.addWidget(list_widget)

        # Adicionar barra de rolagem para lidar com o excesso
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet("QScrollBar:vertical { border: 1px solid gray; border-radius: 10px; background-color: #000013; }")
        scroll_area.setWidgetResizable(True)
        container = QFrame()
        container.setStyleSheet("QFrame { border: 1px solid gray; border-radius: 10px; background-color: #000000; }")
        container.setLayout(main_layout)
        scroll_area.setWidget(container)

        dialog_layout = QVBoxLayout()
        dialog_layout.addWidget(scroll_area)
        dialog.setLayout(dialog_layout)

        # Mostrar diálogo
        dialog.exec_()

    def on_month_year_selected(self, item):
        # Obtenha o mês/ano selecionado
        selected_month_year = item.text()
        month = int(selected_month_year.split("/")[0])
        year = int(selected_month_year.split("/")[1].split(' - ')[0])

        # Criar tabela
        self.table.setRowCount(0)

        # Linha adicionada para funcionar esta versão
        self.current_date_navigate = datetime.now()
        self.current_date_navigate = datetime.strftime(self.current_date_navigate, "%d/%m/%Y")

        # Consultando banco de dados (Versão atual sem banco de dados)
        data = [(1, self.current_date_navigate, "", 0.0)]

        # Adicionar dados à tabela
        for row_data in data:
            try:
                date_value = datetime.strptime(row_data[1], "%d/%m/%Y")
            except ValueError:
                try:
                    date_value = datetime.strptime(row_data[1], "%Y-%m-%d")
                except ValueError:
                    # Ignore esta linha se o formato da data não for reconhecido
                    continue

            if date_value.month == month and date_value.year == year:
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                item = QTableWidgetItem(date_value.strftime("%d/%m/%Y"))
                item.setData(Qt.UserRole, row_data[0])  # Store the id in the UserRole of the item
                self.table.setItem(row_position, 0, item)
                self.table.setItem(row_position, 1, QTableWidgetItem(row_data[2]))
                if isinstance(row_data[3], (int, float)):
                    self.table.setItem(row_position, 2, QTableWidgetItem(f"{row_data[3]:.2f}".replace(".", ",")))
                else:
                    self.table.setItem(row_position, 2, QTableWidgetItem(row_data[3]))
                self.update_entry_type(row_position)
        
        # Salvar data atual da tabela
        self.current_date = selected_month_year.split(' - ', 1)[0]

        self.sort_table_by_date()

        # Atualizar gráfico
        self.update_graphs()

    def on_date_selected(self, item):
        # Obtenha a data selecionada
        selected_date = item.text()

        # Limpar tabela
        self.table.setRowCount(0)

        # Linha adicionada para funcionar esta versão
        self.current_date_navigate = datetime.now()
        self.current_date_navigate = datetime.strftime(self.current_date_navigate, "%d/%m/%Y")

        # Consultando banco de dados (Versão atual sem banco de dados)
        data = [(1, self.current_date_navigate, "", 0.0)]

        # Adicionar dados à tabela
        for row_data in data:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            item = QTableWidgetItem(row_data[1])
            item.setData(Qt.UserRole, row_data[0])  # Armazene o id no UserRole do item
            self.table.setItem(row_position, 0, item)
            self.table.setItem(row_position, 1, QTableWidgetItem(row_data[2]))
            if isinstance(row_data[3], (int, float)):
                self.table.setItem(row_position, 2, QTableWidgetItem(f"{row_data[3]:.2f}".replace(".", ",")))
            else:
                self.table.setItem(row_position, 2, QTableWidgetItem(row_data[3]))
            self.update_entry_type(row_position)

        # Atualizar gráfico
        self.update_graphs()

    def load_data(self):
        # Obtenha o mês e ano atuais
        current_month = datetime.now().month
        current_year = datetime.now().year

        # Linha adicionada para funcionar esta versão
        self.current_date_navigate = datetime.now()
        self.current_date_navigate = datetime.strftime(self.current_date_navigate, "%d/%m/%Y")

        # Consultando banco de dados (Versão atual sem banco de dados)
        data = [(1, self.current_date_navigate, "", 0.0)]

        # Adicionar dados à tabela
        for row_data in data:
            try:
                date_value = datetime.strptime(row_data[1], "%d/%m/%Y")
            except ValueError:
                try:
                    date_value = datetime.strptime(row_data[1], "%Y-%m-%d")
                except ValueError:
                    # Ignore esta linha se o formato da data não for reconhecido
                    continue

            if date_value.month == current_month and date_value.year == current_year:
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                item = QTableWidgetItem(date_value.strftime("%d/%m/%Y"))
                item.setData(Qt.UserRole, row_data[0])  # Armazene o id no UserRole do item
                self.table.setItem(row_position, 0, item)
                self.table.setItem(row_position, 1, QTableWidgetItem(row_data[2]))
                if isinstance(row_data[3], (int, float)):
                    self.table.setItem(row_position, 2, QTableWidgetItem(f"{row_data[3]:.2f}".replace(".", ",")))
                else:
                    self.table.setItem(row_position, 2, QTableWidgetItem(row_data[3]))
                self.update_entry_type(row_position)
        self.sort_table_by_date()

    def sort_table_by_date(self):
        # Obtenha o número de linhas da tabela
        row_count = self.table.rowCount()
        
        # Crie uma lista para armazenar os dados da tabela junto com os IDs
        table_data = []
        for row in range(row_count):
            date_item = self.table.item(row, 0)
            what_date = date_item.text().rsplit('/', 1)[-1]
            if what_date != self.current_date.split('/')[1]:
                continue
            description_item = self.table.item(row, 1)
            value_item = self.table.item(row, 2)
            type_item = self.table.item(row, 3)
            
            # Recuperar dados de itens de tabela
            date = date_item.text()
            description = description_item.text() if description_item is not None else ""
            value = value_item.text() if value_item is not None else 0.0
            entry_id = self.table.item(row, 0).data(Qt.UserRole)  # Recuperar ID de UserRole da primeira coluna
            entry_type = type_item.text() if type_item is not None else ""
            
            # Armazene dados em uma tupla junto com o ID
            table_data.append((entry_id, date, description, value, entry_type))
        
        # Classifique os dados da tabela por data
        table_data.sort(key=lambda x: datetime.strptime(x[1], "%d/%m/%Y"))
        
        # Limpar a tabela
        self.table.setRowCount(0)
        
        # Preencher a tabela com dados classificados
        for row, (entry_id, date, description, value, entry_type) in enumerate(table_data):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(date))
            self.table.setItem(row, 1, QTableWidgetItem(description))
            if type(value) == float:
                value = str(value).replace('.', ',')
            self.table.setItem(row, 2, QTableWidgetItem(value))
            self.table.setItem(row, 3, QTableWidgetItem(entry_type))
            self.table.item(row, 0).setData(Qt.UserRole, entry_id)  # Definir o ID para o UserRole da primeira coluna

        for row in range(self.table.rowCount()):
            self.update_entry_type(row)
        self.update_graphs()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FinancialManager()
    window.show()
    app.exec_()
