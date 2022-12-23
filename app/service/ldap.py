from ldap3 import Connection, MODIFY_REPLACE
from ldap3.core.exceptions import LDAPException
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse

from app.utils.auth import initialize_ldap
from app.utils.utils import pretty_dict
from app.common.const import get_settings
from app.utils.logging import logger
from app.schemas.ldap import GroupAdd, NewUserAddToGroup, UserDelete, UserUpdate



settings = get_settings()

async def search_ldap_user_all(
    dc: str ,
    objectClass: str,
    ldap_server,
):
    with Connection(
        ldap_server,
        user=settings.LDAP_ADMIN_USER,
        password=settings.LDAP_ADMIN_PASSWORD,
    ) as conn:
        try:
            success = conn.search(
                search_base=dc,
                search_filter=f"(objectClass={objectClass})",
                search_scope="SUBTREE",
                attributes=["member", "sn", "cn", "objectClass"],
            )
            result = {}
            if success:
                for entry in conn.entries:
                    key = (
                        "-".join(entry.cn.value)
                        if isinstance(entry.cn.value, list)
                        else entry.cn.value
                    )
                    result[key] = {
                        "cn": entry.cn.value,
                        "sn": entry.sn.value,
                        "objectClass": entry.objectClass.value,
                        "member": entry.member.value,
                    }
                logger.info("Search user result: \n{}".format(pretty_dict(result)))
            else:
                logger.warning("Search user failed")
        except LDAPException:
            msg = "[LDAPException]Search user failed"
            logger.exception(msg)
            raise HTTPException(status_code=500, detail={"msg": msg})
        except Exception:
            msg = "[Exception]Search user failed"
            logger.exception(msg)
            raise HTTPException(status_code=500, detail={"msg": msg})
    return JSONResponse(content=result, status_code=200)


async def search_ldap_user(
    cn: str,
    dc: str,
    ldap_server,
):
    result = {}
    with Connection(
        ldap_server,
        user=settings.LDAP_ADMIN_USER,
        password=settings.LDAP_ADMIN_PASSWORD,
    ) as conn:
        try:
            success = conn.search(
                dc,
                f"(cn={cn})",
                attributes=["cn", "sn", "mail", "objectClass"],
            )
            if success:
                entry = conn.entries[0]
                for key, value in vars(entry).items():
                    if "state" not in key:
                        result[key] = value.value
                logger.info(pretty_dict(result))
            else:
                logger.warning("Search user failed")
        except LDAPException:
            msg = "[LDAPException]Search user failed"
            logger.exception(msg)
            raise HTTPException(status_code=500, detail={"msg": msg})
        except Exception:
            msg = "[Exception]Search user failed"
            logger.exception(msg)
            raise HTTPException(status_code=500, detail={"msg": msg})
    return JSONResponse(content=result, status_code=200)


async def add_ldap_group(
    inputs: GroupAdd,
    ldap_server,
):
    result = "\n"
    with Connection(
        ldap_server,
        user=settings.LDAP_ADMIN_USER,
        password=settings.LDAP_ADMIN_PASSWORD,
    ) as conn:
        try:
            ldap_attr = {
                "objectClass": inputs.objectClass,
                "gidNumber": inputs.gidNumber,
            }
            success = conn.add(inputs.dn, attributes=ldap_attr)
            conn_result = conn.result
            result = conn_result.get("description")
            if success:
                logger.info("Add group result: \n{}".format(pretty_dict(conn_result)))
            else:
                logger.warning("Add group result: \n{}".format(pretty_dict(conn_result)))
                result = conn_result.get("description")
        except LDAPException:
            msg = "[LDAPException]Search ldap group failed"
            logger.exception(msg)
            raise HTTPException(status_code=500, detail={"msg": msg})
        except Exception:
            msg = "[Exception]Search ldap group failed"
            logger.exception(msg)
            raise HTTPException(status_code=500, detail={"msg": msg})
    return PlainTextResponse(status_code=201, content=result)



async def add_new_user_to_group(
    inputs: NewUserAddToGroup,
    ldap_server,
):
    result = "\n"
    with Connection(
        ldap_server,
        user=settings.LDAP_ADMIN_USER,
        password=settings.LDAP_ADMIN_PASSWORD,
    ) as conn:
        ldap_attr = {"cn": inputs.cn, "sn": inputs.sn, "mail": inputs.mail}
        try:
            success = conn.add(
                inputs.dn, object_class="inetOrgPerson", attributes=ldap_attr
            )
            conn_result = conn.result
            if success:
                logger.info("Add user result: \n{}".format(pretty_dict(conn_result)))
            else:
                logger.warning("Add user result: \n{}".format(pretty_dict(conn_result)))
                result = conn_result.get("description")
        except LDAPException:
            msg = "[LDAPException]Add new user to group failed"
            logger.exception(msg)
            raise HTTPException(status_code=500, detail={"msg": msg})
        except Exception:
            msg = "[Exception]Add new user to group failed"
            logger.exception(msg)
            raise HTTPException(status_code=500, detail={"msg": msg})
    return PlainTextResponse(status_code=201, content=result)


async def delete_user(
    inputs: UserDelete,
    ldap_server,
):
    result = "\n"
    with Connection(
        ldap_server,
        user=settings.LDAP_ADMIN_USER,
        password=settings.LDAP_ADMIN_PASSWORD,
    ) as conn:
        try:
            success = conn.delete(dn=inputs.dn)
            conn_result = conn.result
            if success:
                logger.info("Delete user result: \n{}".format(pretty_dict(conn_result)))
            else:
                logger.warning("Delete user result: \n{}".format(pretty_dict(conn_result)))
                result = conn_result.get("description")
        except LDAPException:
            msg = "[LDAPException]Delete user failed"
            logger.exception(msg)
            raise HTTPException(status_code=500, detail={"msg": msg})
        except Exception:
            msg = "[Exception]Delete user failed"
            logger.exception(msg)
            raise HTTPException(status_code=500, detail={"msg": msg})
    return PlainTextResponse(content=result, status_code=200)



async def update_user(
    inputs: UserUpdate,
    ldap_server=Depends(initialize_ldap),
):
    result = "\n"
    with Connection(
        ldap_server,
        user=settings.LDAP_ADMIN_USER,
        password=settings.LDAP_ADMIN_PASSWORD,
    ) as conn:
        try:
            success = conn.modify(
                inputs.dn,
                {
                    "givenName": [(MODIFY_REPLACE, [inputs.givenName])],
                    "sn": [(MODIFY_REPLACE, [inputs.sn])],
                },
            )
            conn_result = conn.result
            if success:
                logger.info("Update user result: \n{}".format(pretty_dict(conn_result)))
            else:
                logger.warning("Update user result: \n{}".format(pretty_dict(conn_result)))
                result = conn_result.get("description")
        except LDAPException:
            msg = "[LDAPException]Update user failed"
            logger.exception(msg)
            raise HTTPException(status_code=500, detail={"msg": msg})
        except Exception:
            msg = "[Exception]Update user failed"
            logger.exception(msg)
            raise HTTPException(status_code=500, detail={"msg": msg})
    return PlainTextResponse(content=result, status_code=200)
