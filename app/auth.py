from fastapi import Request, HTTPException
from sqlalchemy.orm import Session
import secrets

from app.models import User

# Stockage simple des sessions en mémoire (pour POC)
sessions = {}


def verify_password(db: Session, username: str, password: str) -> User:
    """Vérifie les identifiants de l'utilisateur"""
    user = db.query(User).filter(User.username == username).first()
    if user and user.password == password:  # En production: utiliser bcrypt
        return user
    return None


def create_session(user_id: int) -> str:
    """Crée une session pour l'utilisateur"""
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = user_id
    return session_id


def delete_session(session_id: str):
    """Supprime une session"""
    if session_id in sessions:
        del sessions[session_id]


def get_current_user(request: Request) -> User:
    """Récupère l'utilisateur actuel depuis la session"""
    from app.database import SessionLocal
    
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Non authentifié")
    
    user_id = sessions[session_id]
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
    
    return user
