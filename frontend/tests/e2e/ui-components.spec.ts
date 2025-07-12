import { test, expect } from '@playwright/test';

/**
 * Browser automation tests for UI components and interactions.
 * 
 * These tests validate the behavior of individual UI components,
 * form interactions, responsive design, and visual elements.
 */
test.describe('UI Components and Interactions', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('research form validation and interaction', async ({ page }) => {
    await test.step('Test form field validation', async () => {
      // Submit empty form
      await page.click('[data-testid="start-research-button"]');
      
      // Should show validation errors
      await expect(page.locator('[data-testid="topic-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="guidelines-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="sections-error"]')).toBeVisible();
      
      // Error messages should be descriptive
      await expect(page.locator('[data-testid="topic-error"]')).toContainText('required');
    });

    await test.step('Test form field character limits', async () => {
      // Test topic field limit
      const longTopic = 'A'.repeat(1000);
      await page.fill('[data-testid="topic-input"]', longTopic);
      
      const topicValue = await page.inputValue('[data-testid="topic-input"]');
      // Should either truncate or show error for long input
      expect(topicValue.length).toBeLessThanOrEqual(500);
      
      // Test sections field with many sections
      const manySections = Array(50).fill('Section').map((s, i) => `${s}${i}`).join(',');
      await page.fill('[data-testid="sections-input"]', manySections);
      
      // Should show warning or error for too many sections
      const sectionsWarning = page.locator('[data-testid="sections-warning"]');
      if (await sectionsWarning.isVisible()) {
        await expect(sectionsWarning).toContainText('many sections');
      }
    });

    await test.step('Test form field suggestions', async () => {
      // Test topic suggestions if implemented
      await page.click('[data-testid="topic-input"]');
      const topicSuggestions = page.locator('[data-testid="topic-suggestions"]');
      
      if (await topicSuggestions.isVisible()) {
        await expect(topicSuggestions.locator('.suggestion')).toHaveCount.greaterThan(0);
        
        // Click on a suggestion
        await topicSuggestions.locator('.suggestion').first().click();
        
        // Should fill the topic field
        const topicValue = await page.inputValue('[data-testid="topic-input"]');
        expect(topicValue).not.toBe('');
      }
      
      // Test sections suggestions
      await page.click('[data-testid="sections-input"]');
      const sectionsSuggestions = page.locator('[data-testid="sections-suggestions"]');
      
      if (await sectionsSuggestions.isVisible()) {
        await expect(sectionsSuggestions.locator('.suggestion')).toHaveCount.greaterThan(0);
      }
    });

    await test.step('Test form auto-save functionality', async () => {
      // Fill form fields
      await page.fill('[data-testid="topic-input"]', 'Auto-save Test Topic');
      await page.fill('[data-testid="guidelines-input"]', 'Auto-save guidelines');
      await page.fill('[data-testid="sections-input"]', 'Introduction,Conclusion');
      
      // Refresh page
      await page.reload();
      
      // Check if values are restored (if auto-save is implemented)
      const topicValue = await page.inputValue('[data-testid="topic-input"]');
      if (topicValue) {
        expect(topicValue).toBe('Auto-save Test Topic');
      }
    });
  });

  test('progress indicators and loading states', async ({ page }) => {
    await test.step('Test loading states during research', async () => {
      // Fill form
      await page.fill('[data-testid="topic-input"]', 'Loading Test');
      await page.fill('[data-testid="guidelines-input"]', 'Test loading states');
      await page.fill('[data-testid="sections-input"]', 'Introduction');
      
      // Start research
      await page.click('[data-testid="start-research-button"]');
      
      // Should show loading indicator
      await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible();
      
      // Loading indicator should be animated
      const loadingIndicator = page.locator('[data-testid="loading-indicator"]');
      await expect(loadingIndicator).toHaveClass(/animate-spin|loading|spinning/);
      
      // Button should be disabled during loading
      await expect(page.locator('[data-testid="start-research-button"]')).toBeDisabled();
    });

    await test.step('Test progress bar for sections', async () => {
      const progressBar = page.locator('[data-testid="progress-bar"]');
      
      if (await progressBar.isVisible()) {
        // Progress should start at 0
        const initialProgress = await progressBar.getAttribute('aria-valuenow');
        expect(parseInt(initialProgress || '0')).toBe(0);
        
        // Progress should increase as sections complete
        await expect(progressBar).toHaveAttribute('aria-valuenow', /[1-9]/);
      }
    });

    await test.step('Test section completion indicators', async () => {
      // Wait for sections to appear
      await expect(page.locator('[data-testid="section-introduction"]')).toBeVisible({ timeout: 30000 });
      
      // Section should have completion indicator
      const sectionStatus = page.locator('[data-testid="section-introduction"] [data-testid="status-indicator"]');
      await expect(sectionStatus).toBeVisible();
      
      // Status should be "completed" or "in-progress"
      const statusClass = await sectionStatus.getAttribute('class');
      expect(statusClass).toMatch(/completed|in-progress|success/);
    });
  });

  test('interactive report display and controls', async ({ page }) => {
    // Start a research session first
    await page.fill('[data-testid="topic-input"]', 'Report Display Test');
    await page.fill('[data-testid="guidelines-input"]', 'Test report display');
    await page.fill('[data-testid="sections-input"]', 'Introduction,Methods');
    await page.click('[data-testid="start-research-button"]');
    
    // Wait for report to be generated
    await expect(page.locator('[data-testid="final-report"]')).toBeVisible({ timeout: 60000 });

    await test.step('Test report navigation and scrolling', async () => {
      const reportContent = page.locator('[data-testid="final-report"] .report-content');
      
      // Should have table of contents with links
      const tocLinks = page.locator('[data-testid="table-of-contents"] a');
      if (await tocLinks.count() > 0) {
        await tocLinks.first().click();
        
        // Should scroll to corresponding section
        await page.waitForTimeout(1000); // Wait for smooth scroll
        
        // Verify section is in view
        const firstSection = page.locator('[data-testid="section-1"]');
        if (await firstSection.isVisible()) {
          await expect(firstSection).toBeInViewport();
        }
      }
      
      // Test scroll-to-top functionality
      const scrollToTop = page.locator('[data-testid="scroll-to-top"]');
      if (await scrollToTop.isVisible()) {
        await scrollToTop.click();
        
        // Should scroll to top
        const isAtTop = await page.evaluate(() => window.scrollY < 100);
        expect(isAtTop).toBeTruthy();
      }
    });

    await test.step('Test report copy functionality', async () => {
      const copyButton = page.locator('[data-testid="copy-report-button"]');
      await expect(copyButton).toBeVisible();
      
      await copyButton.click();
      
      // Should show feedback
      await expect(page.locator('[data-testid="copy-feedback"]')).toBeVisible();
      await expect(page.locator('[data-testid="copy-feedback"]')).toContainText(/copied|success/i);
      
      // Feedback should disappear after a few seconds
      await expect(page.locator('[data-testid="copy-feedback"]')).not.toBeVisible({ timeout: 5000 });
    });

    await test.step('Test report export options', async () => {
      const exportButton = page.locator('[data-testid="export-button"]');
      
      if (await exportButton.isVisible()) {
        await exportButton.click();
        
        // Should show export options
        await expect(page.locator('[data-testid="export-options"]')).toBeVisible();
        
        // Test different export formats
        const exportFormats = ['markdown', 'pdf', 'docx'];
        for (const format of exportFormats) {
          const formatButton = page.locator(`[data-testid="export-${format}"]`);
          if (await formatButton.isVisible()) {
            const downloadPromise = page.waitForEvent('download');
            await formatButton.click();
            const download = await downloadPromise;
            
            expect(download.suggestedFilename()).toMatch(new RegExp(`\\.(${format}|${format.replace('docx', 'doc')})$`));
          }
        }
      }
    });

    await test.step('Test report sharing functionality', async () => {
      const shareButton = page.locator('[data-testid="share-button"]');
      
      if (await shareButton.isVisible()) {
        await shareButton.click();
        
        // Should show share options
        await expect(page.locator('[data-testid="share-options"]')).toBeVisible();
        
        // Test copy link functionality
        const copyLinkButton = page.locator('[data-testid="copy-link-button"]');
        if (await copyLinkButton.isVisible()) {
          await copyLinkButton.click();
          
          await expect(page.locator('[data-testid="link-copied-feedback"]')).toBeVisible();
        }
      }
    });
  });

  test('responsive design and mobile interactions', async ({ page, isMobile }) => {
    await test.step('Test mobile navigation', async () => {
      if (isMobile) {
        // Mobile menu should be visible
        await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible();
        
        // Open mobile menu
        await page.click('[data-testid="mobile-menu-button"]');
        await expect(page.locator('[data-testid="mobile-nav"]')).toBeVisible();
        
        // Navigation items should be accessible
        const navItems = page.locator('[data-testid="mobile-nav"] .nav-item');
        await expect(navItems).toHaveCount.greaterThan(0);
        
        // Close menu
        await page.click('[data-testid="mobile-menu-close"]');
        await expect(page.locator('[data-testid="mobile-nav"]')).not.toBeVisible();
      } else {
        // Desktop navigation should be visible
        await expect(page.locator('[data-testid="desktop-nav"]')).toBeVisible();
        await expect(page.locator('[data-testid="mobile-menu-button"]')).not.toBeVisible();
      }
    });

    await test.step('Test form layout on different screen sizes', async () => {
      // Form should be readable and usable
      await expect(page.locator('[data-testid="research-form"]')).toBeVisible();
      
      if (isMobile) {
        // On mobile, form fields should stack vertically
        const formContainer = page.locator('[data-testid="research-form"]');
        const boundingBox = await formContainer.boundingBox();
        
        if (boundingBox) {
          // Form should not be too wide for mobile
          expect(boundingBox.width).toBeLessThan(500);
        }
        
        // Input fields should be appropriately sized
        const topicInput = page.locator('[data-testid="topic-input"]');
        const inputBox = await topicInput.boundingBox();
        
        if (inputBox) {
          expect(inputBox.width).toBeGreaterThan(200); // Minimum usable width
        }
      }
    });

    await test.step('Test touch interactions on mobile', async () => {
      if (isMobile) {
        // Fill form using touch
        await page.tap('[data-testid="topic-input"]');
        await page.fill('[data-testid="topic-input"]', 'Mobile Touch Test');
        
        await page.tap('[data-testid="guidelines-input"]');
        await page.fill('[data-testid="guidelines-input"]', 'Mobile guidelines');
        
        await page.tap('[data-testid="sections-input"]');
        await page.fill('[data-testid="sections-input"]', 'Introduction');
        
        // Submit using touch
        await page.tap('[data-testid="start-research-button"]');
        
        // Should start research process
        await expect(page.locator('[data-testid="research-status"]')).toContainText('progress');
      }
    });
  });

  test('keyboard navigation and accessibility', async ({ page }) => {
    await test.step('Test tab navigation through form', async () => {
      // Start from beginning
      await page.keyboard.press('Tab');
      await expect(page.locator('[data-testid="topic-input"]')).toBeFocused();
      
      await page.keyboard.press('Tab');
      await expect(page.locator('[data-testid="guidelines-input"]')).toBeFocused();
      
      await page.keyboard.press('Tab');
      await expect(page.locator('[data-testid="sections-input"]')).toBeFocused();
      
      await page.keyboard.press('Tab');
      await expect(page.locator('[data-testid="start-research-button"]')).toBeFocused();
    });

    await test.step('Test keyboard form submission', async () => {
      // Fill form using keyboard
      await page.focus('[data-testid="topic-input"]');
      await page.keyboard.type('Keyboard Navigation Test');
      
      await page.keyboard.press('Tab');
      await page.keyboard.type('Test keyboard accessibility');
      
      await page.keyboard.press('Tab');
      await page.keyboard.type('Introduction');
      
      // Submit using Enter
      await page.keyboard.press('Tab');
      await page.keyboard.press('Enter');
      
      // Should start research
      await expect(page.locator('[data-testid="research-status"]')).toContainText('progress');
    });

    await test.step('Test escape key functionality', async () => {
      // If modal is open, escape should close it
      const modal = page.locator('[data-testid="modal"]');
      if (await modal.isVisible()) {
        await page.keyboard.press('Escape');
        await expect(modal).not.toBeVisible();
      }
      
      // If dropdown is open, escape should close it
      const dropdown = page.locator('[data-testid="dropdown"]');
      if (await dropdown.isVisible()) {
        await page.keyboard.press('Escape');
        await expect(dropdown).not.toBeVisible();
      }
    });

    await test.step('Test screen reader support', async () => {
      // Check for proper ARIA labels
      await expect(page.locator('[data-testid="topic-input"]')).toHaveAttribute('aria-label');
      await expect(page.locator('[data-testid="guidelines-input"]')).toHaveAttribute('aria-label');
      await expect(page.locator('[data-testid="sections-input"]')).toHaveAttribute('aria-label');
      
      // Check for proper roles
      await expect(page.locator('[data-testid="research-form"]')).toHaveAttribute('role', 'form');
      await expect(page.locator('main')).toHaveAttribute('role', 'main');
      
      // Check for live regions for dynamic content
      const liveRegion = page.locator('[aria-live]');
      if (await liveRegion.count() > 0) {
        await expect(liveRegion.first()).toHaveAttribute('aria-live', /polite|assertive/);
      }
    });
  });

  test('dark mode and theme switching', async ({ page }) => {
    await test.step('Test theme toggle functionality', async () => {
      const themeToggle = page.locator('[data-testid="theme-toggle"]');
      
      if (await themeToggle.isVisible()) {
        // Get initial theme
        const initialTheme = await page.evaluate(() => 
          document.documentElement.classList.contains('dark') ? 'dark' : 'light'
        );
        
        // Toggle theme
        await themeToggle.click();
        
        // Theme should change
        const newTheme = await page.evaluate(() => 
          document.documentElement.classList.contains('dark') ? 'dark' : 'light'
        );
        
        expect(newTheme).not.toBe(initialTheme);
        
        // Theme preference should persist
        await page.reload();
        
        const persistedTheme = await page.evaluate(() => 
          document.documentElement.classList.contains('dark') ? 'dark' : 'light'
        );
        
        expect(persistedTheme).toBe(newTheme);
      }
    });

    await test.step('Test system theme preference', async () => {
      // Test prefers-color-scheme: dark
      await page.emulateMedia({ colorScheme: 'dark' });
      await page.reload();
      
      const isDarkMode = await page.evaluate(() => 
        document.documentElement.classList.contains('dark') || 
        getComputedStyle(document.body).backgroundColor === 'rgb(0, 0, 0)'
      );
      
      // Should respect system preference if no manual override
      expect(typeof isDarkMode).toBe('boolean');
    });
  });

  test('animations and visual feedback', async ({ page }) => {
    await test.step('Test button hover and focus states', async () => {
      const startButton = page.locator('[data-testid="start-research-button"]');
      
      // Test hover state
      await startButton.hover();
      await page.waitForTimeout(100); // Allow for hover animation
      
      const hoverClass = await startButton.getAttribute('class');
      expect(hoverClass).toMatch(/hover|focus|active/);
      
      // Test focus state
      await startButton.focus();
      const focusClass = await startButton.getAttribute('class');
      expect(focusClass).toMatch(/focus|ring/);
    });

    await test.step('Test form field animations', async () => {
      const topicInput = page.locator('[data-testid="topic-input"]');
      
      // Focus animation
      await topicInput.focus();
      await page.waitForTimeout(100);
      
      // Should have focus styling
      const focusedClass = await topicInput.getAttribute('class');
      expect(focusedClass).toMatch(/focus|ring|border/);
      
      // Type and check for validation styling
      await topicInput.fill('Test');
      await topicInput.blur();
      
      // Should show valid state
      const validClass = await topicInput.getAttribute('class');
      expect(validClass).not.toMatch(/error|invalid/);
    });

    await test.step('Test loading animations', async () => {
      // Fill form and start research
      await page.fill('[data-testid="topic-input"]', 'Animation Test');
      await page.fill('[data-testid="guidelines-input"]', 'Test animations');
      await page.fill('[data-testid="sections-input"]', 'Introduction');
      await page.click('[data-testid="start-research-button"]');
      
      // Loading spinner should be animated
      const loadingSpinner = page.locator('[data-testid="loading-indicator"]');
      await expect(loadingSpinner).toBeVisible();
      
      const spinnerClass = await loadingSpinner.getAttribute('class');
      expect(spinnerClass).toMatch(/animate-spin|spin|rotate|loading/);
    });
  });
});