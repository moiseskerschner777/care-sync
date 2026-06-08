from pydantic import BaseModel, ConfigDict


class PractitionerResponse(BaseModel):
    id: str
    name: str
    specialty: str
    council_type: str
    council_number: str
    council_state: str
    active: bool

    model_config = ConfigDict(from_attributes=True)
