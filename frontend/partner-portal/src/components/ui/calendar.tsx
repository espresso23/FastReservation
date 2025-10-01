import * as React from 'react'
import { ChevronDownIcon, Calendar as CalendarIcon } from 'lucide-react'
import { Button } from './button'
import { Label } from './label'
import { Popover, PopoverContent, PopoverTrigger } from './popover'
// @ts-ignore - types may not be present for our React version
import { DayPicker } from 'react-day-picker'
import 'react-day-picker/dist/style.css'

export function DatePicker({ id, label, value, onChange, className, trigger = 'button', ariaLabel, range = false }: { id?: string, label?: string, value?: Date | undefined, onChange?: (d: Date | undefined | { from?: Date, to?: Date })=>void, className?: string, trigger?: 'button'|'icon', ariaLabel?: string, range?: boolean }) {
  const [open, setOpen] = React.useState(false)
  const [date, setDate] = React.useState<Date | undefined>(value)
  const [rangeValue, setRangeValue] = React.useState<{from?: Date, to?: Date} | undefined>(undefined)

  React.useEffect(()=>{ setDate(value) }, [value])

  return (
    <div className={`flex flex-col gap-2 ${className||''}`}>
      {label && <Label htmlFor={id} className="px-1">{label}</Label>}
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          {trigger === 'icon' ? (
            <Button variant="outline" id={id} aria-label={ariaLabel || 'Chọn ngày'} className="w-10 h-10 p-0 inline-flex items-center justify-center">
              <CalendarIcon className="h-4 w-4" />
            </Button>
          ) : (
            <Button variant="outline" id={id} className="justify-between font-normal w-full h-10">
              {date ? date.toLocaleDateString() : 'Chọn ngày'}
              <ChevronDownIcon className="ml-2 h-4 w-4" />
            </Button>
          )}
        </PopoverTrigger>
        <PopoverContent className="w-auto p-2" align="start">
          {range ? (
            <DayPicker
              mode="range"
              selected={rangeValue}
              numberOfMonths={2}
              onSelect={(r:any)=>{
                setRangeValue(r)
                onChange && onChange(r)
              }}
              showOutsideDays
              fixedWeeks
            />
          ) : (
            <DayPicker
              mode="single"
              selected={date}
              onSelect={(d:any)=>{
                setDate(d)
                onChange && onChange(d)
                setOpen(false)
              }}
              showOutsideDays
              fixedWeeks
            />
          )}
        </PopoverContent>
      </Popover>
    </div>
  )
}


