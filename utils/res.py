from flask import jsonify

def successResponse(data):
    return jsonify({"code": 0, "msg": "ok", "data": data})

def errorResponse(code, msg):
    return jsonify({"code": code, "msg": msg, "data": None}), code

def pageResponse(list_data, total, page, limit):
    return jsonify({
        "code": 0,
        "msg": "ok",
        "data": {
            "list": list_data,
            "total": total,
            "page": page,
            "limit": limit
        }
    })

def badRequest(msg="参数错误"):
    return errorResponse(400, msg)

def serverError(msg="服务器异常"):
    return errorResponse(500, msg)

def notFound(msg="资源不存在"):
    return errorResponse(404, msg)
