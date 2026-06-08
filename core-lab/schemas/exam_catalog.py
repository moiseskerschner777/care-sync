from pydantic import BaseModel, ConfigDict


class ExamCatalogResponse(BaseModel):
    id: str
    exam_code: str
    exam_name: str
    category: str
    can_perform: bool
    requires_support_lab: bool
    support_lab: str | None
    turnaround_hours: int

    model_config = ConfigDict(from_attributes=True)
