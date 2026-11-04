from fastapi import FastAPI
from app.api import rosreestr, converter, nspd

app = FastAPI(
    title="TerraData API",
    description="API for Rosreestr and NSPD data extraction and XML to PDF conversion",
    version="1.0.0"
)

# Include routers
app.include_router(rosreestr.router)
app.include_router(converter.router)
app.include_router(nspd.router)

@app.get("/")
async def root():

    return {
        "message": "Welcome to TerraData API",
        "docs": "/docs",
        "endpoints": {
            "rosreestr": "/rosreestr",
            "converter": "/converter",
            "nspd": "/nspd"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
