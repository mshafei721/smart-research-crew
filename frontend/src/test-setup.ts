import { beforeAll, afterEach, afterAll } from 'vitest'
import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom'

// Mock EventSource for SSE testing
global.EventSource = class EventSource {
  constructor(public url: string) {}
  close() {}
  addEventListener() {}
  removeEventListener() {}
} as any

beforeAll(() => {
  // Setup code that runs before all tests
})

afterEach(() => {
  // Cleanup after each test
  cleanup()
})

afterAll(() => {
  // Cleanup code that runs after all tests
})