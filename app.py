from flask import Flask, request
from flask_cors import CORS

from db import with_db
from services.vod import VodService
from utils.res import successResponse, pageResponse, badRequest, serverError, notFound, errorResponse

app = Flask(__name__)
app.json.ensure_ascii = False
CORS(app)

def parsePositiveInt(value, defaultValue: int, max_val=None) -> int:
    if value is None:
        return defaultValue
    try:
        num = int(value)
    except (ValueError, TypeError):
        return defaultValue
    if num < 1:
        return defaultValue
    if max_val is not None and num > max_val:
        return max_val
    return num


@app.route("/api/vod/list", methods=["GET"])
def vod_list():
    try:
        page = parsePositiveInt(request.args.get("page"), 1)
        size = parsePositiveInt(request.args.get("size"), 10, 50)
        params = {
            "page": page,
            "size": size,
            "pid": request.args.get("pid"),
            "type": request.args.get("type"),
            "year": request.args.get("year"),
            "area": request.args.get("area"),
            "lang": request.args.get("lang"),
            "class": request.args.get("class"),
            "sort": request.args.get("sort", "vod_time"),
            "order": request.args.get("order", "DESC"),
        }
        ret = with_db(lambda cur, conn: VodService.get_list(cur, params))
        return pageResponse(ret["list"], ret["total"], ret["page"], ret["limit"])
    except Exception as e:
        print("getList error", e)
        return serverError(str(e))


@app.route("/api/vod/detail/<int:id>", methods=["GET"])
def vod_detail(id):
    try:
        if id <= 0:
            return badRequest("无效的影片 ID")
        row = with_db(lambda cur, conn: VodService.get_detail(cur, id))
        if not row:
            return notFound("影片不存在")
        return successResponse(row)
    except Exception as e:
        print("detail error", e)
        return serverError(str(e))


@app.route("/api/vod/search", methods=["GET"])
def vod_search():
    try:
        keyword = request.args.get("keyword", "").strip()
        if not keyword:
            return badRequest("请输入搜索关键词")
        page = parsePositiveInt(request.args.get("page"), 1)
        size = parsePositiveInt(request.args.get("size"), 10, 50)
        year = request.args.get("year", "")
        ret = with_db(lambda cur, conn: VodService.search(cur, keyword, year, page, size))
        return pageResponse(ret["list"], ret["total"], ret["page"], ret["limit"])
    except Exception as e:
        print("search error", e)
        return serverError(str(e))


@app.route("/api/vod/categories", methods=["GET"])
def categories():
    try:
        rows = with_db(lambda cur,conn: VodService.get_categories(cur))
        return successResponse(rows)
    except Exception as e:
        print("categories error", e)
        return serverError(str(e))


@app.route("/api/vod/categories/tree", methods=["GET"])
def categories_tree():
    try:
        tree = with_db(lambda cur,conn: VodService.build_category_tree(cur))
        return successResponse(tree)
    except Exception as e:
        print("tree error", e)
        return serverError(str(e))


@app.route("/api/vod/categories/parent", methods=["GET"])
def categories_parent():
    try:
        rows = with_db(lambda cur,conn: VodService.get_parent_categories(cur))
        return successResponse(rows)
    except Exception as e:
        print("parent cat error", e)
        return serverError(str(e))


@app.route("/api/vod/categories/children/<int:pid>", methods=["GET"])
def categories_children(pid):
    try:
        rows = with_db(lambda cur, conn: VodService.get_children_categories(cur, pid))
        return successResponse(rows)
    except Exception as e:
        print("children cat error", e)
        return serverError(str(e))


@app.route("/api/vod/rank", methods=["GET"])
def vod_rank():
    try:
        limit = parsePositiveInt(request.args.get("size"), 10, 100)
        rows = with_db(lambda cur, conn: VodService.get_rank(cur, limit))
        return successResponse(rows)
    except Exception as e:
        print("rank error", e)
        return serverError(str(e))


@app.route("/api/vod/relate", methods=["GET"])
def vod_relate():
    try:
        type_id_str = request.args.get("type_id",0)
        exclude_id_str = request.args.get("exclude_id", "0")
        try:
            type_id = int(type_id_str)
            exclude_id = int(exclude_id_str)
        except Exception:
            return badRequest("请提供有效的 type_id 参数")
        if type_id <= 0:
            return badRequest("请提供有效的 type_id 参数")
        limit = parsePositiveInt(request.args.get("size"), 5, 20)
        rows = with_db(lambda cur, conn: VodService.get_relate(cur, type_id, exclude_id, limit))
        return successResponse(rows)
    except Exception as e:
        print("relate error", e)
        return serverError(str(e))


@app.route("/api/vod/stats", methods=["GET"])
def vod_stats():
    try:
        row = with_db(lambda cur,conn: VodService.get_stats(cur))
        return successResponse(row)
    except Exception as e:
        print("stats error", e)
        return serverError(str(e))


@app.route("/api/vod/years", methods=["GET"])
def vod_years():
    try:
        rows = with_db(lambda cur,conn: VodService.get_years(cur))
        return successResponse(rows)
    except Exception as e:
        print("years error", e)
        return serverError(str(e))


@app.route("/api/vod/areas", methods=["GET"])
def vod_areas():
    try:
        rows = with_db(lambda cur,conn: VodService.get_areas(cur))
        return successResponse(rows)
    except Exception as e:
        print("areas error", e)
        return serverError(str(e))


@app.route("/api/vod/batch", methods=["POST"])
def vod_batch():
    try:
        body = request.get_json(silent=True) or {}
        ids = body.get("ids", [])
        if not isinstance(ids, list) or len(ids) == 0:
            return badRequest("请提供有效的影片 ID 列表")
        if len(ids) > 100:
            return badRequest("最多支持 100 个影片 ID")
        valid_ids = [x for x in ids if isinstance(x, int) and x > 0]
        if len(valid_ids) == 0:
            return badRequest("请提供有效的数字 ID 列表")
        rows = with_db(lambda cur, conn: VodService.batch_get(cur, valid_ids))
        return successResponse(rows)
    except Exception as e:
        print("batch error", e)
        return serverError(str(e))


@app.errorhandler(404)
def page_not_found(e):
    return errorResponse(404, "接口不存在")


if __name__ == "__main__":
    app.run(debug=False)
