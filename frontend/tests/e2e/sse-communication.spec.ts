import { test, expect } from '@playwright/test';

/**
 * End-to-end tests for Server-Sent Events (SSE) communication.
 * 
 * These tests validate the real-time communication between frontend and backend
 * through SSE streams, including connection management and event handling.
 */
test.describe('SSE Communication', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('SSE connection lifecycle', async ({ page }) => {
    await test.step('Establish SSE connection', async () => {
      // Monitor network requests for SSE connection
      const sseRequestPromise = page.waitForRequest(request => 
        request.url().includes('/sse') && request.method() === 'GET'
      );
      
      // Fill form and start research
      await page.fill('[data-testid="topic-input"]', 'SSE Test Topic');
      await page.fill('[data-testid="guidelines-input"]', 'Test SSE communication');
      await page.fill('[data-testid="sections-input"]', 'Introduction');
      await page.click('[data-testid="start-research-button"]');
      
      // Verify SSE request was made
      const sseRequest = await sseRequestPromise;
      expect(sseRequest.url()).toContain('topic=SSE%20Test%20Topic');
      expect(sseRequest.headers()['accept']).toBe('text/event-stream');
      expect(sseRequest.headers()['cache-control']).toBe('no-cache');
    });

    await test.step('Handle SSE connection states', async () => {
      // Wait for connection status to show connected
      await expect(page.locator('[data-testid="sse-status"]')).toContainText('Connected');
      
      // Verify connection indicator is visible
      await expect(page.locator('[data-testid="connection-indicator"]')).toHaveClass(/connected/);
    });

    await test.step('Receive and process SSE events', async () => {
      // Wait for first section event
      await expect(page.locator('[data-testid="section-introduction"]')).toBeVisible({ timeout: 30000 });
      
      // Verify section content was received and processed
      const sectionContent = page.locator('[data-testid="section-introduction"] .content');
      await expect(sectionContent).not.toBeEmpty();
      
      // Check for sources in section
      const sources = page.locator('[data-testid="section-introduction"] .sources');
      await expect(sources).toBeVisible();
    });

    await test.step('Handle SSE connection completion', async () => {
      // Wait for final report event
      await expect(page.locator('[data-testid="final-report"]')).toBeVisible({ timeout: 60000 });
      
      // Verify connection status shows completed
      await expect(page.locator('[data-testid="sse-status"]')).toContainText('Completed');
      
      // Verify connection indicator shows success
      await expect(page.locator('[data-testid="connection-indicator"]')).toHaveClass(/completed/);
    });
  });

  test('SSE error handling and reconnection', async ({ page }) => {
    await test.step('Handle SSE connection errors', async () => {
      // Intercept SSE requests and fail them initially
      let requestCount = 0;
      await page.route('**/sse*', route => {
        requestCount++;
        if (requestCount === 1) {
          // Fail first request
          route.abort('failed');
        } else {
          // Allow subsequent requests
          route.continue();
        }
      });
      
      await page.fill('[data-testid="topic-input"]', 'Error Test');
      await page.fill('[data-testid="guidelines-input"]', 'Test error handling');
      await page.fill('[data-testid="sections-input"]', 'Introduction');
      await page.click('[data-testid="start-research-button"]');
      
      // Should show error state
      await expect(page.locator('[data-testid="sse-error"]')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('[data-testid="connection-indicator"]')).toHaveClass(/error/);
    });

    await test.step('Test reconnection mechanism', async () => {
      // Click retry button if available
      const retryButton = page.locator('[data-testid="retry-connection-button"]');
      if (await retryButton.isVisible()) {
        await retryButton.click();
        
        // Should attempt reconnection
        await expect(page.locator('[data-testid="sse-status"]')).toContainText('Reconnecting');
        
        // Should eventually succeed (since we only fail first request)
        await expect(page.locator('[data-testid="sse-status"]')).toContainText('Connected', { timeout: 15000 });
      }
    });
  });

  test('SSE event types and processing', async ({ page }) => {
    // Use page evaluation to capture SSE events
    const events: any[] = [];
    
    await page.addInitScript(() => {
      window.addEventListener('sse-event-received', (event: any) => {
        (window as any).capturedSSEEvents = (window as any).capturedSSEEvents || [];
        (window as any).capturedSSEEvents.push(event.detail);
      });
    });
    
    await test.step('Process section events', async () => {
      await page.fill('[data-testid="topic-input"]', 'Event Processing Test');
      await page.fill('[data-testid="guidelines-input"]', 'Test event types');
      await page.fill('[data-testid="sections-input"]', 'Introduction,Methods,Results');
      await page.click('[data-testid="start-research-button"]');
      
      // Wait for multiple sections to be processed
      await expect(page.locator('[data-testid="section-introduction"]')).toBeVisible();
      await expect(page.locator('[data-testid="section-methods"]')).toBeVisible();
      await expect(page.locator('[data-testid="section-results"]')).toBeVisible();
      
      // Verify event processing in UI
      const sections = ['introduction', 'methods', 'results'];
      for (const section of sections) {
        const sectionElement = page.locator(`[data-testid="section-${section}"]`);
        await expect(sectionElement).toHaveAttribute('data-status', 'completed');
      }
    });

    await test.step('Process report event', async () => {
      await expect(page.locator('[data-testid="final-report"]')).toBeVisible({ timeout: 90000 });
      
      // Verify report structure
      const reportContent = page.locator('[data-testid="final-report"] .report-content');
      await expect(reportContent).toContainText('Table of Contents');
      await expect(reportContent).toContainText('References');
      
      // Check that all sections are included in final report
      await expect(reportContent).toContainText('Introduction');
      await expect(reportContent).toContainText('Methods');
      await expect(reportContent).toContainText('Results');
    });

    await test.step('Validate captured events', async () => {
      // Get captured events from page
      const capturedEvents = await page.evaluate(() => (window as any).capturedSSEEvents || []);
      
      // Should have received multiple events
      expect(capturedEvents.length).toBeGreaterThan(0);
      
      // Should have section events
      const sectionEvents = capturedEvents.filter((e: any) => e.type === 'section');
      expect(sectionEvents.length).toBe(3);
      
      // Should have report event
      const reportEvents = capturedEvents.filter((e: any) => e.type === 'report');
      expect(reportEvents.length).toBe(1);
      
      // Events should have required fields
      sectionEvents.forEach((event: any) => {
        expect(event).toHaveProperty('section');
        expect(event).toHaveProperty('content');
        expect(event).toHaveProperty('sources');
      });
      
      reportEvents.forEach((event: any) => {
        expect(event).toHaveProperty('content');
        expect(event.content).toContain('# '); // Should be markdown
      });
    });
  });

  test('SSE performance and reliability', async ({ page }) => {
    await test.step('Measure SSE latency', async () => {
      let firstEventTime: number = 0;
      
      // Capture timing of first SSE event
      await page.addInitScript(() => {
        window.addEventListener('sse-event-received', (event: any) => {
          if (!(window as any).firstEventReceived) {
            (window as any).firstEventReceived = Date.now();
          }
        });
      });
      
      const startTime = Date.now();
      
      await page.fill('[data-testid="topic-input"]', 'Performance Test');
      await page.fill('[data-testid="guidelines-input"]', 'Measure performance');
      await page.fill('[data-testid="sections-input"]', 'Introduction');
      await page.click('[data-testid="start-research-button"]');
      
      // Wait for first event
      await expect(page.locator('[data-testid="section-introduction"]')).toBeVisible();
      
      firstEventTime = await page.evaluate(() => (window as any).firstEventReceived);
      const latency = firstEventTime - startTime;
      
      // First event should arrive within reasonable time
      expect(latency).toBeLessThan(30000); // 30 seconds max
    });

    await test.step('Test SSE connection stability', async () => {
      // Monitor for connection drops or errors during long-running research
      let errorCount = 0;
      
      page.on('pageerror', () => {
        errorCount++;
      });
      
      await page.fill('[data-testid="topic-input"]', 'Stability Test with Multiple Sections');
      await page.fill('[data-testid="guidelines-input"]', 'Test connection stability');
      await page.fill('[data-testid="sections-input"]', 'Introduction,Background,Literature,Methods,Results,Discussion,Conclusion');
      await page.click('[data-testid="start-research-button"]');
      
      // Wait for all sections to complete
      const sections = ['introduction', 'background', 'literature', 'methods', 'results', 'discussion', 'conclusion'];
      for (const section of sections) {
        await expect(page.locator(`[data-testid="section-${section}"]`)).toBeVisible({ timeout: 30000 });
      }
      
      // Wait for final report
      await expect(page.locator('[data-testid="final-report"]')).toBeVisible({ timeout: 60000 });
      
      // Should have minimal errors
      expect(errorCount).toBeLessThanOrEqual(1); // Allow for one potential error
    });
  });

  test('SSE connection management', async ({ page }) => {
    await test.step('Test connection cleanup on page navigation', async () => {
      // Start research
      await page.fill('[data-testid="topic-input"]', 'Navigation Test');
      await page.fill('[data-testid="guidelines-input"]', 'Test cleanup');
      await page.fill('[data-testid="sections-input"]', 'Introduction');
      await page.click('[data-testid="start-research-button"]');
      
      // Wait for connection to establish
      await expect(page.locator('[data-testid="sse-status"]')).toContainText('Connected');
      
      // Navigate away and back
      await page.goto('/about'); // Assuming there's an about page
      await page.goto('/');
      
      // Should not show stale connection state
      const sseStatus = page.locator('[data-testid="sse-status"]');
      const statusText = await sseStatus.textContent();
      expect(statusText).not.toContain('Connected');
    });

    await test.step('Test connection cleanup on browser refresh', async () => {
      // Start research
      await page.fill('[data-testid="topic-input"]', 'Refresh Test');
      await page.fill('[data-testid="guidelines-input"]', 'Test refresh cleanup');
      await page.fill('[data-testid="sections-input"]', 'Introduction');
      await page.click('[data-testid="start-research-button"]');
      
      // Wait for connection
      await expect(page.locator('[data-testid="sse-status"]')).toContainText('Connected');
      
      // Refresh page
      await page.reload();
      
      // Should start fresh
      await expect(page.locator('[data-testid="topic-input"]')).toHaveValue('');
      const sseStatus = page.locator('[data-testid="sse-status"]');
      if (await sseStatus.isVisible()) {
        const statusText = await sseStatus.textContent();
        expect(statusText).not.toContain('Connected');
      }
    });
  });
});