from peewee import CharField, DateTimeField, BooleanField, ForeignKeyField, TextField
import datetime
from app.database import BaseModel


class URL(BaseModel):
    user_id = CharField(null=True)
    short_code = CharField(unique=True)
    original_url = CharField()
    title = TextField(null=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)
