import React, { createContext, useContext, useState, useRef, useEffect } from 'react'

type PopoverCtx = {
  open: boolean
  setOpen: (v: boolean) => void
}

const Ctx = createContext<PopoverCtx | null>(null)

export function Popover({ open: controlledOpen, onOpenChange, children }: { open?: boolean, onOpenChange?: (v: boolean)=>void, children: React.ReactNode }) {
  const [uncontrolled, setUncontrolled] = useState(false)
  const open = controlledOpen ?? uncontrolled
  const setOpen = (v: boolean) => {
    if (onOpenChange) onOpenChange(v)
    else setUncontrolled(v)
  }
  return (
    <Ctx.Provider value={{ open, setOpen }}>
      <div className="relative inline-block align-middle">{children}</div>
    </Ctx.Provider>
  )
}

export function PopoverTrigger({ asChild, children }: { asChild?: boolean, children: React.ReactElement }) {
  const ctx = useContext(Ctx)!
  const child = React.Children.only(children)
  const props = {
    onClick: (e: any) => { child.props.onClick?.(e); ctx.setOpen(!ctx.open) }
  }
  return asChild ? React.cloneElement(child, props) : <button {...props}>{child}</button>
}

export function PopoverContent({ className, align, children }: { className?: string, align?: 'start'|'center'|'end', children: React.ReactNode }) {
  const ctx = useContext(Ctx)!
  const ref = useRef<HTMLDivElement>(null)
  useEffect(()=>{
    function onDoc(e: MouseEvent) {
      if (!ref.current) return
      if (!ref.current.contains(e.target as Node)) ctx.setOpen(false)
    }
    if (ctx.open) document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [ctx.open])
  if (!ctx.open) return null
  return (
    <div
      ref={ref}
      className={`z-20 rounded-md border bg-white shadow-md ${className||''}`}
      style={{
        position: 'absolute',
        top: 'calc(100% + 8px)',
        left: align === 'end' ? 'auto' : 0,
        right: align === 'end' ? 0 : 'auto',
      }}
    >
      {children}
    </div>
  )
}


