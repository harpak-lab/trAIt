import sys
import pandas as pd

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QMessageBox, QFileDialog
)
from PyQt5.QtCore import QThread, pyqtSignal
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
        self.excel_path = None
        self.traits_path = None

        # layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.show_input_form()

    def clear_layout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def show_input_form(self):
        self.clear_layout()

        self.layout.addWidget(QLabel("Upload Excel file (species + traits):"))
        self.upload_excel_btn = QPushButton("Choose Excel File")
        self.upload_excel_btn.clicked.connect(self.upload_excel)
        self.layout.addWidget(self.upload_excel_btn)

        self.layout.addWidget(QLabel("Upload Text file (trait descriptions):"))
        self.upload_traits_btn = QPushButton("Choose Trait Description File")
        self.upload_traits_btn.clicked.connect(self.upload_traits)
        self.layout.addWidget(self.upload_traits_btn)

        self.create_button = QPushButton("Start Data Extraction")
        self.create_button.clicked.connect(self.start_extraction)
        self.layout.addWidget(self.create_button)

    def show_loading(self):
        self.clear_layout()
        self.layout.addWidget(QLabel("Processing... Please wait."))

    def show_success(self, file_name):
        self.clear_layout()
        self.layout.addWidget(QLabel(f"Success! Excel file saved as {file_name}"))
        done_button = QPushButton("Done")
        done_button.clicked.connect(self.close)
        self.layout.addWidget(done_button)

    def upload_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx *.xls)")
        if path:
            self.excel_path = path
            QMessageBox.information(self, "File Selected", f"Excel file selected:\n{path}")

    def upload_traits(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Traits File", "", "Text Files (*.txt)")
        if path:
            self.traits_path = path
            QMessageBox.information(self, "File Selected", f"Trait description file selected:\n{path}")

    def start_extraction(self):
        if not self.excel_path or not self.traits_path:
            QMessageBox.critical(self, "Error", "Please select both Excel and Trait Description files.")
            return

        # parse excel file
        df = pd.read_excel(self.excel_path)
        species_list = df.iloc[:, 0].dropna().astype(str).tolist()  # first col = species
        traits_list = df.columns[1:].astype(str).tolist()  # rest = traits

        # parse trait description file
        trait_descriptions = {}
        # with open(self.traits_path, "r") as f:
        with open(self.traits_path, "r", encoding="utf-16") as f:
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
