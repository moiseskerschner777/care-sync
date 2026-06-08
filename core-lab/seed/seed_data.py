import argparse
from datetime import date, datetime
from pathlib import Path
import sys

from sqlalchemy import inspect

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import SessionLocal
from models.exam_catalog import ExamCatalog
from models.patient import Patient
from models.practitioner import Practitioner
from models.service_request import ServiceRequest
from models.service_request_item import ServiceRequestItem


PATIENTS = [
    {
        "id": "11c5be47-3215-4890-a79f-9c2b2293a85e",
        "name_family": "Silva",
        "name_given": "Ana Paula",
        "birth_date": date(1988, 4, 12),
        "gender": "FEMALE",
        "active": True,
    },
    {
        "id": "e36e8749-a762-45ea-bd6b-63a5745d6e07",
        "name_family": "Oliveira",
        "name_given": "Carlos Eduardo",
        "birth_date": date(1979, 9, 3),
        "gender": "MALE",
        "active": True,
    },
    {
        "id": "664d2678-29ce-450e-ab50-bd463364ded6",
        "name_family": "Souza",
        "name_given": "Mariana",
        "birth_date": date(1995, 1, 27),
        "gender": "FEMALE",
        "active": True,
    },
    {
        "id": "57b22f32-fb64-4328-8aea-331c799e8c5b",
        "name_family": "Pereira",
        "name_given": "Joao Pedro",
        "birth_date": date(2001, 7, 18),
        "gender": "MALE",
        "active": True,
    },
    {
        "id": "cbf0c4f8-6414-4e62-a9d6-8f5fae25e87f",
        "name_family": "Costa",
        "name_given": "Fernanda",
        "birth_date": date(1983, 11, 22),
        "gender": "FEMALE",
        "active": True,
    },
    {
        "id": "62ad9f49-a889-4ca1-9ca0-bb0c3a2f5404",
        "name_family": "Rodrigues",
        "name_given": "Lucas",
        "birth_date": date(1992, 5, 8),
        "gender": "MALE",
        "active": True,
    },
    {
        "id": "21307f05-3ef0-4609-ad95-6ba417d6f5a0",
        "name_family": "Almeida",
        "name_given": "Beatriz",
        "birth_date": date(1974, 2, 14),
        "gender": "FEMALE",
        "active": True,
    },
    {
        "id": "10224d6f-5793-4118-872f-742af3d361ee",
        "name_family": "Lima",
        "name_given": "Rafael",
        "birth_date": date(1986, 12, 30),
        "gender": "MALE",
        "active": True,
    },
    {
        "id": "99ca7393-59ce-4db3-a795-a7c5b784698d",
        "name_family": "Gomes",
        "name_given": "Patricia",
        "birth_date": date(1998, 6, 5),
        "gender": "FEMALE",
        "active": True,
    },
    {
        "id": "17ae4441-d7dd-4f7c-bc55-7ca85bf4f677",
        "name_family": "Martins",
        "name_given": "Thiago",
        "birth_date": date(1969, 10, 9),
        "gender": "MALE",
        "active": True,
    },
]

PRACTITIONERS = [
    {
        "id": "0f7f838f-5bbd-43b7-951c-02582e4272a3",
        "name": "Dra. Helena Martins",
        "specialty": "Cardiologia",
        "council_type": "CRM",
        "council_number": "12345",
        "council_state": "SC",
        "active": True,
    },
    {
        "id": "8853e3c3-d0f9-469f-ae48-7813dc83b8ec",
        "name": "Dr. Ricardo Menezes",
        "specialty": "Clínica Geral",
        "council_type": "CRM",
        "council_number": "23456",
        "council_state": "SC",
        "active": True,
    },
    {
        "id": "35ca797f-5099-479d-91d5-fbe12a125b90",
        "name": "Dra. Camila Azevedo",
        "specialty": "Endocrinologia",
        "council_type": "CRM",
        "council_number": "34567",
        "council_state": "SC",
        "active": True,
    },
]

EXAMS = [
    {
        "id": "d00f6eeb-7c0e-4cdf-a44f-78dd65d16ed5",
        "exam_code": "HEM001",
        "exam_name": "Hemograma",
        "category": "hematology",
        "can_perform": True,
        "requires_support_lab": False,
        "support_lab": None,
        "turnaround_hours": 4,
    },
    {
        "id": "9b5dba88-9494-4853-bcec-c2d5cdf4e346",
        "exam_code": "GLI001",
        "exam_name": "Glicemia",
        "category": "biochemistry",
        "can_perform": True,
        "requires_support_lab": False,
        "support_lab": None,
        "turnaround_hours": 2,
    },
    {
        "id": "bc0495ea-fbec-4030-a79d-6c8b1f462dd2",
        "exam_code": "COL001",
        "exam_name": "Colesterol Total",
        "category": "biochemistry",
        "can_perform": True,
        "requires_support_lab": False,
        "support_lab": None,
        "turnaround_hours": 6,
    },
    {
        "id": "ba0a6086-f4f3-4d00-a84f-a4069b72a721",
        "exam_code": "URI001",
        "exam_name": "Urina Tipo I",
        "category": "urinalysis",
        "can_perform": True,
        "requires_support_lab": False,
        "support_lab": None,
        "turnaround_hours": 8,
    },
    {
        "id": "18aa003f-91dc-49bf-a664-f0cdcc19c347",
        "exam_code": "TSH001",
        "exam_name": "TSH",
        "category": "hormones",
        "can_perform": True,
        "requires_support_lab": False,
        "support_lab": None,
        "turnaround_hours": 12,
    },
    {
        "id": "ea48cf24-2137-4b86-b386-6eb807d1dd83",
        "exam_code": "ONC001",
        "exam_name": "Marcadores Tumorais",
        "category": "oncology",
        "can_perform": False,
        "requires_support_lab": True,
        "support_lab": "REFLAB",
        "turnaround_hours": 72,
    },
    {
        "id": "7c7214ba-bf17-48dc-ac33-53ef157a6c68",
        "exam_code": "GEN001",
        "exam_name": "Teste Genético",
        "category": "genetics",
        "can_perform": False,
        "requires_support_lab": True,
        "support_lab": "REFLAB",
        "turnaround_hours": 120,
    },
    {
        "id": "5c1bd310-b8dc-4d74-85cc-c1fa4518104f",
        "exam_code": "CUL001",
        "exam_name": "Cultura e Antibiograma",
        "category": "microbiology",
        "can_perform": False,
        "requires_support_lab": True,
        "support_lab": "REFLAB",
        "turnaround_hours": 96,
    },
    {
        "id": "b9e7d142-3a65-4f81-bc29-8d4ef6a7c910",
        "exam_code": "ERR-LOINC",
        "exam_name": "Teste LOINC desconhecido (simulador de erro)",
        "category": "external",
        "can_perform": False,
        "requires_support_lab": True,
        "support_lab": "REFLAB",
        "turnaround_hours": 168,
    },
]

SERVICE_REQUESTS = [
    {
        "id": "51f63f5b-3db9-40c9-9344-b86cb7dc30fd",
        "code": "OS-00001",
        "status": "ACTIVE",
        "priority": "ROUTINE",
        "patient_id": "11c5be47-3215-4890-a79f-9c2b2293a85e",
        "practitioner_id": "0f7f838f-5bbd-43b7-951c-02582e4272a3",
        "created_at": datetime(2026, 5, 20, 8, 0, 0),
        "cancelled_at": None,
        "notes": "Check-up anual",
    },
    {
        "id": "cd974d08-25b3-4dad-b7d6-9b5fd0d1c775",
        "code": "OS-00002",
        "status": "ACTIVE",
        "priority": "URGENT",
        "patient_id": "e36e8749-a762-45ea-bd6b-63a5745d6e07",
        "practitioner_id": "8853e3c3-d0f9-469f-ae48-7813dc83b8ec",
        "created_at": datetime(2026, 5, 20, 9, 15, 0),
        "cancelled_at": None,
        "notes": "Investigacao oncológica",
    },
    {
        "id": "8be80631-8b87-4b62-a852-72d5926b021e",
        "code": "OS-00003",
        "status": "ACTIVE",
        "priority": "ROUTINE",
        "patient_id": "664d2678-29ce-450e-ab50-bd463364ded6",
        "practitioner_id": "35ca797f-5099-479d-91d5-fbe12a125b90",
        "created_at": datetime(2026, 5, 21, 10, 30, 0),
        "cancelled_at": None,
        "notes": "Painel metabólico ampliado",
    },
    {
        "id": "8b0282bf-12c0-4a91-ad86-966dfe59d660",
        "code": "OS-00004",
        "status": "COMPLETED",
        "priority": "ROUTINE",
        "patient_id": "57b22f32-fb64-4328-8aea-331c799e8c5b",
        "practitioner_id": "8853e3c3-d0f9-469f-ae48-7813dc83b8ec",
        "created_at": datetime(2026, 5, 18, 7, 45, 0),
        "cancelled_at": None,
        "notes": "Resultado liberado",
    },
    {
        "id": "6f9036b2-7130-47a5-9574-2bf5ce213fc7",
        "code": "OS-00005",
        "status": "CANCELLED",
        "priority": "STAT",
        "patient_id": "cbf0c4f8-6414-4e62-a9d6-8f5fae25e87f",
        "practitioner_id": "0f7f838f-5bbd-43b7-951c-02582e4272a3",
        "created_at": datetime(2026, 5, 19, 6, 20, 0),
        "cancelled_at": datetime(2026, 5, 19, 7, 0, 0),
        "notes": "Solicitação cancelada antes da coleta",
    },
]

SERVICE_REQUEST_ITEMS = [
    {
        "id": "d13f5fbd-0204-4796-96d6-fc0700e9a357",
        "service_request_id": "51f63f5b-3db9-40c9-9344-b86cb7dc30fd",
        "exam_code": "HEM001",
        "exam_name": "Hemograma",
        "status": "PENDING",
        "notes": None,
    },
    {
        "id": "940f4e0d-3769-4bbf-833b-a899c4c0fcae",
        "service_request_id": "51f63f5b-3db9-40c9-9344-b86cb7dc30fd",
        "exam_code": "GLI001",
        "exam_name": "Glicemia",
        "status": "PENDING",
        "notes": None,
    },
    {
        "id": "0de75868-77be-43d6-b269-af7ca2ac11a2",
        "service_request_id": "cd974d08-25b3-4dad-b7d6-9b5fd0d1c775",
        "exam_code": "ONC001",
        "exam_name": "Marcadores Tumorais",
        "status": "PENDING",
        "notes": "Aguardando roteamento",
    },
    {
        "id": "ee6d731b-f982-479d-a4b8-b534495b4591",
        "service_request_id": "8be80631-8b87-4b62-a852-72d5926b021e",
        "exam_code": "TSH001",
        "exam_name": "TSH",
        "status": "PENDING",
        "notes": None,
    },
    {
        "id": "7f5f0c63-6f1e-42c2-ab2b-edbb122cf7f2",
        "service_request_id": "8be80631-8b87-4b62-a852-72d5926b021e",
        "exam_code": "GEN001",
        "exam_name": "Teste Genético",
        "status": "PENDING",
        "notes": "Enviar ao laboratório de apoio",
    },
    {
        "id": "6d2d2f35-72a1-4c89-b2bb-c89fcd293f2e",
        "service_request_id": "8b0282bf-12c0-4a91-ad86-966dfe59d660",
        "exam_code": "COL001",
        "exam_name": "Colesterol Total",
        "status": "COMPLETED",
        "notes": None,
    },
    {
        "id": "29542b31-16b7-4f96-b738-81e44ae15358",
        "service_request_id": "8b0282bf-12c0-4a91-ad86-966dfe59d660",
        "exam_code": "URI001",
        "exam_name": "Urina Tipo I",
        "status": "COMPLETED",
        "notes": None,
    },
    {
        "id": "00c98da7-f6f7-4e3d-b565-7fe05bd0ca18",
        "service_request_id": "6f9036b2-7130-47a5-9574-2bf5ce213fc7",
        "exam_code": "CUL001",
        "exam_name": "Cultura e Antibiograma",
        "status": "CANCELLED",
        "notes": "Cancelado com a OS",
    },
]


def insert_patient_if_missing(session, patient_data):
    if session.get(Patient, patient_data["id"]) is None:
        session.add(Patient(**patient_data))


def insert_practitioner_if_missing(session, practitioner_data):
    if session.get(Practitioner, practitioner_data["id"]) is None:
        session.add(Practitioner(**practitioner_data))


def insert_exam_if_missing(session, exam_data):
    if (
        session.query(ExamCatalog)
        .filter_by(exam_code=exam_data["exam_code"])
        .first()
        is None
    ):
        session.add(ExamCatalog(**exam_data))


def insert_service_request_if_missing(session, service_request_data):
    if session.get(ServiceRequest, service_request_data["id"]) is None:
        session.add(ServiceRequest(**service_request_data))


def insert_service_request_item_if_missing(session, item_data):
    if session.get(ServiceRequestItem, item_data["id"]) is None:
        session.add(ServiceRequestItem(**item_data))


def reset_data(session):
    session.query(ServiceRequestItem).delete()
    session.query(ServiceRequest).delete()
    session.query(Practitioner).delete()
    session.query(Patient).delete()
    session.commit()
    rebuild_exam_catalog_table(session)


def exam_catalog_needs_rebuild(session):
    inspector = inspect(session.get_bind())
    if not inspector.has_table(ExamCatalog.__tablename__):
        return False

    columns = {column["name"] for column in inspector.get_columns(ExamCatalog.__tablename__)}
    primary_key = inspector.get_pk_constraint(ExamCatalog.__tablename__).get(
        "constrained_columns", []
    )
    return "id" not in columns or primary_key != ["id"]


def rebuild_exam_catalog_table(session):
    bind = session.get_bind()
    ExamCatalog.__table__.drop(bind=bind, checkfirst=True)
    ExamCatalog.__table__.create(bind=bind, checkfirst=True)


def database_is_empty(session):
    return (
        session.query(Patient.id).first() is None
        and session.query(Practitioner.id).first() is None
        and session.query(ExamCatalog.id).first() is None
        and session.query(ServiceRequest.id).first() is None
    )


def seed_database(session, reset=False):
    if reset:
        reset_data(session)
    elif exam_catalog_needs_rebuild(session):
        rebuild_exam_catalog_table(session)

    for patient_data in PATIENTS:
        insert_patient_if_missing(session, patient_data)
    for practitioner_data in PRACTITIONERS:
        insert_practitioner_if_missing(session, practitioner_data)
    for exam_data in EXAMS:
        insert_exam_if_missing(session, exam_data)
    for service_request_data in SERVICE_REQUESTS:
        insert_service_request_if_missing(session, service_request_data)
    session.flush()
    for item_data in SERVICE_REQUEST_ITEMS:
        insert_service_request_item_if_missing(session, item_data)
    session.commit()


def seed_database_if_empty(session):
    if not exam_catalog_needs_rebuild(session) and not database_is_empty(session):
        return False

    seed_database(session)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    session = SessionLocal()
    try:
        seed_database(session, reset=args.reset)
    finally:
        session.close()


if __name__ == "__main__":
    main()
