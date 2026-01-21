from fastapi import FastAPI, Request, Form, Depends, HTTPException, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from pydantic import BaseModel
import json
import os
from openai import OpenAI

from app.database import engine, get_db, Base
from app.models import User, Equipment, Calculation
from app.auth import verify_password, get_current_user, create_session, delete_session

# Créer les tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configuration du client AI (DeepInfra via format OpenAI)
# REMPLACEZ PAR VOTRE CLÉ API RÉELLE
DEEPINFRA_API_KEY = ""

client = OpenAI(
    api_key=DEEPINFRA_API_KEY,
    base_url="https://api.deepinfra.com/v1/openai",
)

# Monter les fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# --- MODÈLES PYDANTIC ---
class AnalysisRequest(BaseModel):
    calculation_ids: List[int]

# --- CONSTANTES ---
LVMH_HOUSES = [
    "Louis Vuitton", "Dior", "Fendi", "Givenchy", "Celine", 
    "Moët Hennessy", "Hennessy", "TAG Heuer", "Bulgari", "Sephora"
]

EQUIPMENT_TYPES = {
    "iPhone 15 Pro": {"price": 1200, "eco_score": 65, "lifespan": 3},
    "iPhone 14": {"price": 900, "eco_score": 70, "lifespan": 3},
    "MacBook Pro M3": {"price": 2500, "eco_score": 75, "lifespan": 5},
    "MacBook Air M2": {"price": 1500, "eco_score": 80, "lifespan": 5},
    "Dell XPS 15": {"price": 2000, "eco_score": 70, "lifespan": 4},
    "Dell Latitude": {"price": 1200, "eco_score": 72, "lifespan": 4},
    "iPad Pro": {"price": 1100, "eco_score": 68, "lifespan": 4},
    "Samsung Galaxy Tab": {"price": 600, "eco_score": 65, "lifespan": 3},
    "HP EliteBook": {"price": 1400, "eco_score": 71, "lifespan": 4},
    "Lenovo ThinkPad": {"price": 1300, "eco_score": 73, "lifespan": 4}
}

# --- ROUTES AUTH ---
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = verify_password(db, username, password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Identifiants invalides"})
    session_id = create_session(user.id)
    response = RedirectResponse(url="/home", status_code=303)
    response.set_cookie(key="session_id", value=session_id)
    return response

@app.get("/logout")
async def logout(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id: delete_session(session_id)
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session_id")
    return response

# --- ROUTES APP ---
@app.get("/home", response_class=HTMLResponse)
async def home(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("home.html", {"request": request, "user": user, "houses": LVMH_HOUSES})

@app.post("/select-house")
async def select_house(request: Request, house: str = Form(...), user: User = Depends(get_current_user)):
    response = RedirectResponse(url="/data-input", status_code=303)
    response.set_cookie(key="selected_house", value=house)
    return response

@app.get("/data-input", response_class=HTMLResponse)
async def data_input(request: Request, user: User = Depends(get_current_user)):
    selected_house = request.cookies.get("selected_house", "Non sélectionnée")
    return templates.TemplateResponse("data_input.html", {
        "request": request, "user": user, "selected_house": selected_house, "equipment_types": list(EQUIPMENT_TYPES.keys())
    })

@app.post("/save-equipments")
async def save_equipments(request: Request, user: User = Depends(get_current_user)):
    form_data = await request.form()
    equipments = []
    equipment_types = form_data.getlist("equipment_type[]")
    quantities = form_data.getlist("quantity[]")
    
    for eq_type, qty in zip(equipment_types, quantities):
        if eq_type and qty:
            equipments.append({
                "type": eq_type,
                "quantity": int(qty),
                "price": EQUIPMENT_TYPES[eq_type]["price"],
                "eco_score": EQUIPMENT_TYPES[eq_type]["eco_score"],
                "lifespan": EQUIPMENT_TYPES[eq_type]["lifespan"]
            })
    
    response = RedirectResponse(url="/calculator", status_code=303)
    response.set_cookie(key="equipments", value=json.dumps(equipments))
    return response

@app.get("/calculator", response_class=HTMLResponse)
async def calculator(request: Request, user: User = Depends(get_current_user)):
    selected_house = request.cookies.get("selected_house", "Non sélectionnée")
    equipments = json.loads(request.cookies.get("equipments", "[]"))
    return templates.TemplateResponse("calculator.html", {
        "request": request, "user": user, "selected_house": selected_house, "equipments": equipments
    })

@app.post("/calculate-roi")
async def calculate_roi(
    request: Request, 
    eco_weight: float = Form(...), 
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    equipments = json.loads(request.cookies.get("equipments", "[]"))
    selected_house = request.cookies.get("selected_house")
    
    financial_weight = 100 - eco_weight
    total_cost = sum(eq["price"] * eq["quantity"] for eq in equipments)
    total_qty = sum(eq["quantity"] for eq in equipments) if equipments else 1
    
    avg_eco_score = sum(eq["eco_score"] * eq["quantity"] for eq in equipments) / total_qty if equipments else 0
    avg_lifespan = sum(eq["lifespan"] * eq["quantity"] for eq in equipments) / total_qty if equipments else 1
    
    # Formule simplifiée pour score financier (100 - impact coût/durée)
    financial_score = max(0, 100 - (total_cost / (avg_lifespan * 1000)))
    ecological_score = avg_eco_score
    global_score = (financial_score * financial_weight / 100) + (ecological_score * eco_weight / 100)
    
    calculation = Calculation(
        user_id=user.id,
        house=selected_house,
        equipments=json.dumps(equipments),
        eco_weight=eco_weight,
        financial_weight=financial_weight,
        financial_score=financial_score,
        ecological_score=ecological_score,
        global_score=global_score
    )
    db.add(calculation)
    db.commit()
    
    return RedirectResponse(url=f"/results/{calculation.id}", status_code=303)

@app.get("/results/{calculation_id}", response_class=HTMLResponse)
async def results(request: Request, calculation_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    calculation = db.query(Calculation).filter(Calculation.id == calculation_id, Calculation.user_id == user.id).first()
    if not calculation: raise HTTPException(status_code=404, detail="Calcul non trouvé")
    return templates.TemplateResponse("results.html", {
        "request": request, "user": user, "calculation": calculation, "equipments": json.loads(calculation.equipments)
    })

@app.get("/recommendations/{calculation_id}", response_class=HTMLResponse)
async def recommendations(request: Request, calculation_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    calculation = db.query(Calculation).filter(Calculation.id == calculation_id, Calculation.user_id == user.id).first()
    if not calculation: raise HTTPException(status_code=404, detail="Calcul non trouvé")
    
    # Simulation des recommandations (simplifié pour l'exemple)
    rec_list = []
    if calculation.ecological_score < 75:
        rec_list.append({"icon": "leaf", "title": "Potentiel Écologique", "description": "Optez pour des modèles 'Green IT' certifiés."})
    else:
        rec_list.append({"icon": "trophy", "title": "Excellence Durable", "description": "Vos choix sont alignés avec la stratégie LIFE 360 de LVMH."})

    return templates.TemplateResponse("recommendations.html", {
        "request": request, "user": user, "calculation": calculation, "recommendations": rec_list
    })

@app.get("/history", response_class=HTMLResponse)
async def history(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    calculations = db.query(Calculation).filter(Calculation.user_id == user.id).order_by(desc(Calculation.created_at)).all()
    for calc in calculations:
        calc.equipments_list = json.loads(calc.equipments)
    return templates.TemplateResponse("history.html", {
        "request": request, "user": user, "calculations": calculations
    })

# --- ROUTES COMPARATIVES ---

# 1. Route d'affichage (Rapide, sans IA)
@app.post("/compare", response_class=HTMLResponse)
async def compare_calculations(
    request: Request, 
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    form_data = await request.form()
    calc_ids = form_data.getlist("calculation_ids")
    
    # Conversion en int pour traitement
    try:
        calc_ids_int = [int(i) for i in calc_ids]
    except ValueError:
        return RedirectResponse(url="/history", status_code=303)

    if not calc_ids or len(calc_ids) < 2:
        return RedirectResponse(url="/history", status_code=303)
        
    calculations = db.query(Calculation).filter(
        Calculation.id.in_(calc_ids),
        Calculation.user_id == user.id
    ).all()

    # On passe les IDs à la vue pour que le JS puisse appeler l'API ensuite
    return templates.TemplateResponse("comparison.html", {
        "request": request, 
        "user": user, 
        "calculations": calculations,
        "calculation_ids_json": json.dumps(calc_ids_int) # IDs sérialisés pour JS
    })

# 2. API Endpoint pour l'IA (Asynchrone via JS)
@app.post("/api/analyze-comparison")
async def api_analyze_comparison(
    req: AnalysisRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    calculations = db.query(Calculation).filter(
        Calculation.id.in_(req.calculation_ids),
        Calculation.user_id == user.id
    ).all()

    if not calculations:
        return JSONResponse({"content": "Données insuffisantes pour l'analyse."}, status_code=400)

    # Préparation des données pour l'IA
    scenarios_text = ""
    for calc in calculations:
        equipments = json.loads(calc.equipments)
        eq_list = ", ".join([f"{e['quantity']}x {e['type']}" for e in equipments])
        scenarios_text += (
            f"- Scenario ID {calc.id} ({calc.house}): "
            f"Score Global: {calc.global_score:.1f}, "
            f"Score Eco: {calc.ecological_score:.1f}, "
            f"Score Financier: {calc.financial_score:.1f}. "
            f"Équipements: {eq_list}.\n"
        )

    # Appel LLM (DeepInfra)
    try:
        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3-70B-Instruct",
            messages=[
                {"role": "system", "content": "Tu es un stratège senior chez LVMH, expert en achats IT durables. Tu analyses des scénarios d'investissement. Ton ton est professionnel, concis et luxueux. Utilise le Markdown pour formater ta réponse (titres, listes, gras). Analyse les compromis (trade-offs) entre l'impact financier et écologique. Recommande le meilleur scénario pour une stratégie long-terme."},
                {"role": "user", "content": f"Compare ces scénarios d'achat :\n{scenarios_text}\nFais une synthèse courte des trade-offs et donne une recommandation claire en Markdown."}
            ],
            max_tokens=600
        )
        ai_content = response.choices[0].message.content
        return JSONResponse({"content": ai_content})
    
    except Exception as e:
        print(f"Erreur API: {e}")
        return JSONResponse(
            {"content": "**Erreur de service:** L'IA est momentanément indisponible. Veuillez réessayer plus tard."}, 
            status_code=500
        )

@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    if not db.query(User).filter(User.username == "demo").first():
        db.add(User(username="demo", password="demo123"))
        db.commit()