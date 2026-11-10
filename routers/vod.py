from typing import Optional, List, Any
from fastapi import Query, Path, Body, APIRouter
from pydantic import BaseModel, Field
from db import with_db
from services.vod_service import VodService
from utils.res import successResponse, pageResponse, badRequest, serverError, notFound

# 注册路由
vod_router = APIRouter(prefix="/api/vod")
# 请求体模型
class BatchIdsBody(BaseModel):
    ids: List[Any] = Field(..., description="影片ID数组")


@vod_router.get("/list")
async def vod_list(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=100),
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


@vod_router.get("/detail/{id}")
async def vod_detail(id: int = Path(..., gt=0)):
    try:
        row = with_db(lambda cur, conn: VodService.get_detail(cur, id))
        if not row:
            return notFound("影片不存在")
        return successResponse(row)
    except Exception as e:
        print("detail error", e)
        return serverError(str(e))


@vod_router.get("/search")
async def vod_search(
        keyword: str = Query(...),
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, lt=100),
        year: Optional[str] = Query(None),
):
    try:
        keyword = keyword.strip()
        if not keyword:
            return badRequest("请输入搜索关键词")
        ret = with_db(lambda cur, conn: VodService.search(cur, keyword, year or "", page, size))
        return pageResponse(ret["list"], ret["total"], ret["page"], ret["limit"])
    except Exception as e:
        print("search error", e)
        return serverError(str(e))


@vod_router.get("/categories")
async def categories():
    try:
        rows = with_db(lambda cur, conn: VodService.get_categories(cur))
        return successResponse(rows)
    except Exception as e:
        print("categories error", e)
        return serverError(str(e))


@vod_router.get("/categories/tree")
async def categories_tree():
    try:
        tree = with_db(lambda cur, conn: VodService.build_category_tree(cur))
        return successResponse(tree)
    except Exception as e:
        print("tree error", e)
        return serverError(str(e))


@vod_router.get("/categories/parent")
async def categories_parent():
    try:
        rows = with_db(lambda cur, conn: VodService.get_parent_categories(cur))
        return successResponse(rows)
    except Exception as e:
        print("parent cat error", e)
        return serverError(str(e))


@vod_router.get("/categories/children/{pid}")
async def categories_children(pid: int = Path(..., gt=0)):
    try:
        rows = with_db(lambda cur, conn: VodService.get_children_categories(cur, pid))
        return successResponse(rows)
    except Exception as e:
        print("children cat error", e)
        return serverError(str(e))


@vod_router.get("/rank")
async def vod_rank(size: int = Query(10, ge=1, lt=100)):
    try:
        rows = with_db(lambda cur, conn: VodService.get_rank(cur, size))
        return successResponse(rows)
    except Exception as e:
        print("rank error", e)
        return serverError(str(e))


@vod_router.get("/relate")
async def vod_relate(
        type_id: int = Query(...),
        exclude_id: int = Query(0),
        size: int = Query(5),
):
    try:
        if type_id <= 0:
            return badRequest("请提供有效的 type_id 参数")

        rows = with_db(lambda cur, conn: VodService.get_relate(cur, type_id, exclude_id, size))
        return successResponse(rows)
    except Exception as e:
        print("relate error", e)
        return serverError(str(e))


@vod_router.get("/stats")
async def vod_stats():
    try:
        row = with_db(lambda cur, conn: VodService.get_stats(cur))
        return successResponse(row)
    except Exception as e:
        print("stats error", e)
        return serverError(str(e))


@vod_router.get("/years")
async def vod_years():
    try:
        rows = with_db(lambda cur, conn: VodService.get_years(cur))
        return successResponse(rows)
    except Exception as e:
        print("years error", e)
        return serverError(str(e))


@vod_router.get("/areas")
async def vod_areas():
    try:
        rows = with_db(lambda cur, conn: VodService.get_areas(cur))
        return successResponse(rows)
    except Exception as e:
        print("areas error", e)
        return serverError(str(e))


@vod_router.post("/batch")
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
