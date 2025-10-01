import { Link } from 'react-router-dom'
import type { Establishment } from '../types'

export default function EstablishmentCard({ item }: { item: Establishment }) {
  const thumbs = (item.imageUrlsGallery ?? []).slice(0, 3)
  return (
    <article className="group border rounded-xl overflow-hidden card bg-white/90 backdrop-blur flex flex-col relative">
      <div className="relative w-full h-48 bg-slate-100 overflow-hidden">
        {item.imageUrlMain ? (
          <img src={item.imageUrlMain} alt={item.name} className="w-full h-full object-cover" />
        ) : null}
        {/* Large preview on hover with scroll */}
        {item.imageUrlMain && (
          <div className="absolute z-30 hidden group-hover:block left-full ml-2 top-0 w-96 h-64 bg-white shadow-xl rounded overflow-auto">
            <img src={item.imageUrlMain} alt={item.name} className="w-full h-auto object-contain" />
          </div>
        )}
      </div>
      <div className="p-4 flex-1 flex flex-col">
        <Link to={`/establishments/${item.id}`} className="text-base font-semibold hover:underline">
          {item.name}
        </Link>
        <div className="text-sm text-slate-600 mt-1">{item.city || '-'}</div>
        {item.amenitiesList && item.amenitiesList.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {item.amenitiesList.slice(0, 6).map((a, i) => (
              <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-slate-100 border border-slate-200 chip">
                {a}
              </span>
            ))}
          </div>
        )}
        {thumbs.length>0 && (
          <div className="flex gap-1 mt-3 overflow-hidden">
            {thumbs.map((u, idx) => (
              <div key={idx} className="relative group/thumb rounded overflow-hidden w-14 h-14">
                <img src={u} className="w-full h-full object-cover" />
                <div className="absolute z-30 hidden group-hover/thumb:block left-full ml-2 top-0 w-80 h-56 bg-white shadow-xl rounded overflow-auto">
                  <img src={u} className="w-full h-auto object-contain" />
                </div>
              </div>
            ))}
          </div>
        )}
        <div className="mt-auto flex justify-end">
          <Link to={`/establishments/${item.id}`} className="mt-3 px-3 py-1.5 rounded-md border hover:bg-slate-900 hover:text-white transition">
            Xem chi tiết
          </Link>
        </div>
      </div>
    </article>
  )
}


