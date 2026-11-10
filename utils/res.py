# from flask import jsonify
#
# def successResponse(data):
#     return jsonify({"code": 0, "msg": "ok", "data": data})
#
# def errorResponse(code, msg):
#     return jsonify({"code": code, "msg": msg, "data": None}), code
#
# def pageResponse(list_data, total, page, limit):
#     return jsonify({
#         "code": 0,
#         "msg": "ok",
#         "data": {
#             "list": list_data,
#             "total": total,
#             "page": page,
#             "limit": limit
#         }
#     })
#
# def badRequest(msg="参数错误"):
#     return errorResponse(400, msg)
#
# def serverError(msg="服务器异常"):
#     return errorResponse(500, msg)
#
# def notFound(msg="资源不存在"):
#     return errorResponse(404, msg)

# utils/res.py
# utils/res.py
from fastapi.responses import JSONResponse
from typing import Any
import datetime


def serialize_datetime(obj: Any) -> Any:
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    return obj


def successResponse(data: Any, msg: str = "ok") -> JSONResponse:
    return JSONResponse(
        content=serialize_datetime({"code": 0, "msg": msg, "data": data})
    )


def errorResponse(code: int, msg: str) -> JSONResponse:
    return JSONResponse(
        content={"code": code, "msg": msg, "data": None},
        status_code=code
    )


def pageResponse(list_data: Any, total: int, page: int, limit: int) -> JSONResponse:
    payload = {
        "code": 0,
        "msg": "ok",
        "data": {
            "list": list_data,
            "total": total,
            "page": page,
            "limit": limit
        }
    }
    return JSONResponse(content=serialize_datetime(payload))


def badRequest(msg: str = "参数错误") -> JSONResponse:
    return errorResponse(400, msg)


def serverError(msg: str = "服务器异常") -> JSONResponse:
    return errorResponse(500, msg)


def notFound(msg: str = "资源不存在") -> JSONResponse:
    return errorResponse(404, msg)
