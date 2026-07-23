from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from app.routes.fraud import router

from app.routes.dashboard import router as dashboardRouter

app=FastAPI(
    title="AI Scam Shield"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(
    router,
    prefix="/api/fraud"
)

app.include_router(
    dashboardRouter,
    prefix="/api/dashboard"
)

@app.get("/")

def home():

    return{

        "application":"AI Scam Shield",

        "status":"Running"

    }