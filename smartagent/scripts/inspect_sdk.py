import smartsheet
import os

client = smartsheet.Smartsheet(access_token="dummy")
print("Smartsheet attributes:", [a for a in dir(client) if not a.startswith("_")])
print("\nSheets attributes:", [a for a in dir(client.Sheets) if not a.startswith("_")])
print("\nDiscussions attributes:", [a for a in dir(client.Discussions) if not a.startswith("_")])
