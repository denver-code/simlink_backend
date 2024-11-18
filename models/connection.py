from pydantic import BaseModel


class Connection(BaseModel):
    from_interface: str
    to_interface: str
