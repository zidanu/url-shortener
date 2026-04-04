from peewee import CharField, DateTimeField, TextField, IntegerField
import datetime
from app.database import BaseModel


class Event(BaseModel):
    url_id = IntegerField()
    user_id = IntegerField(null=True)
    event_type = CharField()
    timestamp = DateTimeField(default=datetime.datetime.now)
    details = TextField(null=True)
