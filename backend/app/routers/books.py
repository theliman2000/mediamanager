from fastapi import APIRouter, Depends, HTTPException, Query
import httpx
import logging

from app.dependencies import get_current_user
from app.schemas import BookSearchResult, BookDetail
from app.services.openlibrary_client import (
    openlibrary_client,
    cover_url,
    parse_work_id,
    format_work_key,
)
from app.services.request_service import get_request_for_tmdb
from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/search")
async def search_books(
    query: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    try:
        data = await openlibrary_client.search_books(query, page)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Open Library API error")

    results = []
    for doc in data.get("docs", []):
        key = doc.get("key", "")
        if not key:
            continue
        try:
            work_id = parse_work_id(key)
        except (ValueError, IndexError):
            continue

        existing_request = get_request_for_tmdb(db, work_id, "book", user["user_id"])

        results.append(BookSearchResult(
            ol_work_id=work_id,
            ol_work_key=format_work_key(work_id),
            media_type="book",
            title=doc.get("title", ""),
            authors=doc.get("author_name", []),
            first_publish_year=doc.get("first_publish_year"),
            cover_url=cover_url(doc.get("cover_i"), "M"),
            subject=(doc.get("subject") or [])[:5],
            edition_count=doc.get("edition_count"),
            ratings_average=doc.get("ratings_average"),
            existing_request=existing_request,
        ))

    num_found = data.get("numFound", 0)
    total_pages = max(1, -(-num_found // 20))  # ceil division

    return {
        "results": results,
        "page": page,
        "total_pages": total_pages,
        "total_results": num_found,
    }


@router.get("/work/{work_id}")
async def get_book_detail(
    work_id: int,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    work_key = format_work_key(work_id)
    try:
        data = await openlibrary_client.get_work_details(work_key)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Book not found")
        raise HTTPException(status_code=502, detail="Open Library API error")
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Open Library API error")

    # Extract description
    description = data.get("description")
    if isinstance(description, dict):
        description = description.get("value", "")

    # Build cover URL from covers array or fall back
    covers = data.get("covers", [])
    book_cover_url = cover_url(covers[0], "L") if covers else None

    # Extract subjects
    subjects = [s for s in data.get("subjects", []) if isinstance(s, str)][:15]

    existing_request = get_request_for_tmdb(db, work_id, "book", user["user_id"])

    return BookDetail(
        ol_work_id=work_id,
        ol_work_key=work_key,
        title=data.get("title", ""),
        authors=[
            a.get("author", {}).get("key", "").split("/")[-1]
            if isinstance(a.get("author"), dict)
            else str(a.get("author", ""))
            for a in data.get("authors", [])
        ],
        description=description,
        first_publish_year=None,
        cover_url=book_cover_url,
        subjects=subjects,
        page_count=None,
        edition_count=None,
        ratings_average=None,
        existing_request=existing_request,
    )
