@echo off
cd /d "%~dp0microwave_ndt_prototype"
if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate
pip install -r requirements.txt
if not exist models\defect_classifier.joblib (
  python train_model.py
)
streamlit run app.py
pause
