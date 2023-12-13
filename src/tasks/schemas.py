import datetime
from typing import Annotated, Union, List, Optional

from fastapi import Query
from pydantic import BaseModel, field_validator, validator

m_list = ["important", "notes", "links", "completed", "deleted"]


# class TypeTitle(Enum):
#     important = "important"
#     notes = "notes"
#     links = "links"
#     completed = "completed"
#     deleted = "deleted"


class TaskBase(BaseModel):
    title: str  # "important", "notes", "links", "completed", "deleted", "expired"
    labelText: Annotated[str, Query(min_length=3, max_length=100)]
    do_before: datetime.date
    on_this_day: bool

    @field_validator('title')
    def validate_field(cls, value):
        valid_values = ["important", "notes", "links", "completed", "deleted", "expired"]
        if value not in valid_values:
            raise ValueError(f"Invalid value for field. Allowed values are: {valid_values}")
        return value


class TaskCreate(TaskBase):
    @field_validator('do_before')
    def validate_field2(cls, value):
        print(f'value:{value} now: {datetime.datetime.now().date()}')
        if value < datetime.date.today():
            raise ValueError(f"Enter a valid date.")
        return value


class Task(TaskBase):
    id: int
    user_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True  # orm_mode = True


class TaskData(BaseModel):
    relevant: Optional[List[Task]]
    current: Optional[List[Task]]


class ResponseForGetTasks(BaseModel):
    status: str = "200"
    data: TaskData
    details: str | None
