"""
Grading router — grading scheme endpoints are served via /academics router.
This stub exists to prevent import errors if the module is referenced.
Use GET/POST /api/v1/grading-schemes (defined in app.academics.router).
"""
from fastapi import APIRouter

router = APIRouter(tags=["grading"])
# All grading scheme endpoints are in app/academics/router.py
