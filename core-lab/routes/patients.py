from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.patient import Patient
from schemas.patient import PatientResponse

router = APIRouter()


@router.get("/{id}", response_model=PatientResponse)
def get_patient(id: str, db: Session = Depends(get_db)):
    patient = db.get(Patient, id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    return patient
