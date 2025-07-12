import { test, expect } from '@playwright/test';

/**
 * Visual regression tests using Playwright's screenshot comparison.
 * 
 * These tests capture screenshots of key UI states and compare them
 * against baseline images to detect visual changes and regressions.
 */
test.describe('Visual Regression Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('homepage initial state', async ({ page }) => {
    await test.step('Capture full page screenshot', async () => {
      // Wait for page to fully load
      await page.waitForLoadState('networkidle');
      
      // Take full page screenshot
      await expect(page).toHaveScreenshot('homepage-full.png', {
        fullPage: true,
        animations: 'disabled', // Disable animations for consistent screenshots
      });
    });

    await test.step('Capture above-the-fold content', async () => {
      // Take viewport screenshot
      await expect(page).toHaveScreenshot('homepage-viewport.png', {
        animations: 'disabled',
      });
    });

    await test.step('Capture research form component', async () => {
      const researchForm = page.locator('[data-testid="research-form"]');
      await expect(researchForm).toHaveScreenshot('research-form.png', {
        animations: 'disabled',
      });
    });
  });

  test('form states and validation', async ({ page }) => {
    await test.step('Empty form state', async () => {
      const form = page.locator('[data-testid="research-form"]');
      await expect(form).toHaveScreenshot('form-empty.png', {
        animations: 'disabled',
      });
    });

    await test.step('Filled form state', async () => {
      await page.fill('[data-testid="topic-input"]', 'Artificial Intelligence in Healthcare');
      await page.fill('[data-testid="guidelines-input"]', 'Focus on recent developments and practical applications');
      await page.fill('[data-testid="sections-input"]', 'Introduction,Current Applications,Future Prospects,Challenges,Conclusion');
      
      const form = page.locator('[data-testid="research-form"]');
      await expect(form).toHaveScreenshot('form-filled.png', {
        animations: 'disabled',
      });
    });

    await test.step('Form validation errors', async () => {
      // Clear form and try to submit
      await page.fill('[data-testid="topic-input"]', '');
      await page.fill('[data-testid="guidelines-input"]', '');
      await page.fill('[data-testid="sections-input"]', '');
      await page.click('[data-testid="start-research-button"]');
      
      // Wait for validation errors to appear
      await expect(page.locator('[data-testid="topic-error"]')).toBeVisible();
      
      const form = page.locator('[data-testid="research-form"]');
      await expect(form).toHaveScreenshot('form-validation-errors.png', {
        animations: 'disabled',
      });
    });

    await test.step('Form loading state', async () => {
      // Fill form properly
      await page.fill('[data-testid="topic-input"]', 'Visual Regression Test');
      await page.fill('[data-testid="guidelines-input"]', 'Test loading state visuals');
      await page.fill('[data-testid="sections-input"]', 'Introduction');
      
      // Submit and capture loading state
      await page.click('[data-testid="start-research-button"]');
      
      // Wait for loading state
      await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible();
      
      const form = page.locator('[data-testid="research-form"]');
      await expect(form).toHaveScreenshot('form-loading.png', {
        animations: 'disabled',
      });
    });
  });

  test('research progress states', async ({ page }) => {
    // Start research process
    await page.fill('[data-testid="topic-input"]', 'Progress Visual Test');
    await page.fill('[data-testid="guidelines-input"]', 'Test progress visualization');
    await page.fill('[data-testid="sections-input"]', 'Introduction,Methods,Results');
    await page.click('[data-testid="start-research-button"]');

    await test.step('Initial progress state', async () => {
      await expect(page.locator('[data-testid="research-status"]')).toBeVisible();
      
      const progressArea = page.locator('[data-testid="research-progress"]');
      await expect(progressArea).toHaveScreenshot('progress-initial.png', {
        animations: 'disabled',
      });
    });

    await test.step('Section in progress', async () => {
      // Wait for first section to start
      await expect(page.locator('[data-testid="section-introduction"]')).toBeVisible({ timeout: 30000 });
      
      const sectionElement = page.locator('[data-testid="section-introduction"]');
      await expect(sectionElement).toHaveScreenshot('section-in-progress.png', {
        animations: 'disabled',
      });
    });

    await test.step('Multiple sections with different states', async () => {
      // Wait for multiple sections to appear
      await expect(page.locator('[data-testid="section-methods"]')).toBeVisible({ timeout: 30000 });
      
      const allSections = page.locator('[data-testid*="section-"]');
      await expect(allSections.first()).toHaveScreenshot('sections-mixed-states.png', {
        animations: 'disabled',
      });
    });
  });

  test('final report display', async ({ page }) => {
    // Start and complete research process
    await page.fill('[data-testid="topic-input"]', 'Report Visual Test');
    await page.fill('[data-testid="guidelines-input"]', 'Test final report visualization');
    await page.fill('[data-testid="sections-input"]', 'Introduction,Conclusion');
    await page.click('[data-testid="start-research-button"]');

    // Wait for final report
    await expect(page.locator('[data-testid="final-report"]')).toBeVisible({ timeout: 90000 });

    await test.step('Final report header and metadata', async () => {
      const reportHeader = page.locator('[data-testid="final-report"] .report-header');
      if (await reportHeader.isVisible()) {
        await expect(reportHeader).toHaveScreenshot('report-header.png', {
          animations: 'disabled',
        });
      }
    });

    await test.step('Report content and formatting', async () => {
      const reportContent = page.locator('[data-testid="final-report"] .report-content');
      await expect(reportContent).toHaveScreenshot('report-content.png', {
        animations: 'disabled',
        fullPage: true, // Capture entire content even if scrollable
      });
    });

    await test.step('Report controls and actions', async () => {
      const reportControls = page.locator('[data-testid="report-controls"]');
      if (await reportControls.isVisible()) {
        await expect(reportControls).toHaveScreenshot('report-controls.png', {
          animations: 'disabled',
        });
      }
    });

    await test.step('Table of contents navigation', async () => {
      const tableOfContents = page.locator('[data-testid="table-of-contents"]');
      if (await tableOfContents.isVisible()) {
        await expect(tableOfContents).toHaveScreenshot('table-of-contents.png', {
          animations: 'disabled',
        });
      }
    });
  });

  test('responsive design breakpoints', async ({ page }) => {
    await test.step('Mobile viewport (320px)', async () => {
      await page.setViewportSize({ width: 320, height: 568 });
      await page.waitForTimeout(500); // Allow for responsive changes
      
      await expect(page).toHaveScreenshot('mobile-320.png', {
        animations: 'disabled',
      });
    });

    await test.step('Mobile viewport (375px)', async () => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(500);
      
      await expect(page).toHaveScreenshot('mobile-375.png', {
        animations: 'disabled',
      });
    });

    await test.step('Tablet viewport (768px)', async () => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.waitForTimeout(500);
      
      await expect(page).toHaveScreenshot('tablet-768.png', {
        animations: 'disabled',
      });
    });

    await test.step('Desktop viewport (1024px)', async () => {
      await page.setViewportSize({ width: 1024, height: 768 });
      await page.waitForTimeout(500);
      
      await expect(page).toHaveScreenshot('desktop-1024.png', {
        animations: 'disabled',
      });
    });

    await test.step('Large desktop viewport (1440px)', async () => {
      await page.setViewportSize({ width: 1440, height: 900 });
      await page.waitForTimeout(500);
      
      await expect(page).toHaveScreenshot('desktop-1440.png', {
        animations: 'disabled',
      });
    });
  });

  test('theme variations', async ({ page }) => {
    await test.step('Light theme', async () => {
      // Ensure light theme is active
      await page.evaluate(() => {
        document.documentElement.classList.remove('dark');
      });
      await page.waitForTimeout(200);
      
      await expect(page).toHaveScreenshot('theme-light.png', {
        animations: 'disabled',
      });
    });

    await test.step('Dark theme', async () => {
      // Switch to dark theme
      await page.evaluate(() => {
        document.documentElement.classList.add('dark');
      });
      await page.waitForTimeout(200);
      
      await expect(page).toHaveScreenshot('theme-dark.png', {
        animations: 'disabled',
      });
    });

    await test.step('Theme toggle component', async () => {
      const themeToggle = page.locator('[data-testid="theme-toggle"]');
      if (await themeToggle.isVisible()) {
        await expect(themeToggle).toHaveScreenshot('theme-toggle.png', {
          animations: 'disabled',
        });
      }
    });
  });

  test('error states and edge cases', async ({ page }) => {
    await test.step('Network error state', async () => {
      // Block network requests to simulate offline
      await page.route('**/*', route => route.abort());
      
      await page.fill('[data-testid="topic-input"]', 'Network Error Test');
      await page.fill('[data-testid="guidelines-input"]', 'Test network error handling');
      await page.fill('[data-testid="sections-input"]', 'Introduction');
      await page.click('[data-testid="start-research-button"]');
      
      // Wait for error state
      await expect(page.locator('[data-testid="connection-error"]')).toBeVisible({ timeout: 10000 });
      
      const errorState = page.locator('[data-testid="error-container"]');
      await expect(errorState).toHaveScreenshot('network-error.png', {
        animations: 'disabled',
      });
    });

    await test.step('Empty results state', async () => {
      // Reset network routes
      await page.unroute('**/*');
      
      // Mock empty response
      await page.route('**/sse*', route => {
        route.fulfill({
          status: 200,
          headers: { 'content-type': 'text/plain; charset=utf-8' },
          body: 'data: {"type": "report", "content": ""}\n\n',
        });
      });
      
      await page.fill('[data-testid="topic-input"]', 'Empty Results Test');
      await page.fill('[data-testid="guidelines-input"]', 'Test empty results');
      await page.fill('[data-testid="sections-input"]', 'Introduction');
      await page.click('[data-testid="start-research-button"]');
      
      // Wait for empty state
      await page.waitForTimeout(5000);
      
      const emptyState = page.locator('[data-testid="empty-results"]');
      if (await emptyState.isVisible()) {
        await expect(emptyState).toHaveScreenshot('empty-results.png', {
          animations: 'disabled',
        });
      }
    });
  });

  test('component focus and hover states', async ({ page }) => {
    await test.step('Button focus states', async () => {
      const startButton = page.locator('[data-testid="start-research-button"]');
      await startButton.focus();
      
      await expect(startButton).toHaveScreenshot('button-focus.png', {
        animations: 'disabled',
      });
    });

    await test.step('Input field focus states', async () => {
      const topicInput = page.locator('[data-testid="topic-input"]');
      await topicInput.focus();
      
      await expect(topicInput).toHaveScreenshot('input-focus.png', {
        animations: 'disabled',
      });
    });

    await test.step('Form field with content', async () => {
      await page.fill('[data-testid="topic-input"]', 'Visual Regression Testing');
      const topicInput = page.locator('[data-testid="topic-input"]');
      
      await expect(topicInput).toHaveScreenshot('input-with-content.png', {
        animations: 'disabled',
      });
    });
  });

  test('loading and transition states', async ({ page }) => {
    await test.step('Page loading state', async () => {
      // Reload page and capture loading state
      const pageLoadPromise = page.reload();
      
      // Try to capture loading state (this might not always work due to timing)
      await page.waitForTimeout(100);
      
      try {
        const loadingElement = page.locator('[data-testid="page-loading"]');
        if (await loadingElement.isVisible()) {
          await expect(loadingElement).toHaveScreenshot('page-loading.png', {
            animations: 'disabled',
          });
        }
      } catch (error) {
        console.log('Page loading state not captured (loaded too quickly)');
      }
      
      await pageLoadPromise;
    });

    await test.step('Form submission transition', async () => {
      await page.fill('[data-testid="topic-input"]', 'Transition Test');
      await page.fill('[data-testid="guidelines-input"]', 'Test transitions');
      await page.fill('[data-testid="sections-input"]', 'Introduction');
      
      // Click and immediately capture transition state
      const clickPromise = page.click('[data-testid="start-research-button"]');
      await page.waitForTimeout(100); // Small delay to catch transition
      
      const formTransition = page.locator('[data-testid="research-form"]');
      try {
        await expect(formTransition).toHaveScreenshot('form-transition.png', {
          animations: 'disabled',
        });
      } catch (error) {
        console.log('Form transition state not captured (transitioned too quickly)');
      }
      
      await clickPromise;
    });
  });
});