import httpx


OPENLIBRARY_BASE = "https://openlibrary.org"
COVER_BASE = "https://covers.openlibrary.org/b/id"


def cover_url(cover_id: int | None, size: str = "M") -> str | None:
    if not cover_id:
        return None
    return f"{COVER_BASE}/{cover_id}-{size}.jpg"


def parse_work_id(key: str) -> int:
    """Extract numeric ID from an Open Library work key like '/works/OL27448W'."""
    return int(key.split("/")[-1].removeprefix("OL").removesuffix("W"))


def format_work_key(work_id: int) -> str:
    return f"OL{work_id}W"


class OpenLibraryClient:
    async def search_books(self, query: str, page: int = 1, limit: int = 20) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{OPENLIBRARY_BASE}/search.json",
                params={
                    "q": query,
                    "page": page,
                    "limit": limit,
                    "fields": "key,title,author_name,first_publish_year,cover_i,number_of_pages_median,subject,edition_count,ratings_average",
                },
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_work_details(self, work_key: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{OPENLIBRARY_BASE}/works/{work_key}.json",
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_author(self, author_key: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{OPENLIBRARY_BASE}/authors/{author_key}.json",
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()


openlibrary_client = OpenLibraryClient()
