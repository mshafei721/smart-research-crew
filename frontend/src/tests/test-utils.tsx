import { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { vi } from 'vitest'

// Mock EventSource for SSE testing across all tests
export class MockEventSource {
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  readyState: number = 0
  url: string
  
  constructor(url: string) {
    this.url = url
    this.readyState = 1 // OPEN
    // Simulate connection opened
    setTimeout(() => {
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 0)
  }
  
  close() {
    this.readyState = 2 // CLOSED
  }
  
  // Helper method to simulate receiving messages
  simulateMessage(data: string) {
    if (this.onmessage) {
      const event = new MessageEvent('message', { data })
      this.onmessage(event)
    }
  }
  
  // Helper method to simulate errors
  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'))
    }
  }
}

// Setup global mocks
export const setupGlobalMocks = () => {
  // Mock EventSource
  global.EventSource = MockEventSource as any

  // Mock clipboard API
  Object.assign(navigator, {
    clipboard: {
      writeText: vi.fn(() => Promise.resolve()),
      readText: vi.fn(() => Promise.resolve('mocked clipboard content')),
    },
  })

  // Mock window.matchMedia for responsive design tests
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(), // Deprecated
      removeListener: vi.fn(), // Deprecated
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  })

  // Mock console methods to avoid noise in tests
  const originalError = console.error
  console.error = vi.fn((...args) => {
    // Only suppress React warnings in tests
    if (args[0]?.includes?.('Warning:')) {
      return
    }
    originalError(...args)
  })

  return {
    cleanup: () => {
      console.error = originalError
    }
  }
}

// Custom render function with common providers
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  // Could add providers here if needed (Router, Theme, etc.)
  return render(ui, options)
}

// Test data factories
export const createMockSectionData = (section: string = 'Introduction') => ({
  type: 'section',
  section,
  content: `This is mock content for the ${section} section.`,
  sources: [`https://example.com/${section.toLowerCase()}`, `https://source.org/${section}`]
})

export const createMockReportData = () => ({
  type: 'report',
  content: `# Mock Research Report

## Table of Contents
1. Introduction
2. Methodology
3. Results
4. Conclusion

## 1. Introduction
This is a mock introduction section.

## 2. Methodology
This describes the mock methodology.

## 3. Results
These are the mock results.

## 4. Conclusion
This is the mock conclusion.

## References
[1] Example Source 1
[2] Example Source 2
`
})

// Helper to simulate SSE events
export const simulateSSEEvents = (mockEventSource: MockEventSource, sections: string[] = ['Introduction', 'Conclusion']) => {
  return new Promise<void>((resolve) => {
    let eventCount = 0
    const totalEvents = sections.length + 1 // sections + final report

    const sendNextEvent = () => {
      if (eventCount < sections.length) {
        // Send section events
        const sectionData = createMockSectionData(sections[eventCount])
        mockEventSource.simulateMessage(JSON.stringify(sectionData))
        eventCount++
        setTimeout(sendNextEvent, 100)
      } else if (eventCount === sections.length) {
        // Send final report
        const reportData = createMockReportData()
        mockEventSource.simulateMessage(JSON.stringify(reportData))
        eventCount++
        setTimeout(() => resolve(), 100)
      }
    }

    setTimeout(sendNextEvent, 50)
  })
}

// Helper to wait for async operations
export const waitForAsync = (ms: number = 100) => {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// Re-export everything from testing-library
export * from '@testing-library/react'
export { customRender as render }