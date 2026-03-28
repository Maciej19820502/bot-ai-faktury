"""Generate test Excel file with invoice data."""

import os
import random
from datetime import datetime, timedelta

import openpyxl

EXCEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "invoices.xlsx")

SUPPLIERS = {
    "automotiveparts.pl": "AutoParts Sp. z o.o.",
    "dostawca-czesci.com": "Dostawca Części S.A.",
    "motortech.de": "MotorTech GmbH",
    "supplierxyz.pl": "Supplier XYZ Sp. z o.o.",
    "logistyka-pro.pl": "Logistyka PRO S.A.",
}

SUPPLIER_NAMES = list(SUPPLIERS.values())


def generate_test_data(filepath: str = EXCEL_PATH, num_records: int = 60):
    """Generate a realistic Excel file with invoice test data."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Faktury"

    # Headers matching project specification
    headers = [
        "Numer faktury",
        "Dostawca",
        "Kwota",
        "Waluta",
        "Data wystawienia",
        "Termin płatności",
        "Status",
        "Data płatności",
    ]
    ws.append(headers)

    # Style headers
    for cell in ws[1]:
        cell.font = openpyxl.styles.Font(bold=True)

    random.seed(42)  # Reproducible test data
    base_date = datetime(2025, 7, 1)

    for i in range(1, num_records + 1):
        supplier = random.choice(SUPPLIER_NAMES)

        # Invoice number — mostly standard format, some variants
        year = random.choice([2025, 2026])
        if random.random() < 0.8:
            inv_num = f"FV/{year}/{i:03d}"
        elif random.random() < 0.5:
            inv_num = f"FV-{year}-{i:03d}"
        else:
            inv_num = f"FA/{year}/{i:03d}"

        amount = round(random.uniform(500, 250000), 2)
        currency = "PLN" if random.random() < 0.75 else "EUR"

        issue_date = base_date + timedelta(days=random.randint(0, 250))
        due_date = issue_date + timedelta(days=random.choice([14, 30, 45, 60]))

        # Status distribution
        roll = random.random()
        if roll < 0.40:
            status = "Opłacona"
            payment_date = due_date - timedelta(days=random.randint(0, 10))
            payment_date_str = payment_date.strftime("%Y-%m-%d")
        elif roll < 0.75:
            status = "Oczekująca"
            payment_date_str = ""
        else:
            status = "Przeterminowana"
            payment_date_str = ""

        ws.append([
            inv_num,
            supplier,
            amount,
            currency,
            issue_date.strftime("%Y-%m-%d"),
            due_date.strftime("%Y-%m-%d"),
            status,
            payment_date_str,
        ])

    # Auto-fit column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 3, 30)

    wb.save(filepath)
    print(f"[TEST DATA] Wygenerowano {num_records} faktur -> {filepath}")


def ensure_test_data(filepath: str = EXCEL_PATH):
    """Create test data file if it does not exist."""
    if not os.path.exists(filepath):
        generate_test_data(filepath)
    else:
        print(f"[TEST DATA] Plik już istnieje: {filepath}")


if __name__ == "__main__":
    generate_test_data()
