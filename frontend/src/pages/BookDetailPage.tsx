import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getBookDetails } from '../api/books'
import { createRequest } from '../api/requests'
import RequestBadge from '../components/RequestBadge'
import Spinner from '../components/Spinner'

export default function BookDetailPage() {
  const { workId } = useParams()
  const queryClient = useQueryClient()
  const id = Number(workId)

  const { data, isLoading, error } = useQuery({
    queryKey: ['book', id],
    queryFn: () => getBookDetails(id),
  })

  const requestMutation = useMutation({
    mutationFn: () =>
      createRequest({
        tmdb_id: id,
        media_type: 'book',
        title: data?.title || '',
        poster_path: data?.cover_url,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['book', id] })
    },
  })

  if (isLoading) return <Spinner />
  if (error || !data) return <p className="text-red-400">Failed to load book details.</p>

  const canRequest = !data.existing_request && !data.already_in_library

  return (
    <div>
      <div className="flex flex-col md:flex-row gap-6 md:gap-8">
        {/* Cover */}
        <div className="flex-shrink-0 w-40 mx-auto md:w-56 md:mx-0">
          {data.cover_url ? (
            <img src={data.cover_url} alt={data.title} className="w-full rounded-lg shadow-lg" />
          ) : (
            <div className="w-full aspect-[2/3] bg-slate-700 rounded-lg flex items-center justify-center text-slate-400">
              No Cover
            </div>
          )}
        </div>

        {/* Details */}
        <div className="flex-1">
          <h1 className="text-2xl md:text-3xl font-bold text-white">
            {data.title}{' '}
            {data.first_publish_year && (
              <span className="text-slate-400 font-normal">({data.first_publish_year})</span>
            )}
          </h1>

          {data.authors && data.authors.length > 0 && (
            <p className="text-slate-300 mt-2">by {data.authors.join(', ')}</p>
          )}

          <div className="flex flex-wrap items-center gap-3 mt-3">
            {data.subjects?.map((s: string) => (
              <span key={s} className="text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded">
                {s}
              </span>
            ))}
            {data.page_count && (
              <span className="text-sm text-slate-400">{data.page_count} pages</span>
            )}
            {data.edition_count && (
              <span className="text-sm text-slate-400">
                {data.edition_count} edition{data.edition_count !== 1 ? 's' : ''}
              </span>
            )}
            {data.ratings_average != null && data.ratings_average > 0 && (
              <span className="text-sm text-yellow-400">
                {data.ratings_average.toFixed(1)} / 5
              </span>
            )}
          </div>

          {data.description && (
            <p className="mt-4 text-slate-300 leading-relaxed">{data.description}</p>
          )}

          {/* Action buttons */}
          <div className="mt-6 flex items-center gap-4">
            {data.existing_request && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-400">Request status:</span>
                <RequestBadge status={data.existing_request} />
              </div>
            )}
            {canRequest && (
              <button
                onClick={() => requestMutation.mutate()}
                disabled={requestMutation.isPending}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white px-6 py-2 rounded-lg font-medium transition-colors"
              >
                {requestMutation.isPending ? 'Requesting...' : 'Request'}
              </button>
            )}
            {requestMutation.isError && (
              <span className="text-red-400 text-sm">
                {(requestMutation.error as any)?.response?.data?.detail || 'Failed to submit request'}
              </span>
            )}
            {requestMutation.isSuccess && (
              <span className="text-green-400 text-sm">Request submitted!</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
