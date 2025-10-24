import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import React from 'react'
import App from '../../shell/App'

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    expect(true).toBe(true)
  })
})
