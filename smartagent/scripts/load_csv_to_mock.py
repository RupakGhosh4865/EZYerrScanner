import pandas as pd
import requests
import json
import os

CSV_PATH = "all_agents_dataset.csv"
WIRE_MOCK_ADMIN = "http://localhost:8082/__admin"
SHEET_ID = 5556667778881234

def load_and_inject():
    global CSV_PATH
    if not os.path.exists(CSV_PATH):
        # Check current dir or scripts dir
        possible_paths = [CSV_PATH, os.path.join("scripts", CSV_PATH)]
        for p in possible_paths:
            if os.path.exists(p):
                CSV_PATH = p
                break
        else:
            print(f"Error: {CSV_PATH} not found.")
            return

    print(f"Loading {CSV_PATH}...")
    import csv
    with open(CSV_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        df_columns = reader.fieldnames
        rows_data = list(reader)
    
    columns = []
    for i, col_name in enumerate(df_columns):
        columns.append({
            "id": 100 + i,
            "title": col_name,
            "type": "TEXT_NUMBER",
            "primary": (i == 0)
        })

    rows = []
    for i, data in enumerate(rows_data):
        cells = []
        for j, col_name in enumerate(df_columns):
            val = data[col_name]
            if not val: val = None
            
            cells.append({
                "columnId": 100 + j,
                "value": val,
                "displayValue": str(val) if val is not None else ""
            })
        rows.append({
            "id": 1000 + i,
            "rowNumber": i + 1,
            "cells": cells
        })

    sheet_data = {
        "id": SHEET_ID,
        "name": "Global Multi-Agent Dataset (Stress Test)",
        "totalRowCount": len(rows),
        "columns": columns,
        "rows": rows
    }

    # API response format: GET /2.0/sheets/{id}
    mapping_get_sheet = {
        "request": {
            "method": "GET",
            "urlPattern": fr".*sheets/{SHEET_ID}.*"
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "jsonBody": sheet_data
        }
    }

    # API response format: GET /2.0/sheets
    mapping_list_sheets = {
        "request": {
            "method": "GET",
            "urlPattern": r".*2\.0/sheets$"
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "jsonBody": {
                "pageNumber": 1,
                "pageSize": 100,
                "totalPages": 1,
                "totalCount": 1,
                "data": [
                    {
                        "id": SHEET_ID, 
                        "name": "Q2 Project Tracker (Stress Test)", 
                        "accessLevel": "OWNER",
                        "modifiedAt": "2024-03-30T21:26:00Z",
                        "totalRowCount": len(rows)
                    }
                ]
            }
        }
    }

    try:
        # 0. FORCE RESET WireMock to clear persistent mappings and recorded requests.
        # This is more aggressive than DELETE and essential for a clean slate.
        print("Force resetting WireMock (clearing persistent storage)...")
        reset_res = requests.post(f"{WIRE_MOCK_ADMIN}/reset")
        if reset_res.status_code == 200:
            print("✅ WireMock force reset successful.")
        else:
            print(f"⚠️ Warning: WireMock reset failed (Status: {reset_res.status_code})")
        
        # Inject mappings
        r1 = requests.post(f"{WIRE_MOCK_ADMIN}/mappings", json=mapping_get_sheet)
        r2 = requests.post(f"{WIRE_MOCK_ADMIN}/mappings", json=mapping_list_sheets)
        
        print(f"Injected GET /sheets/{SHEET_ID}: {r1.status_code}")
        print(f"Injected GET /sheets: {r2.status_code}")
        
        if r1.status_code == 201 and r2.status_code == 201:
            print(f"Success! {len(rows)} rows loaded into WireMock.")
        else:
            print("Injection failed. Check if WireMock is running.")
            
    except Exception as e:
        print(f"Connection to WireMock failed: {e}")

if __name__ == "__main__":
    load_and_inject()
