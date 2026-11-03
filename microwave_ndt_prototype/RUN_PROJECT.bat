@echo off
cd /d "%~dp0"
if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate
pip install -r requirements.txt
if not exist models\defect_classifier.joblib (
  echo Training AI models...
  python train_model.py
)
streamlit run app.py
pause
