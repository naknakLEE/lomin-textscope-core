inference_responses = {
    200: {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "example": {
                    "status": "1200",
                    "minQlt": "00",
                    "reliability": "0.367125",
                    "lnbzDocClcd": "00",
                    "ocrResult": {
                        "tenantName": "홍길동",
                        "tenantID": "200123-1234567",
                        "memberNum": "5",
                        "memberList": {
                            "memberName": "심청이",
                            "memberID": "510123-2234567",
                            "memberRelation": "배우자",
                            "status": "00",
                        },
                        "releaseData": "2021-02-10",
                    },
                }
            }
        },
    }
}


users_me_responses = {
    200: {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "example": {
                    "email": "garam@example.com",
                    "username": "garam",
                    "full_name": "Garam Yoon",
                    "is_superuser": False,
                    "id": 0,
                },
            }
        },
    },
}


# dict는 key 필요 -> 리스트는 표현하기 어려움
# usage_me_responses = {
#     200: {
#         "description": "Successful Response",
#         "content": {
#             "application/json": {
#                 "example": {
#                     tuple([
#                         {
#                             "created_at": "2021-06-23 06:49:50",
#                             "status_code": 0000,
#                             "email": "garam@example.com"
#                         }
#                     ]),
#                 },
#             }
#         }
#     },
# }

auth_token_responses = {
    200: {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "example": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
                    "token_type": "Bearer",
                },
            }
        },
    },
}


admin_users_responses = {
    200: {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "example": {
                    "email": "garam@example.com",
                    "usernasme": "garma",
                    "full_name": "Garam Yoon",
                    "is_superuser": False,
                    "id": 0,
                },
            }
        },
    },
}
