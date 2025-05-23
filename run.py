import uvicorn
from app.config.settings import Settings

if __name__ == "__main__":
    config = Settings()
    
    uvicorn.run(
       app="app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG_MODE,
        log_level=config.LOG_LEVEL.lower(),
        proxy_headers=config.PROXY_HEADERS,
        timeout_keep_alive=config.KEEP_ALIVE_TIMEOUT,
        reload_dirs=["app"]
    )