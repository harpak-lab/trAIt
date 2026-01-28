import sys
import os
import pandas as pd

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QMessageBox, QFileDialog,
    QTabWidget,
    QSpacerItem, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from pubmed_query import process_species_traits, sanity_check


# Worker thread for Sanity Check
class SanityCheckWorker(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, species_list, traits_list):
        super().__init__()
        self.species_list = species_list
        self.traits_list = traits_list

    def run(self):
        results = sanity_check(self.species_list, self.traits_list)
        self.finished.emit(results)


# Worker thread
class ExtractionWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, species_list, traits_list, trait_descriptions, file_name):
        super().__init__()
        self.species_list = species_list
        self.traits_list = traits_list
        self.trait_descriptions = trait_descriptions
        self.file_name = file_name

    def run(self):
        process_species_traits(
            self.species_list, self.traits_list,
            self.file_name, self.trait_descriptions
        )
        self.finished.emit(self.file_name)


class SpeciesTraitsApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Species & Traits Analysis")
        self.setGeometry(200, 200, 600, 500)

        # file paths
        self.species_path = None
        self.traits_path = None
        
        # stored data for pipeline
        self.species_list = []
        self.traits_list = []
        self.trait_descriptions = {}
        self.output_file_name = "output_results.csv"

        # layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # tab widget
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # create tabs
        self.instructions_tab = QWidget()
        self.examples_tab = QWidget()
        self.upload_tab = QWidget()

        self.tabs.addTab(self.instructions_tab, "Instructions")
        self.tabs.addTab(self.examples_tab, "Examples")
        self.tabs.addTab(self.upload_tab, "Upload")

        # populate tabs
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
            # Construct absolute path relative to this script file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            image_path = os.path.join(script_dir, "..", "sample_data", f"{filename}.png")
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaledToWidth(350, Qt.SmoothTransformation)
                image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignHCenter)
            layout.addWidget(image_label)

        # Add all examples
        add_example("Example CSV Format", "example_species_csv")
        add_example("Example Excel Format", "example_species_excel")
        add_example("Example Trait Description File", "example_trait_desc")

        self.examples_tab.setLayout(layout)

    def show_sanity_loading(self):
        self.clear_layout()
        loading_label = QLabel("Running Trait Assessment...\n\nChecking literature availability for your traits.")
        loading_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(loading_label)

    def show_sanity_results(self, trait_stats):
        self.clear_layout()
        
        container = QWidget()
        layout = QVBoxLayout(container)

        # Header
        header = QLabel("<h2>Trait Assessment Results</h2>")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Explanation
        explanation = QLabel(
            "The <b>mean</b> indicates typical literature availability.<br>"
            "The <b>standard deviation</b> (std dev) indicates variability across species."
        )
        explanation.setAlignment(Qt.AlignCenter)
        layout.addWidget(explanation)

        # Force window resize to fit content - removed fixed height, use min width
        self.setMinimumWidth(600)

        # Stats Area (Scrollable)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        for trait, stats in trait_stats.items():
            mean_val = stats['mean']
            std_dev_val = stats['std_dev']

            trait_label = QLabel(
                f"<b>{trait}</b>: Mean = {mean_val:.1f}, Std Dev = {std_dev_val:.1f}"
            )
            scroll_layout.addWidget(trait_label)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        
        # Adjust height based on content (approx 35px per item + padding)
        # Cap at 400px, min 100px
        content_height = len(trait_stats) * 35 + 40
        scroll_area.setFixedHeight(min(max(content_height, 100), 400))
        
        layout.addWidget(scroll_area)

        # Buttons
        btn_layout = QVBoxLayout()
        
        proceed_label = QLabel("You can use this information to revise your files or proceed as is.")
        proceed_label.setAlignment(Qt.AlignCenter)
        btn_layout.addWidget(proceed_label)

        proceed_btn = QPushButton("Proceed with Extraction")
        proceed_btn.clicked.connect(self.run_extraction_pipeline)
        btn_layout.addWidget(proceed_btn)

        quit_btn = QPushButton("Quit")
        quit_btn.clicked.connect(self.close)
        btn_layout.addWidget(quit_btn)

        layout.addLayout(btn_layout)
        self.layout.addWidget(container)
        
        # Resize window to fit content
        self.adjustSize()
    
    def run_sanity_check(self):
        self.show_sanity_loading()
        self.sanity_worker = SanityCheckWorker(self.species_list, self.traits_list)
        self.sanity_worker.finished.connect(self.on_sanity_check_finished)
        self.sanity_worker.start()

    def on_sanity_check_finished(self, results):
        self.show_sanity_results(results)

    def run_extraction_pipeline(self):
        # switch to loading
        self.show_loading()

        # start worker
        self.worker = ExtractionWorker(
            self.species_list, self.traits_list, 
            self.trait_descriptions, self.output_file_name
        )
        self.worker.finished.connect(self.on_extraction_finished)
        self.worker.start()

    def show_loading(self):
        self.clear_layout()
        self.layout.addWidget(QLabel("Processing... Please wait."))

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
            QMessageBox.information(self, "File Selected", f"File selected:\n{path}")

    def upload_traits(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Traits File", "", "Text Files (*.txt)")
        if path:
            self.traits_path = path
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

        # Start Sanity Check
        self.run_sanity_check()

    def on_extraction_finished(self, file_name):
        self.show_success(file_name)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpeciesTraitsApp()
    window.show()
    sys.exit(app.exec_())
