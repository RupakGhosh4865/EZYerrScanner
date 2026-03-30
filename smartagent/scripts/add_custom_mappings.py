import requests, json

ADMIN = "http://localhost:8082/__admin"

def add_mapping(test_name, method, url_pattern, response_body, status=200):
    mapping = {
        "request": {
            "method": method,
            "urlPattern": url_pattern,
            # Removed header requirement for stability in Phase 2
        },
        "response": {
            "status": status,
            "headers": {"Content-Type": "application/json"},
            "jsonBody": response_body
        }
    }
    r = requests.post(f"{ADMIN}/mappings", json=mapping)
    print(f"Added mapping '{test_name}' [{method} {url_pattern}]: {r.status_code}")

if __name__ == "__main__":
    # Ensure list-sheets is there (redundant but safe)
    add_mapping(
        test_name="list-sheets",
        method="GET",
        url_pattern="/sheets\\/?",
        response_body={
            "data": [
                {"id": 4583173393803140, "name": "Q2 Project Tracker", "totalRowCount": 45}
            ]
        }
    )

    # Ensure get-sheet works without the Assume-User header requirement
    add_mapping(
        test_name="get-sheet",
        method="GET",
        url_pattern="/sheets/4583173393803140\\/?",
        response_body={
            "id": 4583173393803140,
            "name": "Q2 Project Tracker",
            "totalRowCount": 2,
            "columns": [
                {"id": 101, "title": "Task Name", "type": "TEXT_NUMBER", "primary": True},
                {"id": 102, "title": "Status", "type": "PICKLIST"}
            ],
            "rows": [
                {
                    "id": 201, "rowNumber": 1,
                    "cells": [
                        {"columnId": 101, "value": "Fix broken formulas", "displayValue": "Fix broken formulas"},
                        {"columnId": 102, "value": "In Progress", "displayValue": "In Progress"}
                    ]
                }
            ]
        }
    )

    add_mapping(
        test_name="add-comment",
        method="POST",
        url_pattern="/sheets/.*/rows/.*/discussions",
        response_body={"message": "SUCCESS", "result": {"id": 999, "comment": {"text": "Added"}}}
    )

    add_mapping(
        test_name="update-rows",
        method="PUT",
        url_pattern="/sheets/.*/rows",
        response_body={"message": "SUCCESS", "result": [{"id": 201}]}
    )

    add_mapping(
        test_name="create-sheet",
        method="POST",
        url_pattern="/sheets\\/?",
        response_body={
            "result": {"id": 888, "name": "Audit Report", "permalink": "https://app.smartsheet.com/b/home"}
        }
    )

    add_mapping(
        test_name="add-rows",
        method="POST",
        url_pattern="/sheets/.*/rows",
        response_body={"message": "SUCCESS", "result": [{"id": 301}]}
    )

    print("\nCustom mappings injected into WireMock.")
