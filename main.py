from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from contacts import models, schemas, database
from typing import List
from datetime import date, timedelta
from sqlalchemy import func

app = FastAPI(
    title="Contacts API",
    description="API for managing contacts.",
    version="1.0.0",
)


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/contacts/birthdays/next_week")
async def get_birthdays_next_week(db: Session = Depends(get_db)):
    today = date.today()

    next_week = today + timedelta(days=7)

    contacts = (
        db.query(models.Contact)
        .filter(
            (func.extract("month", models.Contact.birth_date) == today.month)
            & (func.extract("day", models.Contact.birth_date) >= today.day)
            & (func.extract("day", models.Contact.birth_date) <= next_week.day)
        )
        .all()
    )

    return contacts


@app.get("/contacts/search", response_model=List[schemas.Contact])
def search_contacts(
    db: Session = Depends(get_db),
    name: str = Query(None, description="Ім'я контакту для пошуку"),
    last_name: str = Query(None, description="Прізвище контакту для пошуку"),
    email: str = Query(None, description="Електронна адреса контакту для пошуку"),
):
    query = db.query(models.Contact)

    if name:
        query = query.filter(models.Contact.first_name.contains(name))

    if last_name:
        query = query.filter(models.Contact.last_name.contains(last_name))

    if email:
        query = query.filter(models.Contact.email.contains(email))

    contacts = query.all()

    return contacts


@app.post("/contacts/", response_model=schemas.Contact)
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db)):
    db_contact = models.Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


@app.get("/contacts/{contact_id}", response_model=schemas.Contact)
def read_contact(contact_id: int, db: Session = Depends(get_db)):
    db_contact = (
        db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    )
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact


@app.get("/contacts/", response_model=list[schemas.Contact])
def read_contacts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    contacts = db.query(models.Contact).offset(skip).limit(limit).all()
    return contacts


@app.put("/contacts/{contact_id}", response_model=schemas.Contact)
def update_contact(
    contact_id: int, contact: schemas.ContactUpdate, db: Session = Depends(get_db)
):
    db_contact = (
        db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    )
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    for key, value in contact.dict().items():
        setattr(db_contact, key, value)

    db.commit()
    db.refresh(db_contact)
    return db_contact


@app.delete("/contacts/{contact_id}", response_model=schemas.Contact)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    db_contact = (
        db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    )
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(db_contact)
    db.commit()
    return db_contact


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
