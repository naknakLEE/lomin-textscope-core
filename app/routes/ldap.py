from typing import List
from ldap3 import Connection, MODIFY_REPLACE
from ldap3.core.exceptions import LDAPException
from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse, JSONResponse
from app.utils.utils import print_error_log
from app.utils.auth import initialize_ldap
from rich import pretty
from rich.traceback import install
from rich.console import Console
install(show_locals=True)
pretty.install()
console = Console()


router = APIRouter()


PASSWORD = "lomin"
USER = f"cn=admin,dc=lomin,dc=ai"


@router.get("/user/search/dc")
async def search_ldap_user(
    dc: str, 
    objectClass: str,
    ldap_server=Depends(initialize_ldap)
):
    with Connection(ldap_server, user=USER, password=PASSWORD) as conn:
        try:
            conn.search(
                search_base=dc, # "cn=frontend,ou=groups,dc=lomin,dc=ai"
                search_filter=f"(objectClass={objectClass})",
                search_scope="SUBTREE",
                attributes=["member", "cn", "objectClass"],
            )
            console.log(conn.entries)
            user_info = {}
            for entry in conn.entries:
                key = (
                    "-".join(entry.cn.value)
                    if isinstance(entry.cn.value, list)
                    else entry.cn.value
                )
                user_info[key] = {
                    "cn": entry.cn.value,
                    "objectClass": entry.objectClass.value,
                    "member": entry.member.value,
                }
            return user_info
        except LDAPException:
            print_error_log()
    return PlainTextResponse("Search user failed", status_code=500)


@router.get("/user/search/cn")
async def search_ldap_user(
    cn: str, 
    dc: str,
    ldap_server=Depends(initialize_ldap)
):
    with Connection(ldap_server, user=USER, password=PASSWORD) as conn:
        try:
            conn.search(
                dc,
                f"(cn={cn})",
                attributes=["cn", "sn", "userPassword", "mail", "objectClass"],
            )
            user_info = {}
            entry = conn.entries[0]
            for key, value in vars(entry).items():
                if "state" not in key:
                    user_info[key] = value.value
            console.log(user_info)
            return JSONResponse(user_info, status_code=200)
        except LDAPException:
            print_error_log()
            # TODO: error return 형식으로 변경
            return JSONResponse({"msg": "Search user failed"}, status_code=500)


@router.post("/group/create")
async def add_ldap_group(
    objectClass: List[str], 
    gidNumber: str, 
    dn: str = "cn=group1,dc=lomin,dc=ai",
    ldap_server=Depends(initialize_ldap)
):
    with Connection(ldap_server, user=USER, password=PASSWORD) as conn:
        try:
            ldap_attr = {"objectClass": objectClass, "gidNumber": gidNumber}
            response = conn.add(dn, attributes=ldap_attr)
            console.log(conn.result)
        except LDAPException:
            print_error_log()
            response = False
    return PlainTextResponse(response)


@router.post("/user/create")
async def add_new_user_to_group(
    cn: str = "test user",
    sn: str = "AD",
    dn: str = "cn=testuser,cn=groups,dc=lomin,dc=ai",
    ldap_server=Depends(initialize_ldap)
):
    with Connection(ldap_server, user=USER, password=PASSWORD) as conn:
        ldap_attr = {"cn": cn, "sn": sn}
        try:
            response = conn.add(dn, object_class="inetOrgPerson", attributes=ldap_attr)
            console.log(conn.result)
        except LDAPException:
            print_error_log()
            response = False
    return PlainTextResponse(response)


@router.post("/user/delete")
async def delete_user(
    dn: str = "cn=testuser,cn=testgroup,dc=lomin,dc=ai",
    ldap_server=Depends(initialize_ldap)
):
    with Connection(ldap_server, user=USER, password=PASSWORD) as conn:
        try:
            response = conn.delete(dn=dn)
        except LDAPException:
            print_error_log()
            response = False
    return PlainTextResponse(response)


@router.put("/user/update")
async def update_user(
    dn: str = "cn=user1,ou=users,o=company", 
    givenName: str = "user2", 
    sn: str = "us",
    ldap_server=Depends(initialize_ldap)
):
    with Connection(ldap_server, user=USER, password=PASSWORD) as conn:
        try:
            conn.modify(
                dn,
                {
                    "givenName": [(MODIFY_REPLACE, [givenName])],
                    "sn": [(MODIFY_REPLACE, [sn])],
                },
            )
            console.log(conn.result)
        except LDAPException:
            print_error_log()
