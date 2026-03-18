from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QInputDialog,
    QTableWidgetItem, QAbstractItemView,QHeaderView,QLineEdit,QScrollArea,QFrame
)
from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout
from PyQt6.uic import loadUiType
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import (Qt,QSize)
import psycopg2
import sys
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QDoubleSpinBox, QSpinBox, QMessageBox, QWidget, QGridLayout
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QFileDialog
)
from PIL import Image, ExifTags
from os import path
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QSize
from PIL import Image, ExifTags
from os import path
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QFrame, QPushButton

#from main import Ui_MainWindow

FORM_CLASS, _ = loadUiType(r"C:\Users\LOQ\Documents\espace de programmation gi11\my brikoler set up\source code brikoler\main.ui")

#-----------------------
class ProductDisplay(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent  # MainApp reference
        self.conn = parent.connection
        self.cursor = parent.cursor

        main_layout = QVBoxLayout(self)

        # === Search bar ===
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 بحث عن طريق الاسم أو الماركة...")
        self.search_button = QPushButton("بحث")
        self.search_button.clicked.connect(self.load_products)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)

        # === Scrollable area ===
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.products_container = QWidget()
        self.grid_layout = QGridLayout(self.products_container)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setSpacing(15)

        self.scroll_area.setWidget(self.products_container)

        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.scroll_area)

    def load_products(self):
        # Clear grid
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        search_text = self.search_input.text().strip()
        query = """
            SELECT bar_code, designation, marque, category, prix_achat, prix_vende, img_path, quantity
            FROM produit
            WHERE 1=1
        """
        params = []
        if search_text:
            query += " AND (LOWER(designation) LIKE %s OR LOWER(marque) LIKE %s)"
            search_term = f"%{search_text.lower()}%"
            params.extend([search_term, search_term])

        query += " ORDER BY designation LIMIT 1000"

        self.cursor.execute(query, params)
        products = self.cursor.fetchall()

        row, col = 0, 0
        for product in products:
            card = self.create_product_card(product)
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col >= 4:  # 4 items per row
                col = 0
                row += 1






    def create_product_card(self, product):
        bar_code, designation, marque, category, prix_achat, prix_vende, img_path, quantity = product

        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setFixedSize(QSize(200, 270))
        layout = QVBoxLayout(card)

        # === Image ===
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pixmap = None

        if img_path:
                full_path = path.abspath(img_path)
                if path.exists(full_path):
                        try:
                                # Open with Pillow
                                pil_img = Image.open(full_path)

                                # Fix orientation based on EXIF
                                try:
                                        for orientation in ExifTags.TAGS.keys():
                                                if ExifTags.TAGS[orientation] == "Orientation":
                                                        break
                                        exif = pil_img._getexif()
                                        if exif and orientation in exif:
                                                if exif[orientation] == 3:
                                                        pil_img = pil_img.rotate(180, expand=True)
                                                elif exif[orientation] == 6:
                                                        pil_img = pil_img.rotate(270, expand=True)
                                                elif exif[orientation] == 8:
                                                        pil_img = pil_img.rotate(90, expand=True)
                                except Exception:
                                        pass  # ignore if no EXIF

                                # Convert to QPixmap
                                data = pil_img.tobytes("raw", "RGB")
                                qimage = QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGB888)
                                pixmap = QPixmap.fromImage(qimage)
                        except Exception:
                                pass

        # Fallback
        if not pixmap or pixmap.isNull():
                pixmap = QPixmap("no_image.png")

        # Scale
        pixmap = pixmap.scaled(
                150, 150,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
        )
        image_label.setPixmap(pixmap)

        # === Name ===
        name_label = QLabel(designation)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)

        # === Price ===
        price_label = QLabel(f"{prix_vende:.2f} د.ت")
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_label.setStyleSheet("color: green; font-weight: bold;")

        # === Sell button ===
        sell_button = QPushButton("🛒 بيع")
        sell_button.clicked.connect(lambda _, p=product: self.sell_product(p))

        layout.addWidget(image_label)
        layout.addWidget(name_label)
        layout.addWidget(price_label)
        layout.addWidget(sell_button)

        return card


    def sell_product(self, product):
        qty, prix_final = self.parent_app.ask_quantity_and_confirm(product)
        if qty is not None and prix_final is not None:
            self.parent_app.sales_list.append((product, qty, prix_final))
            self.parent_app.add_to_sales_table(product, qty, prix_final)


#***-----*****------




class ProductSaleDialog(QDialog):
    def __init__(self, product, parent=None):
        super().__init__(parent)
        self.setWindowTitle("نافذة البيع")
        self.setMinimumWidth(500)

        self.product = product
        bar_code, designation, marque, category, prix_achat, prix_vende, img_path, quantity_stock = product

        main_layout = QHBoxLayout()

        # === Image ===
        image_label = QLabel()
        pixmap = None
        if img_path and path.exists(img_path):
            try:
                pil_img = Image.open(img_path)

                # Fix orientation based on EXIF
                try:
                    for orientation in ExifTags.TAGS.keys():
                        if ExifTags.TAGS[orientation] == "Orientation":
                            break
                    exif = pil_img._getexif()
                    if exif and orientation in exif:
                        if exif[orientation] == 3:
                            pil_img = pil_img.rotate(180, expand=True)
                        elif exif[orientation] == 6:
                            pil_img = pil_img.rotate(270, expand=True)
                        elif exif[orientation] == 8:
                            pil_img = pil_img.rotate(90, expand=True)
                except Exception:
                    pass  # ignore if no EXIF

                # Ensure RGB
                if pil_img.mode != "RGB":
                    pil_img = pil_img.convert("RGB")

                # Convert Pillow -> QPixmap
                data = pil_img.tobytes("raw", "RGB")
                qimage = QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(qimage)

            except Exception:
                pixmap = None

        if pixmap and not pixmap.isNull():
            image_label.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            image_label.setText("❌ لا توجد صورة")

        main_layout.addWidget(image_label)

        # === Input Area ===
        input_layout = QVBoxLayout()

        # Product name
        input_layout.addWidget(QLabel(f"📦 المنتج: {designation}"))

        # Quantity available
        input_layout.addWidget(QLabel(f"الكمية المتوفرة: {quantity_stock}"))

        # Purchase price (capital)
        input_layout.addWidget(QLabel(f"رأس المال: {prix_achat:.2f} د.ت"))

        # Quantity to sell
        input_layout.addWidget(QLabel("الكمية المراد بيعها:"))
        if category in ['kg', 'm']:
            self.qty_input = QDoubleSpinBox()
            self.qty_input.setDecimals(3)
            self.qty_input.setMinimum(0.00)
            self.qty_input.setSingleStep(0.1)
            self.qty_input.setMaximum(float(quantity_stock))
        else:
            self.qty_input = QSpinBox()
            self.qty_input.setMinimum(1)
            self.qty_input.setMaximum(int(quantity_stock))
        input_layout.addWidget(self.qty_input)

        # Final sale price
        input_layout.addWidget(QLabel("السعر النهائي للوحدة:"))
        self.price_input = QDoubleSpinBox()
        self.price_input.setDecimals(2)
        self.price_input.setMinimum(float(prix_achat))
        self.price_input.setMaximum(999999)
        self.price_input.setValue(float(prix_vende))
        input_layout.addWidget(self.price_input)

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("✅ موافق")
        cancel_button = QPushButton("❌ إلغاء")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        input_layout.addLayout(button_layout)

        main_layout.addLayout(input_layout)
        self.setLayout(main_layout)

    def get_values(self):
        return self.qty_input.value(), self.price_input.value()

class MainApp(QMainWindow, FORM_CLASS):
    def __init__(self, parent=None):
        super(MainApp, self).__init__(parent)
        QMainWindow.__init__(self)
        self.setupUi(self)
        self.setWindowTitle("Brikoler")

        self.DB_connect()
        self.tabWidget.tabBar().setVisible(False)
        #******-------
        self.button_100.clicked.connect(self.show_product_window)

        #******------
        self.setup_sales_table()
        self.load_produits_into_table()
        self.dateEdit.setDate(QDate.currentDate())
        self.bar_code_input.setFocus()
        self.search_ventes_by_date()
        self.tableWidget.cellClicked.connect(self.display_selected_image)
        self.tableWidget_1.cellClicked.connect(self.display_selected_image_1)
        self.pushButton.clicked.connect(self.search_item)
        self.load_marques()  # Fill comboBox_2 with available marques
        self.search_item()
        self.dateEdit_2.setDate(QDate.currentDate())

        
        self.sales_list = []  # List of (product, quantity, prix_final)

        # Side menu buttons
        self.store.clicked.connect(self.store_fonc)
        self.base.clicked.connect(self.base_fonc)
        self.historique.clicked.connect(self.historique_fonc)
        self.manque.clicked.connect(lambda: self.tabWidget.setCurrentIndex(3))

        # Main action buttons
        self.ajouter.clicked.connect(self.add_product_to_cart)
        self.sell_btn.clicked.connect(self.confirm_sale)     # بيع
        self.cancel_btn.clicked.connect(self.cancel_sale)    # الغاء
        self.pushButton_2.clicked.connect(self.search_ventes_by_date)#سجل المبيعات
        self.pushButton_day.clicked.connect(self.show_profit_day)
        self.pushButton_week.clicked.connect(self.show_profit_week)
        self.pushButton_month.clicked.connect(self.show_profit_month)
        self.pushButton_year.clicked.connect(self.show_profit_year)
        self.pushButton_8.clicked.connect(self.browse_image)
        self.pushButton_9.clicked.connect(self.add_product_to_db)

        self.pushButton_10.clicked.connect(self.browse_image)
        self.pushButton_11.clicked.connect(self.update_product_in_db)

        self.pushButton_3.clicked.connect(self.load_facture_details_by_date)
        

        self.tableWidget_2.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableWidget_2.verticalHeader().setVisible(False)
        self.tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget_1.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableWidget_1.verticalHeader().setVisible(False)
        self.tableWidget_3.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableWidget_3.verticalHeader().setVisible(False)
        self.total_label.setText("0")  # ✅ Initialize total label

    def DB_connect(self):
        try:
            self.connection = psycopg2.connect(
                dbname='magasin_db',
                user='postgres',
                password='0000',
                host='localhost',
                port=5432
            )
            self.cursor = self.connection.cursor()
            print("✅ Connected to PostgreSQL database.")
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Could not connect to database:\n{e}")
    #*******--------
    def show_product_window(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("📦 عرض المنتجات")
        dialog.setMinimumSize(900, 600)

        layout = QVBoxLayout(dialog)

    # Add ProductDisplay widget
        product_display = ProductDisplay(self)
        layout.addWidget(product_display)

    # Load products immediately
        product_display.load_products()

        dialog.setLayout(layout)
        dialog.exec()

    #*******--------
    def store_fonc(self):
        self.bar_code_input.clear()
        self.tabWidget.setCurrentIndex(0)
        self.bar_code_input.setFocus()

    def base_fonc(self):
        self.lineEdit_9.clear()
        self.tabWidget.setCurrentIndex(1)
        self.lineEdit_9.setFocus()
        
    def historique_fonc(self):
        self.lineEdit_7.clear()
        self.tabWidget.setCurrentIndex(2)
        self.lineEdit_7.setFocus()
        
    
    def get_product_by_barcode(self, bar_code):
        try:
            self.cursor.execute("""
                SELECT bar_code, designation, marque,category, prix_achat, prix_vende,img_path, quantity
                FROM produit
                WHERE bar_code = %s
            """, (bar_code,))
            return self.cursor.fetchone()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))
            return None

    def ask_quantity_and_confirm(self, product):
        bar_code, designation, _, _, _, _, _, quantity_stock = product
        if quantity_stock < 1:
            QMessageBox.warning(self, "الكمية غير متوفرة", f"المنتج {designation} غير متوفر في المخزون.")
            self.bar_code_input.clear()
            return None, None

        dialog = ProductSaleDialog(product, self)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            qty, prix_final = dialog.get_values()
            return qty, prix_final

        return None, None
    
    def add_product_to_cart(self):
        bar_code = self.bar_code_input.text().strip()
        if not bar_code:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال معرف السلعة")
            return

        product = self.get_product_by_barcode(bar_code)
        if not product:
            QMessageBox.warning(self, "غير موجود", "المنتج غير موجود في قاعدة البيانات")
            self.bar_code_input.clear()
            return

        qty, prix_final = self.ask_quantity_and_confirm(product)
        if qty is None or prix_final is None:
            return
        if qty <= 0.001:
            QMessageBox.warning(self, "كمية غير صالحة", "❌ لا يمكن بيع كمية تساوي صفر.")
            return
        for i, (p, existing_qty, existing_price) in enumerate(self.sales_list):
            if p[0] == bar_code and existing_price == prix_final:
            # Update quantity in the sales list
                new_qty = existing_qty + qty
                self.sales_list[i] = (p, new_qty, prix_final)

            # Update row in the table
                self.tableWidget.setItem(i, 0, QTableWidgetItem(str(new_qty)))  # Update quantity cell

            # ✅ Recalculate total
                self.recalculate_total()
                return

        self.sales_list.append((product, qty, prix_final))
        self.add_to_sales_table(product, qty, prix_final)
        self.bar_code_input.clear()           # ✅ Clear after adding
        self.bar_code_input.setFocus() 
# # # # # # # # # # # # # #
    def setup_sales_table(self):
    # Ensure the table has 4 columns
        self.tableWidget.setColumnCount(4)

    # Set Arabic column headers
        self.tableWidget.setHorizontalHeaderLabels(["  الكمية  ","  المعرف  ", "  اسم المنتج  ", "  السعر  " ])

    # Optional: Adjust header size to fit content
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) 

# # # # # # # # # # # # # # # 
    def add_to_sales_table(self, product, qty, prix_final):
        _, designation, _, _, _, _, _, _ = product
        row = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row)
        self.tableWidget.setItem(row, 3, QTableWidgetItem(f"{prix_final:.2f}"))  # Prix
        self.tableWidget.setItem(row, 2, QTableWidgetItem(designation))          # Designation
        self.tableWidget.setItem(row, 1, QTableWidgetItem(product[0]))          # Bar_code
        self.tableWidget.setItem(row, 0, QTableWidgetItem(str(qty)))            # Quantity

        # ✅ Update total label
        try:
            current_total = float(self.total_label.text()) if self.total_label.text() else 0.0
            current_total += qty * prix_final
            self.total_label.setText(f"{current_total:.2f}")
        except Exception as e:
            print(f"❌ Failed to update total: {e}")
        self.recalculate_total() 
    def confirm_sale(self):
        if not self.sales_list:
            QMessageBox.information(self, "تنبيه", "لا توجد منتجات للشراء")
            return
        for product, qty, _ in self.sales_list:
            if qty <= 0.001:
                QMessageBox.warning(self, "خطأ", f"❌ لا يمكن بيع {product[1]} بكمية تساوي صفر.")
                return

        total_invoice = sum(qty * prix_final for _, qty, prix_final in self.sales_list)

        try:
        # 1. Insert into facture and get the new facture_id
            self.cursor.execute("""
                INSERT INTO facture (total) VALUES (%s) RETURNING id
            """, (total_invoice,))
            facture_id = self.cursor.fetchone()[0]

        # 2. Insert into ventes with this facture_id
            for product, qty, prix_final in self.sales_list:
                bar_code = product[0]
                designation = product[1]
                self.perform_sale(bar_code, qty)
                self.record_sale(bar_code, designation, qty, prix_final, facture_id)

            self.connection.commit()
            QMessageBox.information(self, "تم", f"✅ تم إصدار الفاتورة رقم {facture_id}")
            self.clear_sales_table()
            self.load_produits_into_table()

        except Exception as e:
            self.connection.rollback()
            QMessageBox.critical(self, "خطأ", f"❌ {str(e)}")
        self.bar_code_input.setFocus()
    def record_sale(self, bar_code, designation, qty, prix_final, facture_id):
        try:
            self.cursor.execute("""
                INSERT INTO ventes (bar_code, designation, quantity_sold, prix_vende, facture_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (bar_code, designation, qty, prix_final, facture_id))
        except Exception as e:
            raise e

    def cancel_sale(self):
        if not self.sales_list:
            QMessageBox.information(self, "تنبيه", "لا توجد عملية بيع للغاء")
            return

        choice = QMessageBox.question(
            self, "إلغاء الشراء",
            "هل تريد إلغاء كل عملية البيع؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if choice == QMessageBox.StandardButton.Yes:
            self.clear_sales_table()
        else:
            self.remove_or_edit_item()
        self.bar_code_input.setFocus()
    def remove_or_edit_item(self):
        barcodes = [f"{i+1}. {p[0][1]} ({p[0][0]})" for i, p in enumerate(self.sales_list)]
        item, ok = QInputDialog.getItem(self, "تعديل", "اختر المنتج للتعديل أو الحذف:", barcodes, editable=False)
        if ok and item:
            index = int(item.split('.')[0]) - 1
            action = QMessageBox.question(
                self, "خيارات",
                f"هل تريد حذف {self.sales_list[index][0][1]}؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if action == QMessageBox.StandardButton.Yes:
                del self.sales_list[index]
                self.tableWidget.removeRow(index)
                self.recalculate_total()
        self.recalculate_total()
    def recalculate_total(self):
        total = 0
        for _, qty, prix_final in self.sales_list:
            total += qty * prix_final
        self.total_label.setText(f"{total:.2f}")

    def clear_sales_table(self):
        self.tableWidget.setRowCount(0)
        self.sales_list.clear()
        #self.total_label.setText("0")
        self.recalculate_total()
    def perform_sale(self, bar_code, qty):
        try:
            self.cursor.execute("""
                UPDATE produit
                SET quantity = quantity - %s
                WHERE bar_code = %s AND quantity >= %s
            """, (qty, bar_code, qty))
            self.connection.commit()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Erreur lors de la mise à jour: {e}")
    def load_produits_into_table(self):
        try:
            self.cursor.execute("SELECT * FROM vue_produit_en_temps_reel")
            produits = self.cursor.fetchall()

            headers = [desc[0] for desc in self.cursor.description]  # Column names from the view

            self.tableWidget_1.setColumnCount(len(headers))
            self.tableWidget_1.setHorizontalHeaderLabels(headers)
            self.tableWidget_1.setRowCount(0)  # Clear existing rows

            for row_idx, row_data in enumerate(produits):
                self.tableWidget_1.insertRow(row_idx)
                for col_idx, value in enumerate(row_data):
                    self.tableWidget_1.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"خطأ أثناء تحميل البيانات:\n{e}")




#---------------------------------------
          
            
    def load_marques(self):
        try:
            self.comboBox_2.clear()
            self.cursor.execute("SELECT DISTINCT marque FROM produit")
            marques = self.cursor.fetchall()
            self.comboBox_2.addItem("")  # Empty for optional
            for marque in marques:
                self.comboBox_2.addItem(marque[0])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load marques:\n{str(e)}")

    def search_item(self):
        bar_code = self.lineEdit_9.text().strip()
        marque = self.comboBox_2.currentText().strip()

        query = "SELECT bar_code, designation, marque, category, prix_achat, prix_vende,img_path ,quantity FROM produit WHERE 1=1"
        params = []

        if bar_code:
            query += " AND bar_code ILIKE %s"
            params.append(bar_code)
        if marque:
            query += " AND marque ILIKE %s"
            params.append(marque)

        try:
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            self.display_results(results)
        except Exception as e:
            QMessageBox.critical(self, "Search Error", str(e))

    def display_results(self, results):
        self.tableWidget_1.setRowCount(0)
        for row_idx, row_data in enumerate(results):
            self.tableWidget_1.insertRow(row_idx)
            for col_idx, value in enumerate(row_data):
                self.tableWidget_1.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

            try:
                quantity = float(row_data[7])  # Index 7 corresponds to `quantity`
                if quantity <= 5:
                    for col in range(self.tableWidget_1.columnCount()):
                        self.tableWidget_1.item(row_idx, col).setBackground(QColor(255, 150, 150))  # Light red
            except (IndexError, ValueError):
                continue  # If data is missing or invalid, skip coloring

    def search_ventes_by_date(self):
        selected_date = self.dateEdit.date().toPyDate()

        try:
            
            self.cursor.execute("""
                SELECT id, bar_code, designation, quantity_sold, prix_vende, total_vente, date_vente
                FROM ventes
                WHERE DATE(date_vente) = %s
                ORDER BY date_vente DESC
            """, (selected_date,))
            rows = self.cursor.fetchall()

            self.tableWidget_2.setRowCount(0)
            self.tableWidget_2.setColumnCount(7)
            headers = ["ID", "Code Barre", "Désignation", "Quantité Vendue", "Prix Vente", "Total Vente", "Date"]
            self.tableWidget_2.setHorizontalHeaderLabels(headers)

            for row_idx, row_data in enumerate(rows):
                self.tableWidget_2.insertRow(row_idx)
                for col_idx, value in enumerate(row_data):
                    self.tableWidget_2.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))



        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la recherche des ventes:\n{e}")

    def get_selected_date(self):
        return self.calendarWidget.selectedDate().toPyDate()

    
    def show_profit_in_label(self, query, params, label_text):
        try:
            
            self.cursor.execute(query, params)
            profit = self.cursor.fetchone()[0] or 0
            self.label_4.setText(f"{label_text}: {profit:.2f} Dinars")
            
        except Exception as e:
            self.label_4.setText(f"Erreur: {e}")

    # Profit per day
    def show_profit_day(self):
        date = self.get_selected_date()
        query = """
            SELECT SUM((v.prix_vende - p.prix_achat) * v.quantity_sold)
            FROM ventes v
            JOIN produit p ON v.bar_code = p.bar_code
            WHERE DATE(v.date_vente) = %s
        """
        self.show_profit_in_label(query, (date,), f"مرابيح اليوم {date}")
        self.show_total_day()
    # Profit per week
    def show_profit_week(self):
        date = self.get_selected_date()
        start = date - timedelta(days=date.weekday())     # Monday
        end = start + timedelta(days=6)                    # Sunday
        query = """
            SELECT SUM((v.prix_vende - p.prix_achat) * v.quantity_sold)
            FROM ventes v
            JOIN produit p ON v.bar_code = p.bar_code
            WHERE DATE(v.date_vente) BETWEEN %s AND %s
        """
        self.show_profit_in_label(query, (start, end), f"مرابيح الأسبوع {start} → {end}")
        self.show_total_week()
    # Profit per month
    def show_profit_month(self):
        date = self.get_selected_date()
        query = """
            SELECT SUM((v.prix_vende - p.prix_achat) * v.quantity_sold)
            FROM ventes v
            JOIN produit p ON v.bar_code = p.bar_code
            WHERE EXTRACT(MONTH FROM v.date_vente) = %s AND EXTRACT(YEAR FROM v.date_vente) = %s
        """
        self.show_profit_in_label(query, (date.month, date.year), f"مرابيح شهر {date.month}/{date.year}")
        self.show_total_month()
    # Profit per year
    def show_profit_year(self):
        date = self.get_selected_date()
        query = """
            SELECT SUM((v.prix_vende - p.prix_achat) * v.quantity_sold)
            FROM ventes v
            JOIN produit p ON v.bar_code = p.bar_code
            WHERE EXTRACT(YEAR FROM v.date_vente) = %s
       """
        self.show_profit_in_label(query, (date.year,), f"مرابيح السنة {date.year}")
        self.show_total_year()



    def display_selected_image(self, row, column):
        try:
            bar_code_item = self.tableWidget.item(row, 1)
            if not bar_code_item:
                self.image_label.setText("❌ No barcode found")
                return
            bar_code = bar_code_item.text()
            
            product = self.get_product_by_barcode(bar_code)
            if product:
                _, _, _, _, _, _, img_path, _ = product
                pixmap = self.load_pixmap_with_exif(img_path)
                if not pixmap.isNull():
                    self.image_label.setPixmap(pixmap.scaled(
                        self.image_label.width(),
                        self.image_label.height(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    ))
                else:
                    self.image_label.setText("❌ Image not found")
            else:
                self.image_label.setText("❌ Product not found")

        except Exception as e:
            self.image_label.setText(f"❌ Error loading image: {e}")

    def display_selected_image_1(self, row, column):
        try:
            bar_code_item = self.tableWidget_1.item(row, 0)
            if not bar_code_item:
                self.image_label_1.setText("❌ No barcode found")
                return
            bar_code = bar_code_item.text()
            
            product = self.get_product_by_barcode(bar_code)
            if product:
                _, _, _, _, _, _, img_path, _ = product
                pixmap = self.load_pixmap_with_exif(img_path)
                if not pixmap.isNull():
                    self.image_label_1.setPixmap(pixmap.scaled(
                        self.image_label_1.width(),
                        self.image_label_1.height(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    ))
                else:
                    self.image_label_1.setText("❌ Image not found")
            else:
                self.image_label_1.setText("❌ Product not found")

        except Exception as e:
            self.image_label_1.setText(f"❌ Error loading image: {e}")


    def show_image_popup(self, img_path, title="صورة المنتج"):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout()

        pixmap = QPixmap(img_path)
        label = QLabel()
        if not pixmap.isNull():
            label.setPixmap(pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            label.setText("❌ الصورة غير موجودة")

        layout.addWidget(label)
        dialog.setLayout(layout)
        dialog.exec()

    def browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "اختيار صورة المنتج", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.lineEdit_24.setText(file_path)
            self.lineEdit_31.setText(file_path)
    def add_product_to_db(self):
        try:
            # === Get values from UI ===
            bar_code = self.lineEdit_22.text().strip()
            designation = self.lineEdit_25.text().strip()
            marque = self.lineEdit_3.text().strip()
            category = self.lineEdit_4.currentText().strip()
            prix_achat_str = self.lineEdit_23.text().strip()
            prix_vente_str = self.lineEdit_26.text().strip()
            quantity_str = self.lineEdit_2.text().strip()
            img_path = self.lineEdit_24.text().strip()

        # === Empty fields check ===
            if not all([bar_code, designation, marque, category, prix_achat_str, prix_vente_str, quantity_str]):
                QMessageBox.warning(self, "خطأ", "❌ الرجاء ملء جميع الحقول المطلوبة.")
                return

        # === Validate category ===
            valid_categories = ['piece', 'kg', 'm']
            if category not in valid_categories:
                QMessageBox.warning(
                    self,
                    "خطأ في الفئة",
                    f"❌ الفئة غير صالحة. يجب أن تكون واحدة من: {', '.join(valid_categories)}"
                )
                return

        # === Convert and validate numeric values ===
            try:
                prix_achat = float(prix_achat_str)
                prix_vente = float(prix_vente_str)
                quantity = int(quantity_str)

                if prix_achat < 0 or prix_vente < 0:
                    QMessageBox.warning(self, "خطأ في السعر", "❌ السعر يجب أن يكون عددًا موجبًا.")
                    return

                if prix_vente < prix_achat:
                    QMessageBox.warning(self, "تحذير", "❌ السعر النهائي أقل من رأس المال.")
                    return

                if quantity < 0:
                    QMessageBox.warning(self, "خطأ في الكمية", "❌ الكمية يجب أن تكون صفر أو أكثر.")
                    return
 
            except ValueError:
                QMessageBox.warning(
                    self,
                    "خطأ في القيم",
                    "❌ تأكد من إدخال أرقام صحيحة في السعر أو الكمية."
                )
                return

            # === Execute INSERT ===
            self.cursor.execute("""
                INSERT INTO produit (
                    bar_code, designation, marque, category,
                    prix_achat, prix_vende, img_path, quantity
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                bar_code, designation, marque, category,
                prix_achat, prix_vente, img_path, quantity
            ))

            self.connection.commit()

        # === Success ===
            QMessageBox.information(self, "تم", "✅ تم إضافة المنتج بنجاح.")
            self.clear_inputs()
            self.load_produits_into_table()

    # === Duplicate Barcode ===
        except psycopg2.errors.UniqueViolation:
            self.connection.rollback()
            QMessageBox.critical(self, "تكرار", "❌ الرمز الشريطي موجود بالفعل.")

    # === SQL Error ===
        except psycopg2.Error as e:
            self.connection.rollback()
            QMessageBox.critical(self, "خطأ في قاعدة البيانات", f"❌ {e.pgerror}")

    # === Other unexpected errors ===
        except Exception as e:
            self.connection.rollback()
            QMessageBox.critical(self, "خطأ غير متوقع", f"❌ {str(e)}")

#--------------------update-------------------------------

    def update_product_in_db(self):
        try:
        # === Get values from UI ===
            bar_code = self.lineEdit_28.text().strip()
            designation = self.lineEdit_27.text().strip()
            marque = self.lineEdit_5.text().strip()
            category = self.lineEdit_6.currentText().strip()
            prix_achat_str = self.lineEdit_29.text().strip()
            prix_vente_str = self.lineEdit_30.text().strip()
            quantity_str = self.lineEdit.text().strip()
            img_path = self.lineEdit_31.text().strip()

        # === Empty fields check ===
            if not all([bar_code, designation, marque, category, prix_achat_str, prix_vente_str, quantity_str]):
                QMessageBox.warning(self, "خطأ", "❌ الرجاء ملء جميع الحقول المطلوبة.")
                return

        # === Validate category ===
            valid_categories = ['piece', 'kg', 'm']
            if category not in valid_categories:
                QMessageBox.warning(
                    self,
                    "خطأ في الفئة",
                    f"❌ الفئة غير صالحة. يجب أن تكون واحدة من: {', '.join(valid_categories)}"
                )
                return

        # === Convert and validate numeric values ===
            try:
                prix_achat = float(prix_achat_str)
                prix_vente = float(prix_vente_str)
                quantity = float(quantity_str)

                if prix_achat < 0 or prix_vente < 0:
                    QMessageBox.warning(self, "خطأ في السعر", "❌ السعر يجب أن يكون عددًا موجبًا.")
                    return

                if prix_vente < prix_achat:
                    QMessageBox.warning(self, "تحذير", "❌ السعر النهائي أقل من رأس المال.")
                    return

                if quantity <= 0:
                    QMessageBox.warning(self, "خطأ في الكمية", "❌ الكمية يجب أن تكون صفر أو أكثر.")
                    return

            except ValueError:
                QMessageBox.warning(
                    self,
                    "خطأ في القيم",
                    "❌ تأكد من إدخال أرقام صحيحة في السعر أو الكمية."
                )
                return

        # === Check if product exists ===
            self.cursor.execute("SELECT 1 FROM produit WHERE bar_code = %s", (bar_code,))
            if not self.cursor.fetchone():
                QMessageBox.warning(self, "غير موجود", "❌ المنتج غير موجود في قاعدة البيانات.")
                return

        # === Execute UPDATE ===
            self.cursor.execute("""
                UPDATE produit SET
                    designation = %s,
                    marque = %s,
                    category = %s,
                    prix_achat = %s,
                    prix_vende = %s,
                    img_path = %s,
                    quantity = %s
                WHERE bar_code = %s
            """, (
                designation, marque, category,
                prix_achat, prix_vente, img_path, quantity, bar_code
            ))

            self.connection.commit()

        # === Success ===
            QMessageBox.information(self, "تم", "✅ تم تحديث المنتج بنجاح.")
            self.clear_inputs()
            self.load_produits_into_table()
            self.load_marques()

    # === SQL Error ===
        except psycopg2.Error as e:
            self.connection.rollback()
            QMessageBox.critical(self, "خطأ في قاعدة البيانات", f"❌ {e.pgerror}")

    # === Other unexpected errors ===
        except Exception as e:
            self.connection.rollback()
            QMessageBox.critical(self, "خطأ غير متوقع", f"❌ {str(e)}")

        


    def clear_inputs(self):
        self.lineEdit_22.clear()
        self.lineEdit_25.clear()
        self.lineEdit_3.clear()
        self.lineEdit_4.clear()
        self.lineEdit_23.clear()
        self.lineEdit_26.clear()
        self.lineEdit_2.clear()
        self.lineEdit_24.clear()
        
        self.lineEdit_28.clear()
        self.lineEdit_27.clear()
        self.lineEdit_5.clear()
        self.lineEdit_6.clear()
        self.lineEdit_29.clear()
        self.lineEdit_30.clear()
        self.lineEdit.clear()
        self.lineEdit_31.clear()

    def load_facture_details_by_date(self):

        facture_id_text = self.lineEdit_7.text().strip()
        selected_date = self.dateEdit_2.date().toPyDate()

        try:
                # Determine query based on input
                if facture_id_text:
                        self.cursor.execute("""
                                SELECT f.id, v.bar_code, v.designation, v.quantity_sold, v.prix_vende, v.total_vente, f.total
                                FROM facture f
                                JOIN ventes v ON f.id = v.facture_id
                                WHERE f.id = %s
                                ORDER BY v.designation
                        """, (facture_id_text,))
                else:
                        self.cursor.execute("""
                                SELECT f.id, v.bar_code, v.designation, v.quantity_sold, v.prix_vende, v.total_vente, f.total
                                FROM facture f
                                JOIN ventes v ON f.id = v.facture_id
                                WHERE DATE(f.date_facture) = %s
                                ORDER BY f.id, v.designation
                        """, (selected_date,))

                rows = self.cursor.fetchall()

                # Set up the table
                self.tableWidget_3.setRowCount(0)
                self.tableWidget_3.setColumnCount(7)
                headers = ["رقم الفاتورة", "الباركود", "المنتج", "الكمية", "سعر البيع", "المجموع", "إجمالي الفاتورة"]
                self.tableWidget_3.setHorizontalHeaderLabels(headers)

                # Fill the table
                last_facture_id = None
                for row_idx, row_data in enumerate(rows):
                        self.tableWidget_3.insertRow(row_idx)
                        for col_idx, value in enumerate(row_data):
                                # Only show 'total invoice' once per facture
                                if col_idx == 6 and row_data[0] == last_facture_id:
                                        self.tableWidget_3.setItem(row_idx, col_idx, QTableWidgetItem(""))
                                else:
                                        item = QTableWidgetItem(str(value))
                                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                                        self.tableWidget_3.setItem(row_idx, col_idx, item)
                        last_facture_id = row_data[0]

                if not rows:
                        QMessageBox.information(self, "لا توجد فواتير", "❌ لا توجد نتائج حسب البيانات المدخلة.")

        except Exception as e:
                QMessageBox.critical(self, "خطأ", f"❌ فشل في تحميل تفاصيل الفواتير:\n{e}")

    def show_total_in_label_5(self, query, params, label_text):
        try:
            self.cursor.execute(query, params)
            total = self.cursor.fetchone()[0] or 0
            self.label_5.setText(f"{label_text}: {total:.2f} Dinars")
        except Exception as e:
            self.label_5.setText(f"Erreur: {e}")

    # Total sales per day
    def show_total_day(self):
        date = self.get_selected_date()
        query = """
            SELECT SUM(v.prix_vende * v.quantity_sold)
            FROM ventes v
            WHERE DATE(v.date_vente) = %s
        """
        self.show_total_in_label_5(query, (date,), f"مداخيل اليوم {date}")

    # Total sales per week
    def show_total_week(self):
        date = self.get_selected_date()
        start = date - timedelta(days=date.weekday())  # Monday
        end = start + timedelta(days=6)               # Sunday
        query = """
            SELECT SUM(v.prix_vende * v.quantity_sold)
            FROM ventes v
            WHERE DATE(v.date_vente) BETWEEN %s AND %s
        """
        self.show_total_in_label_5(query, (start, end), f"مداخيل الأسبوع {start} → {end}")

    # Total sales per month
    def show_total_month(self):
        date = self.get_selected_date()
        query = """
            SELECT SUM(v.prix_vende * v.quantity_sold)
            FROM ventes v
            WHERE EXTRACT(MONTH FROM v.date_vente) = %s AND EXTRACT(YEAR FROM v.date_vente) = %s
        """
        self.show_total_in_label_5(query, (date.month, date.year), f"مداخيل شهر {date.month}/{date.year}")

    # Total sales per year
    def show_total_year(self):
        date = self.get_selected_date()
        query = """
            SELECT SUM(v.prix_vende * v.quantity_sold)
            FROM ventes v
            WHERE EXTRACT(YEAR FROM v.date_vente) = %s
        """
        self.show_total_in_label_5(query, (date.year,), f"مداخيل السنة {date.year}")





    def load_pixmap_with_exif(self,img_path):
        try:
                pil_img = Image.open(img_path)

                # Fix orientation
                try:
                        for orientation in ExifTags.TAGS.keys():
                                if ExifTags.TAGS[orientation] == "Orientation":
                                        break
                        exif = pil_img._getexif()
                        if exif and orientation in exif:
                                if exif[orientation] == 3:
                                        pil_img = pil_img.rotate(180, expand=True)
                                elif exif[orientation] == 6:
                                        pil_img = pil_img.rotate(270, expand=True)
                                elif exif[orientation] == 8:
                                        pil_img = pil_img.rotate(90, expand=True)
                except Exception:
                        pass  # ignore if no EXIF

                if pil_img.mode != "RGB":
                        pil_img = pil_img.convert("RGB")

                data = pil_img.tobytes("raw", "RGB")
                qimage = QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGB888)
                return QPixmap.fromImage(qimage)
        except Exception:
                return QPixmap("no_image.png")





def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
