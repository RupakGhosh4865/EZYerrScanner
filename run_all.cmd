call env\Scripts\activate.bat
pip install -r backend\requirements.txt
python generator.py
python test_schema.py
