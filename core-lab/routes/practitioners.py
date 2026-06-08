from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.practitioner import Practitioner
from schemas.practitioner import PractitionerResponse

router = APIRouter()


@router.get("/{id}", response_model=PractitionerResponse)
def get_practitioner(id: str, db: Session = Depends(get_db)):
    print("supermario practitioner with ID:", id)
    practitioner = db.get(Practitioner, id)
    if practitioner is None:
        raise HTTPException(status_code=404, detail="Practitioner not foundxxx")

    return practitioner
