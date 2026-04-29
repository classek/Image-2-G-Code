import sys
import numpy as np
from PIL import Image, ImageEnhance, ImageOps
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QFileDialog, QVBoxLayout, QHBoxLayout, QSlider,
    QDoubleSpinBox, QSpinBox, QTabWidget, QTextEdit,
    QComboBox, QDialog, QCheckBox, QGroupBox
)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt

class LaserProV12_9(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Image 2 G-Code")
        self.resize(1450, 950)
        
        # --- Inställningar ---
        self.lang = "English"
        self.dark_mode = False
        self.original = None
        self.preview_arr = None

        self.init_ui()
        self.apply_theme()
        self.update_labels()

    def apply_theme(self):
        if self.dark_mode:
            bg, fg, accent = "#1e1e1e", "#e0e0e0", "#bb86fc"
            btn_bg, edit_bg = "#3d3d3d", "#2b2b2b"
        else:
            bg, fg, accent = "#f5f5f5", "#202020", "#6200ee"
            btn_bg, edit_bg = "#e0e0e0", "#ffffff"

        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {bg}; }}
            QWidget {{ color: {fg}; font-family: 'Segoe UI'; font-size: 13px; }}
            QGroupBox {{ border: 1px solid #999; margin-top: 15px; font-weight: bold; padding-top: 10px; }}
            QPushButton {{ background-color: {btn_bg}; border: 1px solid #bbb; padding: 8px; border-radius: 4px; }}
            QSlider::handle:horizontal {{ background: {accent}; width: 18px; border-radius: 9px; }}
            QTextEdit {{ background-color: {edit_bg}; color: {fg}; }}
        """)

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # --- KONTROLLPANEL (VÄNSTER) ---
        self.left_panel = QVBoxLayout()
        self.left_widget = QWidget()
        self.left_widget.setFixedWidth(400)
        
        # Topprad: Språk & Tema
        top_bar = QHBoxLayout()
        self.lang_box = QComboBox()
        self.lang_box.addItems(["English", "Svenska"])
        self.lang_box.currentTextChanged.connect(self.change_lang)
        self.btn_theme = QPushButton("Toggle Theme")
        self.btn_theme.clicked.connect(self.toggle_theme)
        top_bar.addWidget(self.lang_box)
        top_bar.addWidget(self.btn_theme)
        self.left_panel.addLayout(top_bar)

        # Arkiv
        self.file_group = QGroupBox()
        file_layout = QVBoxLayout(self.file_group)
        self.btn_load = QPushButton(); self.btn_load.clicked.connect(self.load)
        self.btn_help = QPushButton(); self.btn_help.clicked.connect(self.show_manual)
        file_layout.addWidget(self.btn_load)
        file_layout.addWidget(self.btn_help)
        self.left_panel.addWidget(self.file_group)

        # Flikar för inställningar
        self.tabs = QTabWidget()
        
        # --- FLIK 1: BILD ---
        self.img_tab = QWidget(); img_lay = QVBoxLayout(self.img_tab)
        
        self.lbl_width = QLabel(); img_lay.addWidget(self.lbl_width)
        self.width_slider, self.width_spin = self.add_slider(img_lay, 10, 500, 100, True)
        
        self.lbl_gamma = QLabel(); img_lay.addWidget(self.lbl_gamma)
        self.gamma_slider, self.gamma_spin = self.add_slider(img_lay, 0.5, 3.0, 1.2)
        
        self.lbl_sharp = QLabel(); img_lay.addWidget(self.lbl_sharp)
        self.sharp_slider, self.sharp_spin = self.add_slider(img_lay, 1.0, 5.0, 1.5)
        
        img_lay.addStretch()
        self.tabs.addTab(self.img_tab, "Image")

        # --- FLIK 2: MASKIN ---
        self.mac_tab = QWidget(); mac_lay = QVBoxLayout(self.mac_tab)
        
        self.lbl_maxs = QLabel(); mac_lay.addWidget(self.lbl_maxs)
        self.maxs_slider, self.maxs_spin = self.add_slider(mac_lay, 1, 1000, 1000, True)
        
        self.lbl_feed = QLabel(); mac_lay.addWidget(self.lbl_feed)
        self.feed_slider, self.feed_spin = self.add_slider(mac_lay, 100, 8000, 1200, True)
        
        self.lbl_oscan = QLabel(); mac_lay.addWidget(self.lbl_oscan)
        self.oscan_slider, self.oscan_spin = self.add_slider(mac_lay, 0, 20, 2.5)
        
        self.lbl_cut = QLabel(); mac_lay.addWidget(self.lbl_cut)
        self.cut_slider, self.cut_spin = self.add_slider(mac_lay, 150, 255, 245, True)
        
        self.check_serp = QCheckBox(); self.check_serp.setChecked(True)
        mac_lay.addWidget(self.check_serp)
        
        mac_lay.addStretch()
        self.tabs.addTab(self.mac_tab, "Machine")
        
        self.left_panel.addWidget(self.tabs)

        # Invertering (Alltid synlig)
        self.check_invert = QCheckBox(); self.check_invert.setChecked(True)
        self.check_invert.stateChanged.connect(self.update_preview)
        self.left_panel.addWidget(self.check_invert)

        # Spara-knapp
        self.btn_save = QPushButton(); self.btn_save.setFixedHeight(50)
        self.btn_save.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white;")
        self.btn_save.clicked.connect(self.save)
        self.left_panel.addWidget(self.btn_save)

        self.left_widget.setLayout(self.left_panel)
        self.main_layout.addWidget(self.left_widget)

        # --- FÖRHANDSVISNING (HÖGER) ---
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("border: 1px solid #999; background-color: #333;")
        self.main_layout.addWidget(self.preview, 1)

    def add_slider(self, layout, minv, maxv, start, int_mode=False):
        row = QHBoxLayout()
        slider = QSlider(Qt.Horizontal)
        spin = QSpinBox() if int_mode else QDoubleSpinBox()
        if int_mode:
            slider.setRange(int(minv), int(maxv)); spin.setRange(int(minv), int(maxv))
            slider.setValue(int(start)); spin.setValue(int(start))
        else:
            slider.setRange(int(minv*100), int(maxv*100)); spin.setRange(minv, maxv)
            spin.setDecimals(2); slider.setValue(int(start*100)); spin.setValue(start)
        
        def s_ch():
            v = slider.value() if int_mode else slider.value()/100
            spin.blockSignals(True); spin.setValue(v); spin.blockSignals(False); self.update_preview()
        def sp_ch():
            v = spin.value()
            slider.blockSignals(True); slider.setValue(int(v) if int_mode else int(v*100)); slider.blockSignals(False); self.update_preview()
            
        slider.valueChanged.connect(s_ch); spin.valueChanged.connect(sp_ch)
        row.addWidget(slider); row.addWidget(spin); layout.addLayout(row)
        return slider, spin

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode; self.apply_theme()

    def change_lang(self, val):
        self.lang = val; self.update_labels()

    def update_labels(self):
        t = {
            "Svenska": {
                "file_grp": "1. ARKIV", "load": "ÖPPNA BILD", "save": " GENERERA G-KOD", "help": "MANUAL",
                "width": "BREDD (Fysiskt mått i mm):", "gamma": "GAMMA (Kontrast/Mellantoner):", "sharp": "SKÄRPA (Kantförstärkning):",
                "maxs": "MAX LASEREFFEKT (S-värde):", "feed": "BRÄNNFART (G1 mm/min):", "oscan": "OVERSCAN (Säkerhetsmarginal mm):",
                "cut": "VIT-GRÄNS (Cutoff):", "inv": "Auto-Invertera mörka hörn", "serp": "Sicksack-bränning (Serpentine)",
                "tab_img": " Bild", "tab_mac": " Maskin"
            },
            "English": {
                "file_grp": "1. FILE MANAGEMENT", "load": "OPEN IMAGE", "save": " GENERATE G-CODE", "help": "MANUAL",
                "width": "WIDTH (Physical size in mm):", "gamma": "GAMMA (Brightness/Contrast):", "sharp": "SHARPNESS (Edge boost):",
                "maxs": "MAX LASER POWER (S-value):", "feed": "BURN SPEED (G1 mm/min):", "oscan": "OVERSCAN (Safety Margin mm):",
                "cut": "WHITE CUTOFF (Threshold):", "inv": "Auto-Invert dark corners", "serp": "Serpentine (Zigzag Mode)",
                "tab_img": "Image", "tab_mac": "Machine"
            }
        }[self.lang]
        
        self.file_group.setTitle(t["file_grp"]); self.btn_load.setText(t["load"]); self.btn_save.setText(t["save"]); self.btn_help.setText(t["help"])
        self.lbl_width.setText(t["width"]); self.lbl_gamma.setText(t["gamma"]); self.lbl_sharp.setText(t["sharp"])
        self.lbl_maxs.setText(t["maxs"]); self.lbl_feed.setText(t["feed"]); self.lbl_oscan.setText(t["oscan"])
        self.lbl_cut.setText(t["cut"]); self.check_invert.setText(t["inv"]); self.check_serp.setText(t["serp"])
        self.tabs.setTabText(0, t["tab_img"]); self.tabs.setTabText(1, t["tab_mac"])

    def load(self):
        path, _ = QFileDialog.getOpenFileName()
        if not path: return
        img = Image.open(path)
        if img.mode in ('RGBA', 'LA'):
            bg = Image.new("RGB", img.size, (255, 255, 255)); bg.paste(img, mask=img.split()[-1]); img = bg
        self.original = img.convert("RGB"); self.update_preview()

    def update_preview(self):
        if not self.original: return
        img = self.original.copy()
        if self.check_invert.isChecked():
            if np.mean(np.array(img.convert("L"))[:20, :20]) < 100: img = ImageOps.invert(img)
        img = ImageOps.autocontrast(img).convert("L")
        img = ImageEnhance.Sharpness(img).enhance(self.sharp_spin.value())
        arr = np.array(img)/255.0; arr = (np.power(arr, self.gamma_spin.value())*255).astype(np.uint8)
        self.preview_arr = arr; h, w = arr.shape
        qimg = QImage(arr.data, w, h, w, QImage.Format_Grayscale8)
        pix = QPixmap.fromImage(qimg).scaled(self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview.setPixmap(pix)

    def save(self):
        if self.preview_arr is None: return
        path, _ = QFileDialog.getSaveFileName(filter="Gcode (*.nc)")
        if not path: return
        
        # --- STABIL V11.8 MOTOR ---
        arr = self.preview_arr; h, w = arr.shape
        px = self.width_spin.value() / w
        oscan = self.oscan_spin.value()
        f_b = self.feed_spin.value()
        max_s = self.maxs_spin.value()
        cut = self.cut_spin.value()
        serp = self.check_serp.isChecked()

        with open(path, "w") as f:
            f.write("(LaserPro v12.9 - Safe Boundary)\nG21\nG90\nM4\n")
            for y in range(h):
                y_mm = y * px
                is_rev = serp and (y % 2 == 1)
                margin = oscan
                start_x, end_x, dir_m = (margin, (w-1)*px+margin, 1) if not is_rev else ((w-1)*px+margin, margin, -1)
                f.write(f"G0 X{start_x-(oscan*dir_m):.3f} Y{y_mm:.3f} F10000\n")
                f.write(f"G1 X{start_x:.3f} S0 F{f_b}\n")
                active, last_s = False, -1
                xs = range(w) if not is_rev else range(w-1, -1, -1)
                for x in xs:
                    val = arr[h-1-y, x]; x_pos = (x * px) + margin
                    s = int(((255-val)/255.0)**1.4 * max_s)
                    if val >= cut:
                        if active: f.write(f"G1 X{x_pos:.3f} S0\n"); active, last_s = False, 0
                        continue
                    if not active: f.write(f"G1 X{x_pos:.3f} S0\n"); active = True
                    if s != last_s: f.write(f"G1 X{x_pos:.3f} S{s}\n"); last_s = s
                f.write(f"G1 X{end_x:.3f} S0\nG1 X{end_x+(oscan*dir_m):.3f} S0\n")
            f.write("G0 X0 Y0 F10000\nM5\nM2\n")
        messagebox = QDialog(self); messagebox.setWindowTitle("Done")
        QVBoxLayout(messagebox).addWidget(QLabel("G-code saved successfully!")); messagebox.show()

    def show_manual(self):
        self.mw = QDialog(self); self.mw.setWindowTitle("Manual")
        self.mw.resize(900, 800)
        l = QVBoxLayout(self.mw); t = QTextEdit(); t.setReadOnly(True)
        
        sw = """
        <h1 style='color: #6200ee;'>Bruksanvisning LaserPro</h1>
        
        <h3>1. Filhantering & System</h3>
        <p><b>Language (Språk):</b> Växlar mellan engelska och svenska. All text i gränssnittet ändras direkt.</p>
        <p><b>Dark Mode:</b> Byter färgtema på appen. Det ljusa läget är standard, mörkt läge sparar ögonen.</p>
        <p><b>Open Image (Ladda bild):</b> Importerar din bild. Programmet har en inbyggd Alpha-fix som gör genomskinliga bakgrunder helt vita.</p>
        <p><b>Auto-fix background:</b> En smart sensor som känner av mörka ramar och inverterar bilden automatiskt så att bakgrunden blir vit.</p>

        <h3>2. Bildinställningar</h3>
        <p><b>Width (Bredd mm):</b> Bestämmer hur stor graveringen blir i verkligheten. Höjden räknas ut automatiskt.</p>
        <p><b>Gamma (Kontrast):</b> Avgörande för trä. Lågt värde ger ljusare bild, högt värde framhäver mörka partier (1.2–1.4 rekommenderas).</p>
        <p><b>Sharpness (Skärpa):</b> Förstärker kanterna så att text och detaljer syns tydligare.</p>

        <h3>3. Maskinparametrar (G-kod)</h3>
        <p><b>Max S (Lasereffekt):</b> Maxvärdet för lasern (ofta 1000). Motsvarar 100% styrka.</p>
        <p><b>Burn Speed (G1):</b> Hastighet vid bränning (mm/min). Långsammare = mörkare bränning.</p>
        <p><b>Rapid Speed (G0):</b> Hastighet vid transport utan bränning. Sparar tid.</p>
        <p><b>Overscan (Marginal mm):</b> Proffsfunktion som låter maskinen accelerera utanför bilden för jämna kanter utan brännmärken.</p>
        <p><b>White Cutoff (Vit-gräns):</b> Hoppar över pixlar som är nästan vita för renare resultat och snabbare körning.</p>
        <p><b>Serpentine (Sicksack):</b> Bränner åt båda hållen för att halvera arbetstiden.</p>

        <h3>Hur säkerhetsmarginalen fungerar</h3>
        <p>Programmet har en dold "Safety Origin"-funktion. Om du ställer in 2.5 mm Overscan, flyttar programmet automatiskt hela bilden 2.5 mm åt höger i koordinatsystemet. Detta gör att accelerationen sker på X0 istället för ett negativt värde, vilket förhindrar felmeddelanden i LaserGRBL.</p>
        """
        
        en = """
        <h1 style='color: #6200ee;'>User Manual LaserPro</h1>
        
        <h3>1. File Management & System</h3>
        <p><b>Language:</b> Toggles between English and Swedish. All text updates immediately.</p>
        <p><b>Dark Mode:</b> Switches the app theme. Light mode is default, Dark mode is easier on the eyes.</p>
        <p><b>Open Image:</b> Imports your image. Built-in Alpha-fix makes transparent backgrounds white.</p>
        <p><b>Auto-fix background:</b> Smart sensor that detects dark frames and inverts the image to ensure a white background.</p>

        <h3>2. Image Settings</h3>
        <p><b>Width (mm):</b> Defines physical engraving size. Height is calculated automatically.</p>
        <p><b>Gamma (Contrast):</b> Critical for wood. Low value = lighter, high value = darker details (1.2–1.4 recommended).</p>
        <p><b>Sharpness:</b> Enhances edges to make text and details pop.</p>

        <h3>3. Machine Parameters (G-code)</h3>
        <p><b>Max S (Power):</b> Maximum laser value (often 1000). Represents 100% power.</p>
        <p><b>Burn Speed (G1):</b> Engraving speed (mm/min). Slower = darker burn.</p>
        <p><b>Rapid Speed (G0):</b> Travel speed when not burning. Saves time.</p>
        <p><b>Overscan (Margin mm):</b> Allows the machine to accelerate outside the image for even edges without burn marks.</p>
        <p><b>White Cutoff:</b> Skips near-white pixels for cleaner results and faster operation.</p>
        <p><b>Serpentine:</b> Engraves in both directions to cut job time in half.</p>

        <h3>How the Safety Margin Works</h3>
        <p>The program features a hidden "Safety Origin" function. If you set 2.5 mm Overscan, the software automatically offsets the entire image 2.5 mm to the right. This ensures acceleration happens at X0 instead of a negative value, preventing errors in LaserGRBL.</p>
        """
        
        t.setHtml(sw if self.lang == "Svenska" else en)
        l.addWidget(t); self.mw.show()

if __name__ == "__main__":
    app = QApplication(sys.argv); win = LaserProV12_9(); win.show(); sys.exit(app.exec())