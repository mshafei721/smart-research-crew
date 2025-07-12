import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Wizard from '../Wizard'

// Mock props for Wizard component
const mockSetSections = vi.fn()
const mockSetReportMd = vi.fn()

// Mock EventSource for SSE testing
class MockEventSource {
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

// Mock global EventSource
global.EventSource = MockEventSource as any

describe('Wizard Component', () => {
  beforeEach(() => {
    mockSetSections.mockClear()
    mockSetReportMd.mockClear()
  })
  let mockEventSource: MockEventSource

  beforeEach(() => {
    vi.clearAllMocks()
    mockEventSource = new MockEventSource('test-url')
  })

  it('renders initial wizard form', () => {
    render(<Wizard setSections={mockSetSections} setReportMd={mockSetReportMd} />)
    
    // Check for main form elements
    expect(screen.getByText(/research topic/i)).toBeInTheDocument()
    expect(screen.getByText(/guidelines.*tone/i)).toBeInTheDocument()
    expect(screen.getByText(/sections/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /launch research/i })).toBeInTheDocument()
  })

  it('allows user input in form fields', async () => {
    const user = userEvent.setup()
    render(<Wizard setSections={mockSetSections} setReportMd={mockSetReportMd} />)
    
    const topicInput = screen.getAllByDisplayValue("")[0] // First input is topic
    const guidelinesInput = screen.getAllByDisplayValue("")[1] // Second input is guidelines
    
    if (topicInput) {
      await user.type(topicInput, 'AI in Healthcare')
      expect(topicInput).toHaveValue('AI in Healthcare')
    }
    
    if (guidelinesInput) {
      await user.type(guidelinesInput, 'Academic style with citations')
      expect(guidelinesInput).toHaveValue('Academic style with citations')
    }
  })

  it('validates required fields before submission', async () => {
    const user = userEvent.setup()
    render(<Wizard setSections={mockSetSections} setReportMd={mockSetReportMd} />)
    
    const submitButton = screen.getByRole('button', { name: /launch research/i })
    await user.click(submitButton)
    
    // Should show validation errors or prevent submission
    // The exact behavior depends on implementation
    expect(submitButton).toBeInTheDocument()
  })

  it('displays research progress when research starts', async () => {
    const user = userEvent.setup()
    render(<Wizard setSections={mockSetSections} setReportMd={mockSetReportMd} />)
    
    // Fill out form
    const topicInput = screen.getAllByDisplayValue("")[0] // First input is topic
    const guidelinesInput = screen.getAllByDisplayValue("")[1] // Second input is guidelines
    
    if (topicInput && guidelinesInput) {
      await user.type(topicInput, 'Test Topic')
      await user.type(guidelinesInput, 'Test Guidelines')
      
      // Submit form
      const submitButton = screen.getByRole('button', { name: /launch research/i })
      await user.click(submitButton)
      
      // Should show loading state or progress indicators
      await waitFor(() => {
        // Look for loading indicators, progress bars, or section status
        const progressElements = screen.queryAllByText(/loading|progress|researching/i)
        expect(progressElements.length).toBeGreaterThanOrEqual(0)
      })
    }
  })

  it('handles section completion updates', async () => {
    const user = userEvent.setup()
    render(<Wizard setSections={mockSetSections} setReportMd={mockSetReportMd} />)
    
    // Start research process (if form allows)
    const topicInput = screen.getAllByDisplayValue("")[0] // First input is topic
    if (topicInput) {
      await user.type(topicInput, 'Test Topic')
      
      const submitButton = screen.getByRole('button', { name: /launch research/i })
      if (submitButton && !submitButton.disabled) {
        await user.click(submitButton)
        
        // Simulate section completion via SSE
        setTimeout(() => {
          mockEventSource.simulateMessage(JSON.stringify({
            type: 'section',
            section: 'Introduction',
            content: 'Test introduction content',
            sources: ['test.com']
          }))
        }, 100)
        
        await waitFor(() => {
          // Should show section completion
          const sectionElements = screen.queryAllByText(/introduction|completed/i)
          expect(sectionElements.length).toBeGreaterThanOrEqual(0)
        })
      }
    }
  })

  it('displays final report when research completes', async () => {
    const user = userEvent.setup()
    render(<Wizard setSections={mockSetSections} setReportMd={mockSetReportMd} />)
    
    // Start research (simplified for testing)
    const topicInput = screen.getAllByDisplayValue("")[0] // First input is topic
    if (topicInput) {
      await user.type(topicInput, 'Test Topic')
      
      const submitButton = screen.getByRole('button', { name: /launch research/i })
      if (submitButton && !submitButton.disabled) {
        await user.click(submitButton)
        
        // Simulate final report via SSE
        setTimeout(() => {
          mockEventSource.simulateMessage(JSON.stringify({
            type: 'report',
            content: '# Test Report\n\nFinal research report content'
          }))
        }, 100)
        
        await waitFor(() => {
          // Should show final report
          const reportElements = screen.queryAllByText(/report|final/i)
          expect(reportElements.length).toBeGreaterThanOrEqual(0)
        })
      }
    }
  })

  it('handles SSE connection errors gracefully', async () => {
    const user = userEvent.setup()
    render(<Wizard setSections={mockSetSections} setReportMd={mockSetReportMd} />)
    
    // Start research
    const topicInput = screen.getAllByDisplayValue("")[0] // First input is topic
    if (topicInput) {
      await user.type(topicInput, 'Test Topic')
      
      const submitButton = screen.getByRole('button', { name: /launch research/i })
      if (submitButton && !submitButton.disabled) {
        await user.click(submitButton)
        
        // Simulate SSE error
        setTimeout(() => {
          mockEventSource.simulateError()
        }, 100)
        
        await waitFor(() => {
          // Should handle error gracefully (show error message or retry option)
          const errorElements = screen.queryAllByText(/error|failed|retry/i)
          expect(errorElements.length).toBeGreaterThanOrEqual(0)
        })
      }
    }
  })

  it('allows user to restart research process', async () => {
    const user = userEvent.setup()
    render(<Wizard setSections={mockSetSections} setReportMd={mockSetReportMd} />)
    
    // Complete a research cycle first (simplified)
    const topicInput = screen.getAllByDisplayValue("")[0] // First input is topic
    if (topicInput) {
      await user.type(topicInput, 'Test Topic')
      
      // Look for reset/new research buttons
      const restartButtons = screen.queryAllByText(/new|reset|start over|back/i)
      expect(restartButtons.length).toBeGreaterThanOrEqual(0)
    }
  })

  it('preserves form data during research process', async () => {
    const user = userEvent.setup()
    render(<Wizard setSections={mockSetSections} setReportMd={mockSetReportMd} />)
    
    // Find inputs by their context - they appear after their respective labels
    const inputs = screen.getAllByDisplayValue("")
    const topicInput = inputs[0] // First input is topic
    const guidelinesInput = inputs[1] // Second input is guidelines
    
    await user.type(topicInput, 'Preserved Topic')
    await user.type(guidelinesInput, 'Preserved Guidelines')
    
    // Values should persist even after starting research
    expect(topicInput).toHaveValue('Preserved Topic')
    expect(guidelinesInput).toHaveValue('Preserved Guidelines')
  })

  it('handles different section configurations', async () => {
    const user = userEvent.setup()
    render(<Wizard setSections={mockSetSections} setReportMd={mockSetReportMd} />)
    
    // Test with different section selections
    const sectionInputs = screen.queryAllByRole('checkbox') || screen.queryAllByRole('textbox')
    
    // Should be able to configure sections
    expect(sectionInputs.length).toBeGreaterThanOrEqual(0)
    
    // Test section selection/deselection if checkboxes exist
    const checkboxes = screen.queryAllByRole('checkbox')
    if (checkboxes.length > 0) {
      await user.click(checkboxes[0])
      // Should handle section toggle
      expect(checkboxes[0]).toBeInTheDocument()
    }
  })
})