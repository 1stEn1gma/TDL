from datetime import datetime

from fastapi import Depends
from sqlalchemy import Table, Column, Integer, String, ForeignKey, TIMESTAMP, MetaData

from src.auth.base_config import current_user
from src.auth.models import user, User

metadata = MetaData()
c_user: User = Depends(current_user)

group = Table(
    "group",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey(user.c.id)),  # user
    Column("title", String, nullable=True),
    Column("labelText", String, nullable=False),
    Column("created_at", TIMESTAMP, default=datetime.utcnow),
)
