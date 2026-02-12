import logging

from fastapi import APIRouter, Depends, HTTPException, Query
import httpx

from app.dependencies import get_current_user
from app.schemas import LibraryItem, LibraryStats
from app.services.jellyfin_client import jellyfin_client

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/movies")
async def get_movies(
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    sort_by: str = Query("SortName"),
    sort_order: str = Query("Ascending"),
    user: dict = Depends(get_current_user),
):
    try:
        start_index = (page - 1) * limit
        data = await jellyfin_client.get_items(
            user_id=user["user_id"],
            token=user["jellyfin_token"],
            include_item_types="Movie",
            search_term=search,
            start_index=start_index,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        items = [
            LibraryItem(
                jellyfin_id=item["Id"],
                title=item.get("Name", ""),
                year=item.get("ProductionYear"),
                poster_url=jellyfin_client.get_image_url(item["Id"]),
                media_type="movie",
            )
            for item in data.get("Items", [])
        ]
        return {
            "items": items,
            "total": data.get("TotalRecordCount", 0),
            "page": page,
            "limit": limit,
        }
    except httpx.HTTPStatusError as e:
        logger.error("Jellyfin HTTP error (movies): %s", e.response.status_code)
        if e.response.status_code == 401:
            raise HTTPException(status_code=401, detail="Jellyfin session expired. Please log out and log back in.")
        raise HTTPException(status_code=502, detail=f"Jellyfin error: {e.response.status_code}")
    except Exception as e:
        logger.error("Jellyfin error (movies): %s", e)
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/tvshows")
async def get_tv_shows(
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    sort_by: str = Query("SortName"),
    sort_order: str = Query("Ascending"),
    user: dict = Depends(get_current_user),
):
    try:
        start_index = (page - 1) * limit
        data = await jellyfin_client.get_items(
            user_id=user["user_id"],
            token=user["jellyfin_token"],
            include_item_types="Series",
            search_term=search,
            start_index=start_index,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        items = [
            LibraryItem(
                jellyfin_id=item["Id"],
                title=item.get("Name", ""),
                year=item.get("ProductionYear"),
                poster_url=jellyfin_client.get_image_url(item["Id"]),
                media_type="tv",
            )
            for item in data.get("Items", [])
        ]
        return {
            "items": items,
            "total": data.get("TotalRecordCount", 0),
            "page": page,
            "limit": limit,
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(status_code=401, detail="Jellyfin session expired. Please log out and log back in.")
        raise HTTPException(status_code=502, detail="Jellyfin server error")
    except Exception as e:
        logger.error("Jellyfin error (tvshows): %s", e)
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/stats", response_model=LibraryStats)
async def get_library_stats(user: dict = Depends(get_current_user)):
    try:
        movies = await jellyfin_client.get_items(
            user["user_id"], user["jellyfin_token"],
            include_item_types="Movie", limit=0,
        )
        shows = await jellyfin_client.get_items(
            user["user_id"], user["jellyfin_token"],
            include_item_types="Series", limit=0,
        )
        episodes = await jellyfin_client.get_items(
            user["user_id"], user["jellyfin_token"],
            include_item_types="Episode", limit=0,
        )
        return LibraryStats(
            total_movies=movies.get("TotalRecordCount", 0),
            total_shows=shows.get("TotalRecordCount", 0),
            total_episodes=episodes.get("TotalRecordCount", 0),
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(status_code=401, detail="Jellyfin session expired. Please log out and log back in.")
        raise HTTPException(status_code=502, detail="Jellyfin server error")
    except Exception as e:
        logger.error("Jellyfin error (stats): %s", e)
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/recent")
async def get_recent(
    limit: int = Query(20, ge=1, le=50),
    user: dict = Depends(get_current_user),
):
    try:
        items = await jellyfin_client.get_latest_items(
            user["user_id"], user["jellyfin_token"], limit
        )
        return [
            LibraryItem(
                jellyfin_id=item["Id"],
                title=item.get("Name", ""),
                year=item.get("ProductionYear"),
                poster_url=jellyfin_client.get_image_url(item["Id"]),
                media_type="movie" if item.get("Type") == "Movie" else "tv",
            )
            for item in items
        ]
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(status_code=401, detail="Jellyfin session expired. Please log out and log back in.")
        raise HTTPException(status_code=502, detail="Jellyfin server error")
    except Exception as e:
        logger.error("Jellyfin error (recent): %s", e)
        raise HTTPException(status_code=502, detail=str(e))
