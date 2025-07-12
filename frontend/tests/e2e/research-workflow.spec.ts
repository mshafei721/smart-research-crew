import { test, expect } from '@playwright/test';

/**
 * End-to-end tests for the complete research workflow.
 * 
 * These tests validate the full user journey from entering research parameters
 * to receiving and displaying the final research report via SSE.
 */
test.describe('Research Workflow Integration', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for the app to load
    await expect(page.locator('h1')).toBeVisible();
  });

  test('complete research workflow with real backend', async ({ page }) => {
    // Step 1: Fill out the research form
    await test.step('Fill research form', async () => {
      await page.fill('[data-testid="topic-input"]', 'Artificial Intelligence in Healthcare');
      await page.fill('[data-testid="guidelines-input"]', 'Focus on recent developments and practical applications');
      await page.fill('[data-testid="sections-input"]', 'Introduction,Current Applications,Future Prospects');
      
      // Verify form fields are filled
      await expect(page.locator('[data-testid="topic-input"]')).toHaveValue('Artificial Intelligence in Healthcare');
    });

    // Step 2: Start the research process
    await test.step('Start research', async () => {
      await page.click('[data-testid="start-research-button"]');
      
      // Verify the research started
      await expect(page.locator('[data-testid="research-status"]')).toContainText('Research in progress');
    });

    // Step 3: Monitor SSE events and progress
    await test.step('Monitor research progress', async () => {
      // Wait for section updates to appear
      await expect(page.locator('[data-testid="section-introduction"]')).toBeVisible({ timeout: 60000 });
      await expect(page.locator('[data-testid="section-current-applications"]')).toBeVisible({ timeout: 60000 });
      await expect(page.locator('[data-testid="section-future-prospects"]')).toBeVisible({ timeout: 60000 });
      
      // Verify each section has content
      const sections = ['introduction', 'current-applications', 'future-prospects'];
      for (const section of sections) {
        const sectionContent = page.locator(`[data-testid="section-${section}"] .content`);
        await expect(sectionContent).not.toBeEmpty();
      }
    });

    // Step 4: Verify final report generation
    await test.step('Verify final report', async () => {
      // Wait for final report to be generated
      await expect(page.locator('[data-testid="final-report"]')).toBeVisible({ timeout: 90000 });
      
      // Verify report contains expected sections
      const reportContent = page.locator('[data-testid="final-report"] .report-content');
      await expect(reportContent).toContainText('Introduction');
      await expect(reportContent).toContainText('Current Applications');
      await expect(reportContent).toContainText('Future Prospects');
      
      // Verify report has references
      await expect(reportContent).toContainText('References');
    });

    // Step 5: Test report interactions
    await test.step('Test report interactions', async () => {
      // Test copy functionality
      await page.click('[data-testid="copy-report-button"]');
      
      // Verify copy feedback
      await expect(page.locator('[data-testid="copy-feedback"]')).toContainText('Copied');
      
      // Test download functionality if available
      const downloadButton = page.locator('[data-testid="download-report-button"]');
      if (await downloadButton.isVisible()) {
        const downloadPromise = page.waitForEvent('download');
        await downloadButton.click();
        const download = await downloadPromise;
        expect(download.suggestedFilename()).toMatch(/.*\.(md|txt|pdf)$/);
      }
    });
  });

  test('research workflow with error handling', async ({ page }) => {
    // Test error scenarios
    await test.step('Test validation errors', async () => {
      // Try to start research without filling required fields
      await page.click('[data-testid="start-research-button"]');
      
      // Should show validation errors
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
      await expect(page.locator('[data-testid="error-message"]')).toContainText('required');
    });

    await test.step('Test network error handling', async () => {
      // Fill form with valid data
      await page.fill('[data-testid="topic-input"]', 'Test Topic');
      await page.fill('[data-testid="guidelines-input"]', 'Test Guidelines');
      await page.fill('[data-testid="sections-input"]', 'Introduction');
      
      // Intercept and fail the SSE request
      await page.route('**/sse*', route => route.abort());
      
      await page.click('[data-testid="start-research-button"]');
      
      // Should show connection error
      await expect(page.locator('[data-testid="connection-error"]')).toBeVisible({ timeout: 10000 });
    });
  });

  test('responsive design on mobile', async ({ page, isMobile }) => {
    test.skip(!isMobile, 'This test only runs on mobile');
    
    await test.step('Mobile research form', async () => {
      // Verify mobile layout
      await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible();
      
      // Test collapsible sections
      await page.click('[data-testid="mobile-menu-button"]');
      await expect(page.locator('[data-testid="mobile-nav"]')).toBeVisible();
      
      // Fill form on mobile
      await page.fill('[data-testid="topic-input"]', 'Mobile Test');
      await page.fill('[data-testid="guidelines-input"]', 'Mobile Guidelines');
      await page.fill('[data-testid="sections-input"]', 'Introduction');
      
      await page.click('[data-testid="start-research-button"]');
      
      // Verify mobile-optimized progress display
      await expect(page.locator('[data-testid="mobile-progress"]')).toBeVisible();
    });
  });

  test('concurrent research sessions', async ({ context }) => {
    // Test multiple tabs/sessions
    const page1 = await context.newPage();
    const page2 = await context.newPage();
    
    await page1.goto('/');
    await page2.goto('/');
    
    await test.step('Start concurrent research', async () => {
      // Start research in first tab
      await page1.fill('[data-testid="topic-input"]', 'Topic 1');
      await page1.fill('[data-testid="guidelines-input"]', 'Guidelines 1');
      await page1.fill('[data-testid="sections-input"]', 'Introduction');
      await page1.click('[data-testid="start-research-button"]');
      
      // Start research in second tab
      await page2.fill('[data-testid="topic-input"]', 'Topic 2');
      await page2.fill('[data-testid="guidelines-input"]', 'Guidelines 2');
      await page2.fill('[data-testid="sections-input"]', 'Conclusion');
      await page2.click('[data-testid="start-research-button"]');
      
      // Both should work independently
      await expect(page1.locator('[data-testid="research-status"]')).toContainText('in progress');
      await expect(page2.locator('[data-testid="research-status"]')).toContainText('in progress');
    });
  });

  test('accessibility compliance', async ({ page }) => {
    await test.step('Check ARIA labels and keyboard navigation', async () => {
      // Test keyboard navigation
      await page.keyboard.press('Tab');
      await expect(page.locator('[data-testid="topic-input"]')).toBeFocused();
      
      await page.keyboard.press('Tab');
      await expect(page.locator('[data-testid="guidelines-input"]')).toBeFocused();
      
      // Check ARIA labels
      const topicInput = page.locator('[data-testid="topic-input"]');
      await expect(topicInput).toHaveAttribute('aria-label');
      
      const startButton = page.locator('[data-testid="start-research-button"]');
      await expect(startButton).toHaveAttribute('aria-label');
    });

    await test.step('Check screen reader support', async () => {
      // Verify essential elements have proper roles and labels
      await expect(page.locator('main')).toHaveAttribute('role', 'main');
      await expect(page.locator('[data-testid="research-form"]')).toHaveAttribute('role', 'form');
      
      // Check for proper heading hierarchy
      const h1 = page.locator('h1');
      await expect(h1).toBeVisible();
      
      // Verify form labels
      const labels = page.locator('label');
      const labelCount = await labels.count();
      expect(labelCount).toBeGreaterThan(0);
    });
  });

  test('performance and loading states', async ({ page }) => {
    await test.step('Measure initial load performance', async () => {
      const startTime = Date.now();
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      const loadTime = Date.now() - startTime;
      
      // Should load within 5 seconds
      expect(loadTime).toBeLessThan(5000);
    });

    await test.step('Test loading states during research', async () => {
      await page.fill('[data-testid="topic-input"]', 'Performance Test');
      await page.fill('[data-testid="guidelines-input"]', 'Test Guidelines');
      await page.fill('[data-testid="sections-input"]', 'Introduction');
      
      await page.click('[data-testid="start-research-button"]');
      
      // Should show loading indicator
      await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible();
      
      // Loading state should have proper ARIA attributes
      const loadingIndicator = page.locator('[data-testid="loading-indicator"]');
      await expect(loadingIndicator).toHaveAttribute('aria-live', 'polite');
    });
  });
});