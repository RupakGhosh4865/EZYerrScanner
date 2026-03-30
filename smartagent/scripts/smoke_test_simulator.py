import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from smartsheet_client.simulator import SmartsheetSimulator

def run_smoke_test():
    sim = SmartsheetSimulator()
    sheets = sim.list_sheets()
    df, meta, rows, col_map = sim.read_sheet('DEMO_SHEET_001')
    
    print('Sheets:', sheets)
    print('DataFrame shape:', df.shape)
    print('Columns:', list(df.columns))
    print('Column map:', col_map)
    print('First row IDs:', [r['__row_id__'] for r in rows[:3]])

if __name__ == "__main__":
    run_smoke_test()
