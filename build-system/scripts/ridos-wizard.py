#!/usr/bin/env python3
import sys
import os
from PyQt6.QtWidgets import (QApplication, QWizard, QWizardPage, 
                             QLabel, QVBoxLayout, QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt

class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("مرحباً بك في RIDOS OS")
        layout = QVBoxLayout()
        # دعم الكتابة من اليمين لليسار للعربية
        label = QLabel("أهلاً بك في نسخة 'بغداد+' v1.1.1. هذا النظام مزود بذكاء اصطناعي متكامل لمساعدتك في مهامك التقنية.")
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(label)
        self.setLayout(layout)

class APIConfigPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("إعداد مفتاح الذكاء الاصطناعي")
        layout = QVBoxLayout()
        
        self.label = QLabel("يرجى إدخال مفتاح API الخاص بك (Google Gemini هو الموصى به حالياً):")
        self.label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("أدخل المفتاح هنا...")
        self.api_input.setEchoMode(QLineEdit.EchoMode.Password) # لإخفاء المفتاح أثناء الكتابة لأمان أكثر
        
        self.save_btn = QPushButton("حفظ المفتاح وتفعيل المساعد")
        self.save_btn.clicked.connect(self.save_key)
        
        layout.addWidget(self.label)
        layout.addWidget(self.api_input)
        layout.addWidget(self.save_btn)
        self.setLayout(layout)

    def save_key(self):
        key = self.api_input.text().strip()
        if key:
            try:
                # حفظ في .bashrc للمستخدم الحالي
                bashrc_path = os.path.expanduser("~/.bashrc")
                with open(bashrc_path, "a") as f:
                    f.write(f'\nexport RIDOS_API_KEY="{key}"\n')
                
                # إنشاء ملف إشارة لعدم تكرار تشغيل المعالج
                with open(os.path.expanduser("~/.ridos_setup_done"), "w") as f:
                    f.write("done")
                    
                QMessageBox.information(self, "نجاح", "تم تفعيل المساعد الذكي بنجاح. يرجى إعادة تشغيل الـ Terminal لتفعيل التغييرات.")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحفظ: {str(e)}")
        else:
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال المفتاح أولاً.")

class RidosWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("إعداد RIDOS OS")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        
        # إضافة الصفحات
        self.addPage(WelcomePage())
        self.addPage(APIConfigPage())
        
        self.resize(500, 350)
        # جعل النافذة تظهر في المنتصف
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # ضبط اتجاه التطبيق للعربية
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    wizard = RidosWizard()
    wizard.show()
    sys.exit(app.exec())
