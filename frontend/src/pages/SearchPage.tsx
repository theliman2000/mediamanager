import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { searchMedia } from '../api/tmdb'
import { searchBooks } from '../api/books'
import { useDebounce } from '../hooks/useDebounce'
import SearchBar from '../components/SearchBar'
import MediaGrid from '../components/MediaGrid'

const FILTER_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'movie', label: 'Movies' },
  { value: 'tv', label: 'TV Shows' },
  { value: 'book', label: 'Books' },
] as const

type FilterValue = typeof FILTER_OPTIONS[number]['value']

function mapBookResults(results: any[]) {
  return results.map((b: any) => ({
    tmdb_id: b.ol_work_id,
    media_type: 'book',
    title: b.title,
    poster_path: b.cover_url || null,
    release_date: b.first_publish_year ? `${b.first_publish_year}` : null,
    vote_average: b.ratings_average ?? null,
    existing_request: b.existing_request ?? null,
    already_in_library: b.already_in_library ?? false,
  }))
}

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)
  const [filter, setFilter] = useState<FilterValue>('all')
  const debouncedQuery = useDebounce(query, 400)

  const tmdbType = filter === 'movie' || filter === 'tv' ? filter : undefined

  const { data: tmdbData, isLoading: tmdbLoading } = useQuery({
    queryKey: ['search', debouncedQuery, page, tmdbType],
    queryFn: () => searchMedia(debouncedQuery, page, tmdbType),
    enabled: debouncedQuery.length >= 2 && filter !== 'book',
  })

  const { data: bookData, isLoading: bookLoading } = useQuery({
    queryKey: ['search-books', debouncedQuery, page],
    queryFn: () => searchBooks(debouncedQuery, page),
    enabled: debouncedQuery.length >= 2 && (filter === 'book' || filter === 'all'),
  })

  const isLoading = filter === 'book'
    ? bookLoading
    : filter === 'all'
      ? tmdbLoading || bookLoading
      : tmdbLoading

  const data = (() => {
    if (filter === 'book') {
      return bookData
        ? { ...bookData, results: mapBookResults(bookData.results) }
        : undefined
    }
    if (filter === 'all' && tmdbData) {
      const mappedBooks = bookData ? mapBookResults(bookData.results) : []
      return {
        results: [...tmdbData.results, ...mappedBooks],
        page: tmdbData.page,
        total_pages: Math.max(tmdbData.total_pages, bookData?.total_pages ?? 1),
        total_results: tmdbData.total_results + (bookData?.total_results ?? 0),
      }
    }
    return tmdbData
  })()

  return (
    <div>
      <h2 className="text-2xl font-bold text-white mb-6">Search</h2>
      <SearchBar value={query} onChange={(v) => { setQuery(v); setPage(1) }} />

      <div className="flex gap-2 mt-4">
        {FILTER_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => { setFilter(opt.value); setPage(1) }}
            className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
              filter === opt.value
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <div className="mt-8">
        {isLoading && debouncedQuery.length >= 2 && (
          <p className="text-slate-400 text-center">Searching...</p>
        )}
        {data && (
          <>
            <p className="text-sm text-slate-400 mb-4">
              {data.total_results} result{data.total_results !== 1 ? 's' : ''}
            </p>
            <MediaGrid items={data.results} />
            {data.total_pages > 1 && (
              <div className="flex justify-center gap-4 mt-8">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 rounded text-sm text-white"
                >
                  Previous
                </button>
                <span className="text-slate-400 self-center text-sm">
                  Page {page} of {data.total_pages}
                </span>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page >= data.total_pages}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 rounded text-sm text-white"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
        {!isLoading && !data && debouncedQuery.length < 2 && (
          <p className="text-slate-500 text-center py-12">Type at least 2 characters to search</p>
        )}
      </div>
    </div>
  )
}
