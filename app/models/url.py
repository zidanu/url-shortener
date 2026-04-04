from peewee import CharField, DateTimeField
import datetime
from app.database import BaseModel


class URL(BaseModel):
    original_url = CharField()
    short_code = CharField(unique=True)
    created_at = DateTimeField(default=datetime.datetime.now)
