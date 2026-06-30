"""Debug FastAPI router inclusion."""
from fastapi import FastAPI, APIRouter

router = APIRouter(prefix="/test")


@router.get("/hello")
async def hello():
    return {"msg": "hello"}


app = FastAPI()

print("Before include_router:")
print(f"  app.routes count: {len(app.routes)}")

app.include_router(router)

print("After include_router:")
print(f"  app.routes count: {len(app.routes)}")
for r in app.routes:
    name = type(r).__name__
    path = getattr(r, "path", "N/A")
    print(f"    {name}: path={path}")
