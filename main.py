from typing import Optional, List, Any, Union
from fastapi import FastAPI, Query, Path, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from db import with_db
from services.vod import VodService
from utils.res import successResponse, pageResponse, badRequest, serverError, notFound, errorResponse


app = FastAPI(title="Vod API", version="1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def parse_positive_int(value: Optional[str], default: int, max_val: Optional[int] = None) -> int:
    if value is None:
        return default
    try:
        num = int(value)
    except (ValueError, TypeError):
        return default
    if num < 1:
        return default
    if max_val is not None and num > max_val:
        return max_val
    return num


# 请求体模型
class BatchIdsBody(BaseModel):
    ids: List[Any] = Field(..., description="影片ID数组")


@app.get("/api/vod/list")
async def vod_list(
    page: int = Query(1),
    size: int = Query(10),
    pid: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    year: Optional[str] = Query(None),
    area: Optional[str] = Query(None),
    lang: Optional[str] = Query(None, alias="lang"),
    class_: Optional[str] = Query(None, alias="class"),
    sort: str = Query("vod_time"),
    order: str = Query("DESC"),
):
    try:
        page = parse_positive_int(str(page), 1)
        size = parse_positive_int(str(size), 10, 50)
        params = {
            "page": page,
            "size": size,
            "pid": pid,
            "type": type,
            "year": year,
            "area": area,
            "lang": lang,
            "class": class_,
            "sort": sort,
            "order": order,
        }
        ret = with_db(lambda cur, conn: VodService.get_list(cur, params))
        return pageResponse(ret["list"], ret["total"], ret["page"], ret["limit"])
    except Exception as e:
        print("getList error", e)
        return serverError(str(e))


@app.get("/api/vod/detail/{id}")
async def vod_detail(id: int = Path(..., gt=0)):
    try:
        row = with_db(lambda cur, conn: VodService.get_detail(cur, id))
        if not row:
            return notFound("影片不存在")
        return successResponse(row)
    except Exception as e:
        print("detail error", e)
        return serverError(str(e))


@app.get("/api/vod/search")
async def vod_search(
    keyword: str = Query(...),
    page: int = Query(1),
    size: int = Query(10),
    year: Optional[str] = Query(""),
):
    try:
        keyword = keyword.strip()
        if not keyword:
            return badRequest("请输入搜索关键词")
        page = parse_positive_int(str(page), 1)
        size = parse_positive_int(str(size), 10, 50)
        ret = with_db(lambda cur, conn: VodService.search(cur, keyword, year, page, size))
        return pageResponse(ret["list"], ret["total"], ret["page"], ret["limit"])
    except Exception as e:
        print("search error", e)
        return serverError(str(e))


@app.get("/api/vod/categories")
async def categories():
    try:
        rows = with_db(lambda cur, conn: VodService.get_categories(cur))
        return successResponse(rows)
    except Exception as e:
        print("categories error", e)
        return serverError(str(e))


@app.get("/api/vod/categories/tree")
async def categories_tree():
    try:
        tree = with_db(lambda cur, conn: VodService.build_category_tree(cur))
        return successResponse(tree)
    except Exception as e:
        print("tree error", e)
        return serverError(str(e))


@app.get("/api/vod/categories/parent")
async def categories_parent():
    try:
        rows = with_db(lambda cur, conn: VodService.get_parent_categories(cur))
        return successResponse(rows)
    except Exception as e:
        print("parent cat error", e)
        return serverError(str(e))


@app.get("/api/vod/categories/children/{pid}")
async def categories_children(pid: int = Path(..., gt=0)):
    try:
        rows = with_db(lambda cur, conn: VodService.get_children_categories(cur, pid))
        return successResponse(rows)
    except Exception as e:
        print("children cat error", e)
        return serverError(str(e))


@app.get("/api/vod/rank")
async def vod_rank(size: int = Query(10)):
    try:
        limit = parse_positive_int(str(size), 10, 100)
        rows = with_db(lambda cur, conn: VodService.get_rank(cur, limit))
        return successResponse(rows)
    except Exception as e:
        print("rank error", e)
        return serverError(str(e))


@app.get("/api/vod/relate")
async def vod_relate(
    type_id: int = Query(...),
    exclude_id: int = Query(0),
    size: int = Query(5),
):
    try:
        if type_id <= 0:
            return badRequest("请提供有效的 type_id 参数")
        limit = parse_positive_int(str(size), 5, 20)
        rows = with_db(lambda cur, conn: VodService.get_relate(cur, type_id, exclude_id, limit))
        return successResponse(rows)
    except Exception as e:
        print("relate error", e)
        return serverError(str(e))


@app.get("/api/vod/stats")
async def vod_stats():
    try:
        row = with_db(lambda cur, conn: VodService.get_stats(cur))
        return successResponse(row)
    except Exception as e:
        print("stats error", e)
        return serverError(str(e))


@app.get("/api/vod/years")
async def vod_years():
    try:
        rows = with_db(lambda cur, conn: VodService.get_years(cur))
        return successResponse(rows)
    except Exception as e:
        print("years error", e)
        return serverError(str(e))


@app.get("/api/vod/areas")
async def vod_areas():
    try:
        rows = with_db(lambda cur, conn: VodService.get_areas(cur))
        return successResponse(rows)
    except Exception as e:
        print("areas error", e)
        return serverError(str(e))


@app.post("/api/vod/batch")
async def vod_batch(body: BatchIdsBody = Body(...)):
    try:
        ids = body.ids
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


# 全局404捕获
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return errorResponse(404, "接口不存在")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
