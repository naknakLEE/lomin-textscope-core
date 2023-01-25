from ldap3 import Connection, MODIFY_REPLACE
from ldap3.core.exceptions import LDAPException
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse

from app.utils.auth import initialize_ldap
from app.utils.utils import pretty_dict
from app.common.const import get_settings
from app.utils.logging import logger
from app.schemas.ldap import GroupAdd, NewUserAddToGroup, UserDelete, UserUpdate
from app.service.ldap import (
    search_ldap_user_all as search_ldap_user_all_service,
    search_ldap_user as search_ldap_user_service,
    add_ldap_group as add_ldap_group_service,
    add_new_user_to_group as add_new_user_to_group_service,
    delete_user as delete_user_service,
    update_user as update_user_service
)


settings = get_settings()
router = APIRouter()


@router.get("/user/dc")
async def search_ldap_user_all(
    dc: str = "dc=lomin,dc=ai",
    objectClass: str = "inetOrgPerson",
    ldap_server = Depends(initialize_ldap),
):
    return await search_ldap_user_all_service(
        dc = dc,
        objectClass = objectClass,
        ldap_server =ldap_server
    )



@router.get("/user/cn")
async def search_ldap_user(
    cn: str = "test-lomin",
    dc: str = "dc=lomin,dc=ai",
    ldap_server=Depends(initialize_ldap),
):
    return await search_ldap_user_service(
        cn = cn,
        dc = dc,
        ldap_server = ldap_server
    )


@router.post("/group")
async def add_ldap_group(
    inputs: GroupAdd,
    ldap_server=Depends(initialize_ldap),
):
    return await add_ldap_group_service(
        inputs = inputs,
        ldap_server = ldap_server
    )


@router.post("/user")
async def add_new_user_to_group(
    inputs: NewUserAddToGroup,
    ldap_server=Depends(initialize_ldap),
):
    return await add_new_user_to_group_service(
        inputs = inputs,
        ldap_server = ldap_server
    )

@router.delete("/user")
async def delete_user(
    inputs: UserDelete,
    ldap_server=Depends(initialize_ldap),
):
    return await delete_user_service(
        inputs = inputs,
        ldap_server = ldap_server
    )


@router.put("/user/update")
async def update_user(
    inputs: UserUpdate,
    ldap_server=Depends(initialize_ldap),
):
    return await update_user_service(
        inputs = inputs,
        ldap_server = ldap_server
    )