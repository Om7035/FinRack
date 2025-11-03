'use client'

import { useMemo, useState, useEffect, useRef } from 'react'
import { ColumnDef, flexRender, getCoreRowModel, getFilteredRowModel, getPaginationRowModel, getSortedRowModel, SortingState, useReactTable } from '@tanstack/react-table'
import { useVirtualizer } from '@tanstack/react-virtual'
import api from '@/lib/api'

type Tx = { id: string; date: string; merchant: string; amount: number; category: string };

export default function TransactionsPage() {
  const [data, setData] = useState<Tx[]>([])
  const [globalFilter, setGlobalFilter] = useState('')
  const [sorting, setSorting] = useState<SortingState>([])
  const [selected, setSelected] = useState<Tx | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get('/api/transactions')
        setData(res.data || [])
      } catch {
        setData([])
      }
    }
    load()
  }, [])

  const columns = useMemo<ColumnDef<Tx>[]>(() => [
    { accessorKey: 'date', header: 'Date', cell: (info) => new Date(info.getValue<string>()).toLocaleDateString() },
    { accessorKey: 'merchant', header: 'Merchant' },
    { accessorKey: 'category', header: 'Category' },
    { accessorKey: 'amount', header: 'Amount', cell: (info) => {
      const v = info.getValue<number>()
      return <span className={v < 0 ? 'text-red-500' : 'text-green-600'}>{v < 0 ? '-' : '+'}${Math.abs(v).toFixed(2)}</span>
    }},
  ], [])

  const table = useReactTable({
    data,
    columns,
    state: { globalFilter, sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  })

  const tableContainerRef = useRef<HTMLDivElement | null>(null)
  const rowVirtualizer = useVirtualizer({
    count: table.getRowModel().rows.length,
    getScrollElement: () => tableContainerRef.current,
    estimateSize: () => 44,
    overscan: 10,
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <input
          value={globalFilter ?? ''}
          onChange={(e) => setGlobalFilter(e.target.value)}
          placeholder="Search transactions..."
          className="w-full md:max-w-xs rounded-md border px-3 py-2 text-sm"
        />
      </div>

      <div className="overflow-x-auto rounded-lg border" ref={tableContainerRef} style={{ maxHeight: 480, overflow: 'auto' }}>
        <table className="w-full text-sm" style={{ position: 'relative' }}>
          <thead className="bg-muted/50">
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map(header => (
                  <th key={header.id} className="text-left px-3 py-2 font-medium">
                    {header.isPlaceholder ? null : (
                      <button onClick={header.column.getToggleSortingHandler()} className="hover:underline">
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {{ asc: ' ▲', desc: ' ▼' }[header.column.getIsSorted() as string] ?? null}
                      </button>
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            <tr>
              <td colSpan={columns.length} style={{ height: rowVirtualizer.getTotalSize() }}>
                <div style={{ position: 'relative' }}>
                  {rowVirtualizer.getVirtualItems().map(v => {
                    const row = table.getRowModel().rows[v.index]
                    return (
                      <div key={row.id} style={{ position: 'absolute', top: 0, left: 0, width: '100%', transform: `translateY(${v.start}px)` }}>
                        <table className="w-full text-sm">
                          <tbody>
                            <tr className="border-t hover:bg-accent/40 cursor-pointer" onClick={() => setSelected(row.original)}>
                              {row.getVisibleCells().map(cell => (
                                <td key={cell.id} className="px-3 py-2">
                                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                </td>
                              ))}
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    )
                  })}
                </div>
              </td>
            </tr>
            {table.getRowModel().rows.length === 0 && (
              <tr>
                <td colSpan={columns.length} className="px-3 py-6 text-center text-muted-foreground">No transactions</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-end gap-2">
        <button onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()} className="rounded-md border px-3 py-1 text-sm disabled:opacity-50">Previous</button>
        <button onClick={() => table.nextPage()} disabled={!table.getCanNextPage()} className="rounded-md border px-3 py-1 text-sm disabled:opacity-50">Next</button>
      </div>

      {selected && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4" onClick={() => setSelected(null)}>
          <div className="w-full max-w-md rounded-lg border bg-background p-4" onClick={(e) => e.stopPropagation()}>
            <div className="mb-2 text-sm font-medium">Transaction Details</div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between"><span className="text-muted-foreground">Merchant</span><span>{selected.merchant}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Category</span><span>{selected.category}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Date</span><span>{new Date(selected.date).toLocaleString()}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Amount</span><span className={selected.amount < 0 ? 'text-red-500' : 'text-green-600'}>{selected.amount < 0 ? '-' : '+'}${Math.abs(selected.amount).toFixed(2)}</span></div>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button className="rounded-md border px-3 py-1.5 text-sm" onClick={() => setSelected(null)}>Close</button>
              <button className="rounded-md bg-primary text-primary-foreground px-3 py-1.5 text-sm">Mark Reviewed</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


