import * as React from 'react'
import { ChevronDownIcon } from 'lucide-react'
import { Button } from './button'
import { Label } from './label'
import { Popover, PopoverContent, PopoverTrigger } from './popover'

export function DatePicker({ id, label, value, onChange, className }: { id?: string, label?: string, value?: Date | undefined, onChange?: (d: Date | undefined)=>void, className?: string }) {
  const [open, setOpen] = React.useState(false)
  const [date, setDate] = React.useState<Date | undefined>(value)

  React.useEffect(()=>{ setDate(value) }, [value])

  return (
    <div className={`flex flex-col gap-2 ${className||''}`}>
      {label && <Label htmlFor={id} className="px-1">{label}</Label>}
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" id={id} className="justify-between font-normal w-full h-10">
            {date ? date.toLocaleDateString() : 'Chọn ngày'}
            <ChevronDownIcon className="ml-2 h-4 w-4" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[260px] overflow-hidden p-3" align="start">
          <div className="">
            <input type="date" className="w-full border rounded px-2 py-2"
                   value={date ? new Date(date.getTime()-date.getTimezoneOffset()*60000).toISOString().slice(0,10) : ''}
                   onChange={(e)=>{
                     const d = e.target.value ? new Date(e.target.value+'T00:00:00') : undefined
                     setDate(d)
                     onChange && onChange(d)
                     setOpen(false)
                   }} />
          </div>
        </PopoverContent>
      </Popover>
    </div>
  )
}


