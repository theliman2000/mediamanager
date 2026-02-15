import client from './client'

export async function searchBooks(query: string, page = 1) {
  const { data } = await client.get('/books/search', { params: { query, page } })
  return data
}

export async function getBookDetails(workId: number) {
  const { data } = await client.get(`/books/work/${workId}`)
  return data
}
