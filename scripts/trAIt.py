import sys
import os
import pandas as pd

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QMessageBox, QFileDialog,
    QTabWidget,
    QSpacerItem, QSizePolicy, QScrollArea, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRect
from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor
from PyQt5.QtWidgets import QStyleOptionProgressBar, QStyle
from pubmed_query import process_species_traits, sanity_check


class SanityCheckWorker(QThread):
    finished = pyqtSignal(object)

    def __init__(self, species_list, traits_list):
        super().__init__()
        self.species_list = species_list
        self.traits_list = traits_list

    def run(self):
        results = sanity_check(self.species_list, self.traits_list)
        self.finished.emit(results)


class ExtractionWorker(QThread):
    finished = pyqtSignal(str)
    progress = pyqtSignal(int, int)

    def __init__(self, species_list, traits_list, trait_descriptions, file_name):
        super().__init__()
        self.species_list = species_list
        self.traits_list = traits_list
        self.trait_descriptions = trait_descriptions
        self.file_name = file_name

    def run(self):
        process_species_traits(
            self.species_list, self.traits_list,
            self.file_name, self.trait_descriptions,
            progress_callback=lambda done, total: self.progress.emit(done, total)
        )
        self.finished.emit(self.file_name)


class TrailingLabelProgressBar(QProgressBar):
    """Progress bar with the % label floating above the fill edge."""

    LABEL_AREA = 22

    def paintEvent(self, event):
        opt = QStyleOptionProgressBar()
        self.initStyleOption(opt)
        opt.text = ""
        opt.textVisible = False
        painter = QPainter(self)
        self.style().drawControl(QStyle.CE_ProgressBar, opt, painter, self)

        total = self.maximum() - self.minimum()
        if total <= 0:
            return
        ratio = (self.value() - self.minimum()) / total
        fill_w = int(self.width() * ratio)

        pct = int(ratio * 100)
        label = f"{pct}%"

        fm = painter.fontMetrics()
        text_w = fm.horizontalAdvance(label)
        text_h = fm.height()
        margin = 6

        x = max(fill_w - text_w - margin, fill_w + margin)
        if fill_w - text_w - margin >= margin:
            x = fill_w - text_w - margin
        else:
            x = fill_w + margin

        y = (self.height() + text_h) // 2 - fm.descent()

        if x < fill_w:
            painter.setPen(QColor("white"))
        else:
            painter.setPen(self.palette().text().color())

        painter.drawText(x, y, label)
        painter.end()


class SpeciesTraitsApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Species & Traits Analysis")
        self.setGeometry(200, 200, 600, 500)

        self.species_path = None
        self.traits_path = None
        
        self.species_list = []
        self.traits_list = []
        self.trait_descriptions = {}
        self.output_file_name = "output_results.csv"

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.instructions_tab = QWidget()
        self.examples_tab = QWidget()
        self.upload_tab = QWidget()

        self.tabs.addTab(self.instructions_tab, "Instructions")
        self.tabs.addTab(self.examples_tab, "Examples")
        self.tabs.addTab(self.upload_tab, "Upload")

        self.show_instructions_tab()
        self.show_examples_tab()
        self.show_input_form()

    def clear_layout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def show_input_form(self):
        self.upload_layout = QVBoxLayout()
        self.upload_tab.setLayout(self.upload_layout)

        self.upload_layout.setSpacing(15)

        self.upload_layout.addSpacing(50)

        self.upload_layout.addWidget(QLabel("Upload Excel or CSV file (species + traits):"))
        self.upload_excel_csv_btn = QPushButton("Choose Excel or CSV File")
        self.upload_excel_csv_btn.clicked.connect(self.upload_excel_csv)
        self.upload_layout.addWidget(self.upload_excel_csv_btn)

        self.upload_layout.addSpacing(70)

        self.upload_layout.addWidget(QLabel("Upload Text file (trait descriptions):"))
        self.upload_traits_btn = QPushButton("Choose Trait Description File")
        self.upload_traits_btn.clicked.connect(self.upload_traits)
        self.upload_layout.addWidget(self.upload_traits_btn)

        self.upload_layout.addSpacing(70)

        self.upload_layout.addWidget(QLabel("Once both files are uploaded, click below to start extraction:"))

        self.create_button = QPushButton("Start Data Extraction")
        self.create_button.clicked.connect(self.start_extraction)
        self.upload_layout.addWidget(self.create_button)

        self.upload_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def show_instructions_tab(self):
        layout = QVBoxLayout()
        instructions = QLabel("""
        <h3>How to Use</h3>
        <p>1. Prepare an Excel or CSV file with the first column as <b>species names</b> 
        and the remaining columns as <b>traits</b>.</p>
        <ul>
            <li>Note: trait names should use plain spaces - no underscores, periods, or special characters. 
            Format them as if you were typing the trait into a Google search bar 
            (e.g., <i>body mass</i>, not <i>body_mass</i> or <i>body.mass</i>).</li>
        </ul>
        <p>2. Prepare a text file (.txt, UTF-8 encoded) listing each trait followed by a colon and its description.</p>
        <p>3. Upload both files under the <b>Upload</b> tab and click <b>Start Data Extraction</b>.</p>
        <p>The processed CSV file will be saved as <b>output_results.csv</b> in a results directory.</p>
        """)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        self.instructions_tab.setLayout(layout)

    def show_examples_tab(self):
        layout = QVBoxLayout()

        def add_example(title, filename):
            label = QLabel(f"{title}:\n-------------------")
            label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            layout.addWidget(label)

            image_label = QLabel()
            script_dir = os.path.dirname(os.path.abspath(__file__))
            image_path = os.path.join(script_dir, "..", "sample_data", f"{filename}.png")
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaledToWidth(350, Qt.SmoothTransformation)
                image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignHCenter)
            layout.addWidget(image_label)

        add_example("Example CSV Format", "example_species_csv")
        add_example("Example Excel Format", "example_species_excel")
        add_example("Example Trait Description File", "example_trait_desc")

        self.examples_tab.setLayout(layout)

    def show_sanity_loading(self):
        self.clear_layout()
        loading_label = QLabel("Running Literature Availability Assessment...\n\nChecking literature availability for your traits and species.")
        loading_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(loading_label)

    def show_sanity_results(self, trait_stats, species_stats):
        self.clear_layout()
        
        container = QWidget()
        layout = QVBoxLayout(container)

        header = QLabel("<h2>Literature Availability Results</h2>")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        explanation = QLabel(
            "If any <b>traits</b> yielded too few papers, consider revising the trait name<br>"
            "(e.g., use simpler or more common phrasing).<br>"
            "If any <b>species</b> yielded too few papers, it may be less researched —<br>"
            "consider whether to include it in your dataset.<br><br>"
            'To make these changes, click "Quit" and edit your files, then restart the application. <br>'
            'If you would like to continue with the current files, click "Proceed with Extraction".<br><br>'
            "<i>Showing the 10 lowest results below. Full results saved to <br>"
            "<b>results/literature_availability_results.txt</b>.</i>"
        )
        explanation.setAlignment(Qt.AlignCenter)
        layout.addWidget(explanation)

        self.setMinimumWidth(600)

        def make_scroll_box(stats_dict, label_fn, n_items):
            """Build a scrollable box of stat labels using label_fn(key, stats) -> str."""
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_content = QWidget()
            scroll_layout = QVBoxLayout(scroll_content)
            for key, stats in stats_dict.items():
                lbl = QLabel(label_fn(key, stats))
                scroll_layout.addWidget(lbl)
            scroll_layout.addStretch()
            scroll_area.setWidget(scroll_content)
            content_height = n_items * 35 + 40
            scroll_area.setFixedHeight(min(max(content_height, 80), 300))
            return scroll_area

        trait_header = QLabel("<b>Sources Found Per Trait</b>")
        trait_header.setAlignment(Qt.AlignLeft)
        layout.addWidget(trait_header)

        sorted_traits = dict(sorted(trait_stats.items(), key=lambda x: x[1]['mean'])[:10])
        trait_box = make_scroll_box(
            sorted_traits,
            lambda trait, s: f"<b>{trait}</b>: {s['mean']:.1f} +- {s['std_dev']:.1f} papers",
            len(sorted_traits)
        )
        layout.addWidget(trait_box)

        species_header = QLabel("<b>Sources Found Per Species</b>")
        species_header.setAlignment(Qt.AlignLeft)
        layout.addWidget(species_header)

        sorted_species = dict(sorted(species_stats.items(), key=lambda x: x[1]['mean'])[:10])
        species_box = make_scroll_box(
            sorted_species,
            lambda sp, s: f"<b>{sp}</b>: {s['mean']:.1f} +- {s['std_dev']:.1f} papers",
            len(sorted_species)
        )
        layout.addWidget(species_box)

        btn_layout = QVBoxLayout()

        proceed_btn = QPushButton("Proceed with Extraction")
        proceed_btn.clicked.connect(self.run_extraction_pipeline)
        btn_layout.addWidget(proceed_btn)

        quit_btn = QPushButton("Quit")
        quit_btn.clicked.connect(self.close)
        btn_layout.addWidget(quit_btn)

        layout.addLayout(btn_layout)
        self.layout.addWidget(container)
        self.adjustSize()
    
    def run_sanity_check(self):
        self.show_sanity_loading()
        self.sanity_worker = SanityCheckWorker(self.species_list, self.traits_list)
        self.sanity_worker.finished.connect(self.on_sanity_check_finished)
        self.sanity_worker.start()

    def on_sanity_check_finished(self, results):
        trait_stats, species_stats = results
        self.show_sanity_results(trait_stats, species_stats)

    def run_extraction_pipeline(self):
        self.show_loading(len(self.species_list), len(self.traits_list))

        self.worker = ExtractionWorker(
            self.species_list, self.traits_list,
            self.trait_descriptions, self.output_file_name
        )
        self.worker.progress.connect(lambda done, total: self.progress_bar.setValue(done))
        self.worker.finished.connect(self.on_extraction_finished)
        self.worker.start()

    def show_loading(self, total_species, total_traits):
        self.clear_layout()

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        title = QLabel("Processing... Please wait.")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        desc = QLabel("Progress bar shows the percentage of traits processed across all species.")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.progress_bar = TrailingLabelProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(total_species * total_traits)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumWidth(400)
        self.progress_bar.setFixedHeight(28)
        layout.addWidget(self.progress_bar)

        self.layout.addWidget(container)

    def show_success(self, file_name):
        self.clear_layout()
        self.layout.addWidget(QLabel(f"Success! Excel file saved as {file_name}"))
        done_button = QPushButton("Done")
        done_button.clicked.connect(self.close)
        self.layout.addWidget(done_button)

    def upload_excel_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Excel or CSV File", "", "Data Files (*.xlsx *.xls *.csv);;All Files (*)")
        if path:
            self.species_path = path
            filename = os.path.basename(path)
            self.upload_excel_csv_btn.setText(f"{filename} Selected")
            QMessageBox.information(self, "File Selected", f"File selected:\n{path}")

    def upload_traits(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Traits File", "", "Text Files (*.txt)")
        if path:
            self.traits_path = path
            filename = os.path.basename(path)
            self.upload_traits_btn.setText(f"{filename} Selected")
            QMessageBox.information(self, "File Selected", f"Trait description file selected:\n{path}")

    def start_extraction(self):
        if not self.species_path or not self.traits_path:
            QMessageBox.critical(self, "Error", "Please select both Species and Trait Description files.")
            return

        # parse input file (Excel or CSV)
        if self.species_path.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(self.species_path)
        elif self.species_path.lower().endswith('.csv'):
            df = pd.read_csv(self.species_path)
        else:
            QMessageBox.critical(self, "Error", "Unsupported file type. Please upload an Excel or CSV file.")
            return

        species_list = df.iloc[:, 0].dropna().astype(str).tolist()  # first col = species
        raw_traits_list = df.columns[1:].astype(str).tolist()  # rest = traits

        # parse trait description file
        parsed_descriptions = {}
        with open(self.traits_path, "r") as f: # utf 8
            for line in f:
                if ":" in line:
                    trait, desc = line.split(":", 1)
                    clean_trait = trait.strip().lower().lstrip("\ufeff") # remove BOM if exists
                    parsed_descriptions[clean_trait] = desc.strip()

        # normalize traits and map descriptions (case-insensitive)
        self.traits_list = []
        self.trait_descriptions = {}
        for t in raw_traits_list:
            self.traits_list.append(t)
            t_lower = t.strip().lower()
            self.trait_descriptions[t] = parsed_descriptions.get(t_lower, "")
        
        self.species_list = species_list
        self.output_file_name = "output_results.csv"

        self.run_sanity_check()

    def on_extraction_finished(self, file_name):
        self.show_success(file_name)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpeciesTraitsApp()
    window.show()
    sys.exit(app.exec_())
