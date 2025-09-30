import { Link } from 'react-router-dom'
import type { Establishment } from '../types'

export default function EstablishmentCard({ item }: { item: Establishment }) {
  const thumbs = (item.imageUrlsGallery ?? []).slice(0, 5)
  return (
    <article className="border rounded-lg overflow-hidden grid grid-cols-[1fr,2fr]">
      <div className="relative">
        {item.imageUrlMain ? (
          <img src={item.imageUrlMain} alt={item.name} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full bg-slate-100" />
        )}
      </div>
      <div className="p-4 flex flex-col">
        <Link to={`/establishments/${item.id}`} className="text-lg font-semibold hover:underline">
          {item.name}
        </Link>
        <div className="text-sm text-slate-600 mt-1">{item.city}</div>
        {item.descriptionLong && (
          <div className="text-sm text-slate-700 mt-2 line-clamp-2">{item.descriptionLong}</div>
        )}
        {item.amenitiesList && item.amenitiesList.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {item.amenitiesList.slice(0, 6).map((a, i) => (
              <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-slate-100 border border-slate-200">
                {a}
              </span>
            ))}
          </div>
        )}
        <div className="flex gap-1 mt-3 overflow-hidden">
          {thumbs.map((u, idx) => (
            <img key={idx} src={u} className="w-16 h-16 object-cover rounded" />
          ))}
        </div>
        <div className="mt-auto flex justify-end">
          <Link to={`/establishments/${item.id}`} className="mt-3 px-4 py-2 rounded-md bg-slate-900 text-white hover:bg-slate-700">
            Xem chi tiết
          </Link>
        </div>
      </div>
    </article>
  )
}


