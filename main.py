from fastapi import FastAPI, Request
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# 导入拆分出去的同步路由
from routers.sync import sync_router
from routers.vod import vod_router
from utils.res import errorResponse

# CORS 修复：* 不能搭配 allow_credentials
# 在这里配置 middleware
app = FastAPI(
    title="Vod API",
    version="1.0",
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]
)
# 注册路由
app.include_router(sync_router)
app.include_router(vod_router)


# 全局404捕获
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return errorResponse(404, "接口不存在")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
