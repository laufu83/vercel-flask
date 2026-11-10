import threading
from fastapi import APIRouter
from services.sync_service import SyncService
from utils.res import successResponse
from config import API_BASE_URL, MAX_THREAD

sync_router = APIRouter(prefix="/api/sync")
# 全局单例，给路由调用
sync_service = SyncService(
    api_base_url=API_BASE_URL,
    table_name="vod",
    max_thread=MAX_THREAD
)


@sync_router.get("/start")
async def sync_start():
    st = sync_service.get_sync_status()
    if st["is_running"]:
        return successResponse(data=None, msg="同步任务正在运行中")
    t = threading.Thread(target=sync_service.sync_start, daemon=True)
    t.start()
    return successResponse(data=None, msg="同步任务已启动")


@sync_router.get("/status")
async def sync_status():
    return successResponse(data=sync_service.get_sync_status(), msg="ok")


@sync_router.get("/stop")
async def sync_stop():
    sync_service.mark_sync_stop()
    return successResponse(data=None, msg="已标记停止，正在执行的页面会跑完")
