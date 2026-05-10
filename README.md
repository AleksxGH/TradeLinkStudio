# TradeLink Studio

  **TradeLink Studio** — a desktop application for computing and analyzing influence indices in directed weighted graphs. Supports data import from `.xlsx` and `.csv`, interactive matrix editing, and result export in `.xlsx` format.

  **Author:** Mishchenko Alexander, 2nd year student, HSE University, Faculty of Computer Science, Software Engineering Program.

  **Contact:** admishchenko@edu.hse.ru

  Application developed as a coursework project in the 2nd year of study, academic year 2025-2026.

  ## Feature Overview

  - Data import from XLSX and CSV (see "Input Data Format" section).
  - Index calculation: Copeland, Bundle, Pivotal, PI' (weighted Pivotal), and their normalized versions.
  - Result export to XLSX.
  - Undo/Redo, quota and vertex name editing, `subset_size (k)` configuration.

  ## Technology Stack

  | Component | Library / Technology | Purpose |
  |---|---:|---|
  | Language | Python 3.12 | Main application language |
  | GUI | PyQt5 | User interface |
  | Tabular data | pandas, openpyxl | XLSX read/write, table preparation |
  | Numbers and matrices | numpy | Fast numerical operations |
  | Graphs | networkx | Graph representation and iteration |
  | CSV parsing | Built-in csv, encodings | Reliable CSV reading with fallback |

  Dependencies are listed in `requirements.txt`.

  ## Index Calculation

**Copeland Index** — the sum of incoming edge weights for each vertex.

**Bundle Index** — the number of critical subsets of incoming neighbors of size from 1 to k. A subset is considered critical if the sum of its weights is greater than or equal to the vertex quota.

**Pivotal Index** — the number of occurrences of vertices as pivotal within critical subsets. A vertex is considered pivotal if its removal makes the subset non-critical. Each occurrence counts as 1.

**Weighted Pivotal Index** — uses the same critical subset system, but each occurrence of a pivotal vertex contributes a value equal to the subset size.

---

### Normalization

```
normalized_value = value / sum of all values of the same index
```

If the sum of all values equals 0, all normalized values equal 0.



  ## Input Data Format

  The application documentation (and `resources/ui/help.html`) describes the format in detail; below are precise requirements and examples.

  ### XLSX (Fixed Layout)

  Exact positions used by the loader (`pandas.read_excel(header=None)`):

  | Cell | Content | Type |
  |---|---|---:|
  | B1 (row 0, column 1) | Number of vertices (optional) $N$ | Integer |
  | D2 (1,3) | `subset_size` ($k$) | Integer |
  | F2 onwards (1,5...) | Quotas, N values | N float |
  | B3 onwards (2,1...) | Horizontal vertex names | N strings |
  | A4 onwards (3+,0) | Vertical vertex names | N strings |
  | B4.. (3..3+N, 1..1+N) | Adjacency matrix | N×N numbers |

  Numbers can have decimal comma or period; diagonal elements are typically 0.

  **Example (N=3, k=2):**

  
| N= | 3 |   |   |   |   |   |   |
|----|---|---|---|---|---|---|---|
|    |   | k= | 2 | Quota values: | 2,0 | 3,5 | 2,8 |
|    | v1 | v2 | v3 |   |   |   |   |
| v1 | 0 | 2,0 | 1,0 |   |   |   |   |
| v2 | 1,0 | 0 | 3,0 |   |   |   |   |
| v3 | 4,0 | 2,0 | 0 |   |   |   |   |
  

  ### CSV

  CSV format expects the first row with horizontal vertex names and a `quota` label in the last column. Each subsequent row is a matrix row with quota at the end.

  Example CSV (exactly as in Help page):

  ```
  v1;v2;v3;quota
  0;2,5;1,2;4,0
  1,0;0;3,1;3,5
  4,2;2,0;0;2,8
  ```

  Rules:

  - Header: vertex names, last column is `quota`.
  - Rows: either `name;w1;...;wN;quota` or `w1;...;wN;quota` (without leading name) — the loader supports both variants.
  - Empty matrix cells are treated as 0.
  - **Delimiter** recommendation: use `;`
  - Encodings: `utf-8`, `latin-1`, `utf-16` (fallback).


## Result Export (XLSX)

The exporter generates a table compatible with `.xlsx` file reading logic:

- writes basic metadata (N, subset size, quotas);
- writes vertices and matrix;
- adds index columns to the right of the matrix;
- in case of save issues, attempts an alternative name with timestamp.

## UI and UX

###  HomeWindow

- Welcome screen.
- Project list (standard + custom).
- Project search.
- Project creation/opening/deletion/copying/renaming.
- Built-in Settings and Help pages.

### MainWindow

- Toolbar: Home, Load Data, Undo, Redo, Calculate, Export, Save.
- Parameter controls: subset size, precision.
- Tables: Quotas, Input Matrix, Calculated Indices.
- Visibility control buttons: PI' weighted, Normalized data.
- Dirty-state support and button locking depending on state.

## Logging and Error Handling

- Logging initialization in main.py on startup.
- Unhandled exception catching through sys.excepthook.
- DEBUG/ERROR level logging to app_actions.log.
- QMessageBox display on critical UI/application cycle errors.
- Log cleanup and active-flag clearing on normal exit.

## Installation and Running

### Requirements

- Python 3.12 (recommended, project uses 3.12.6)
- Windows 10/11

Dependencies from requirements.txt:
- PyQt5==5.15.9
- pandas==2.1.1
- numpy==1.26.1
- openpyxl==3.1.3

### Installation

1. Create and activate a virtual environment.
2. Install dependencies:

   pip install -r requirements.txt

3. Run the application:

   python main.py

## EXE Build (PyInstaller)

Use the script:

- build_exe.bat

What the script does:
- activates venv (if found);
- cleans build/dist;
- runs generate_build_metadata.py;
- generates exe name from version;
- calls pyinstaller --onefile --windowed with necessary add-data.

Additionally:
- generate_build_metadata.py generates build/version_file.txt in compatible format for current PyInstaller.

## Quick Code Navigation

- Entry point: main.py
- Main window: app/ui/main_window.py
- Home window: app/ui/home_window.py
- Algorithms: app/core/indices_calculator.py
- State history: app/core/datastore.py
- Project saving: app/services/project_manager.py
- Import/export: app/data/loader.py, app/data/exporter.py
- EXE build: build_exe.bat, generate_build_metadata.py