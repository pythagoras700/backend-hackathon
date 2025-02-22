from fastapi import FastAPI
import uvicorn
from _elements import api_router

main_route = FastAPI()


@main_route.get("/")
async def root():
    return {"message": "Hackathon API Service"}

main_route.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run(main_route, host="0.0.0.0", port=8000)
