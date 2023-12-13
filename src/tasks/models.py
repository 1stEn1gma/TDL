from datetime import datetime

from fastapi import Depends
from sqlalchemy import Table, Column, Integer, String, ForeignKey, TIMESTAMP, MetaData, Boolean

from src.auth.base_config import current_user
from src.auth.models import user, User

metadata = MetaData()
c_user: User = Depends(current_user)

tasks = Table(
    "task",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey(user.c.id)),  # owner
    Column("title", String, nullable=False),  # "important", "notes", "links", "completed", "deleted"
    Column("labelText", String, nullable=False),  # desc
    Column("created_at", TIMESTAMP, default=datetime.utcnow),
    Column("do_before", TIMESTAMP, nullable=False),
    Column("on_this_day", Boolean, nullable=False)
)
