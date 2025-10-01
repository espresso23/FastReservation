import { Link } from 'react-router-dom'
import type { Establishment } from '../types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Button } from './ui/button'
import { MapPin, Eye } from 'lucide-react'

export default function EstablishmentCard({ item }: { item: Establishment }) {
  const thumbs = (item.imageUrlsGallery ?? []).slice(0, 3)
  return (
    <Card className="group overflow-hidden hover:shadow-lg transition-all duration-300 hover-lift">
      <div className="relative w-full h-48 bg-slate-100 overflow-hidden">
        {item.imageUrlMain ? (
          <img 
            src={item.imageUrlMain} 
            alt={item.name} 
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" 
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-slate-200 to-slate-300 flex items-center justify-center">
            <span className="text-slate-500 text-sm">Chưa có ảnh</span>
          </div>
        )}
        {/* Large preview on hover */}
        {item.imageUrlMain && (
          <div className="absolute z-30 hidden group-hover:block left-full ml-2 top-0 w-96 h-64 bg-white shadow-xl rounded-lg overflow-hidden border">
            <img src={item.imageUrlMain} alt={item.name} className="w-full h-auto object-contain" />
          </div>
        )}
      </div>
      
      <CardHeader className="pb-3">
        <CardTitle className="text-lg line-clamp-2">
          <Link to={`/establishments/${item.id}`} className="hover:text-blue-600 transition-colors">
            {item.name}
          </Link>
        </CardTitle>
        <CardDescription className="flex items-center gap-1">
          <MapPin className="w-4 h-4" />
          {item.city || 'Chưa có địa chỉ'}
        </CardDescription>
      </CardHeader>
      
      <CardContent className="pt-0">
        {item.amenities && item.amenities.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-4">
            {item.amenities.slice(0, 4).map((amenity: string, i: number) => (
              <Badge key={i} variant="secondary" className="text-xs">
                {amenity}
              </Badge>
            ))}
            {item.amenities.length > 4 && (
              <Badge variant="outline" className="text-xs">
                +{item.amenities.length - 4} khác
              </Badge>
            )}
          </div>
        )}
        
        {thumbs.length > 0 && (
          <div className="flex gap-2 mb-4 overflow-hidden">
            {thumbs.map((url, idx) => (
              <div key={idx} className="relative group/thumb rounded-md overflow-hidden w-12 h-12 flex-shrink-0">
                <img src={url} className="w-full h-full object-cover" />
                <div className="absolute z-30 hidden group-hover/thumb:block left-full ml-2 top-0 w-80 h-56 bg-white shadow-xl rounded-lg overflow-hidden border">
                  <img src={url} className="w-full h-auto object-contain" />
                </div>
              </div>
            ))}
          </div>
        )}
        
        <Button asChild className="w-full">
          <Link to={`/establishments/${item.id}`}>
            <Eye className="w-4 h-4 mr-2" />
            Xem chi tiết
          </Link>
        </Button>
      </CardContent>
    </Card>
  )
}


