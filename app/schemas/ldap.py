from typing import List
from pydantic.main import BaseModel


class GroupAdd(BaseModel):
    objectClass: List[str] = ["top", "posixGroup"]
    gidNumber: str = 12345
    dn: str = "cn=group1,dc=lomin,dc=ai"


class NewUserAddToGroup(BaseModel):
    cn: str = "lomin-test"
    sn: str = "lt"
    dn: str = "cn=lomin-test,dc=lomin,dc=ai"


class UserDelete(BaseModel):
    dn: str = "cn=frontend,dc=lomin,dc=ai"


class UserUpdate(BaseModel):
    dn: str = "cn=frontend,dc=lomin,dc=ai"
    givenName: str = "replaced-test-lomin"
    sn: str = "replaced-test-lomin"
