import { useParams } from 'react-router-dom'

export default function DocumentView() {
  const { id } = useParams()

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Document: {id}</h1>
      <p className="mt-2 text-gray-500">
        Document detail view — extracted text, entities, and metadata will appear here.
      </p>
    </div>
  )
}
