from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class PatientResponse(BaseModel):
    id: str
    name_family: str
    name_given: str
    birth_date: date
    gender: str
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
