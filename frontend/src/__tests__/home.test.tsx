import { render, screen } from '@testing-library/react'
import Home from '@/app/page'

describe('Home', () => {
  it('renders welcome heading', () => {
    render(<Home />)
    expect(screen.getByText('Welcome to FinRack')).toBeInTheDocument()
  })
})


