import { useCallback, useState } from 'react'

export interface UseDrawerReturn<T = unknown> {
  /** Whether the drawer is open. */
  open: boolean
  /** The payload passed to openDrawer. Undefined when closed. */
  payload: T | undefined
  /** Open the drawer with an optional payload. */
  openDrawer: (payload?: T) => void
  /** Close the drawer. */
  closeDrawer: () => void
  /** Toggle the drawer. */
  toggleDrawer: (payload?: T) => void
}

/**
 * useDrawer — small state container for a single drawer.
 *
 * Keeps the open/closed state plus an optional typed payload so the
 * caller does not need to manage two pieces of state.
 *
 * Example:
 *   const drawer = useDrawer<{ id: string }>()
 *   <button onClick={() => drawer.openDrawer({ id: 'ev-42' })}>Details</button>
 *   <Drawer open={drawer.open} onClose={drawer.closeDrawer} title="Evidence">
 *     <pre>{drawer.payload?.id}</pre>
 *   </Drawer>
 */
export function useDrawer<T = unknown>(): UseDrawerReturn<T> {
  const [open, setOpen] = useState(false)
  const [payload, setPayload] = useState<T | undefined>(undefined)

  const openDrawer = useCallback((next?: T) => {
    setPayload(next)
    setOpen(true)
  }, [])

  const closeDrawer = useCallback(() => {
    setOpen(false)
  }, [])

  const toggleDrawer = useCallback((next?: T) => {
    setOpen((prev) => {
      if (!prev) setPayload(next)
      return !prev
    })
  }, [])

  return { open, payload, openDrawer, closeDrawer, toggleDrawer }
}
