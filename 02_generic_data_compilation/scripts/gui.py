import sys
import pandas as pd

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QMessageBox, QFileDialog,
    QTabWidget,
    QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from pubmed_query import process_species_traits


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
        self.setGeometry(200, 200, 500, 200)

        # file paths
        self.species_path = None
        self.traits_path = None

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
        <p>The processed Excel file will be saved as <b>output_results.xlsx</b> in your working directory.</p>
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
            pixmap = QPixmap(f"../sample_data/{filename}.png")
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
        traits_list = df.columns[1:].astype(str).tolist()  # rest = traits

        # parse trait description file
        trait_descriptions = {}
        with open(self.traits_path, "r") as f: # utf 8
            for line in f:
                if ":" in line:
                    trait, desc = line.split(":", 1)
                    clean_trait = trait.strip().lower().lstrip("\ufeff") # remove BOM if exists
                    trait_descriptions[clean_trait] = desc.strip()

        # normalize traits and map descriptions (case-insensitive)
        normalized_traits = []
        mapped_descriptions = {}
        for t in traits_list:
            t_lower = t.strip().lower()
            normalized_traits.append(t)
            mapped_descriptions[t] = trait_descriptions.get(t_lower, "")

        file_name = "output_results.xlsx"

        # switch to loading
        self.show_loading()

        # start worker
        self.worker = ExtractionWorker(species_list, normalized_traits, mapped_descriptions, file_name)
        self.worker.finished.connect(self.on_extraction_finished)
        self.worker.start()

    def on_extraction_finished(self, file_name):
        self.show_success(file_name)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpeciesTraitsApp()
    window.show()
    sys.exit(app.exec_())
