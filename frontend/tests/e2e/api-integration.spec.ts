import { test, expect } from '@playwright/test';

/**
 * End-to-end tests for API integration between frontend and backend.
 * 
 * These tests validate direct API communication, error handling,
 * and data flow between the React frontend and FastAPI backend.
 */
test.describe('API Integration', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('health check endpoint', async ({ page }) => {
    await test.step('Verify health endpoint accessibility', async () => {
      const response = await page.request.get('http://localhost:8000/health');
      
      expect(response.ok()).toBeTruthy();
      expect(response.status()).toBe(200);
      
      const healthData = await response.json();
      expect(healthData).toHaveProperty('status', 'healthy');
      expect(healthData).toHaveProperty('timestamp');
      expect(healthData).toHaveProperty('version');
    });

    await test.step('Display health status in UI if available', async () => {
      // Check if UI displays health status (if implemented)
      const healthIndicator = page.locator('[data-testid="health-indicator"]');
      if (await healthIndicator.isVisible()) {
        await expect(healthIndicator).toHaveClass(/healthy/);
      }
    });
  });

  test('settings endpoint', async ({ page }) => {
    await test.step('Fetch application settings', async () => {
      const response = await page.request.get('http://localhost:8000/settings');
      
      expect(response.ok()).toBeTruthy();
      const settings = await response.json();
      
      // Verify settings structure
      expect(settings).toHaveProperty('environment');
      expect(settings).toHaveProperty('log_level');
      expect(settings).toHaveProperty('max_sections');
      
      // Verify reasonable defaults
      expect(settings.max_sections).toBeGreaterThan(0);
      expect(settings.max_sections).toBeLessThanOrEqual(20);
    });

    await test.step('Use settings in frontend form validation', async () => {
      // If settings affect form validation, test that
      const response = await page.request.get('http://localhost:8000/settings');
      const settings = await response.json();
      
      if (settings.max_sections) {
        // Try to create more sections than allowed
        const tooManySections = Array(settings.max_sections + 1).fill('Section').join(',');
        
        await page.fill('[data-testid="topic-input"]', 'Settings Test');
        await page.fill('[data-testid="guidelines-input"]', 'Test validation');
        await page.fill('[data-testid="sections-input"]', tooManySections);
        await page.click('[data-testid="start-research-button"]');
        
        // Should show validation error
        await expect(page.locator('[data-testid="validation-error"]')).toBeVisible();
        await expect(page.locator('[data-testid="validation-error"]')).toContainText('too many sections');
      }
    });
  });

  test('SSE endpoint parameter validation', async ({ page }) => {
    await test.step('Test required parameters', async () => {
      // Test missing topic
      const response1 = await page.request.get('http://localhost:8000/sse?guidelines=test&sections=intro');
      expect(response1.status()).toBe(422); // Validation error
      
      // Test missing guidelines
      const response2 = await page.request.get('http://localhost:8000/sse?topic=test&sections=intro');
      expect(response2.status()).toBe(422);
      
      // Test missing sections
      const response3 = await page.request.get('http://localhost:8000/sse?topic=test&guidelines=test');
      expect(response3.status()).toBe(422);
    });

    await test.step('Test parameter limits and validation', async () => {
      // Test very long topic
      const longTopic = 'A'.repeat(1000);
      const response1 = await page.request.get(`http://localhost:8000/sse?topic=${encodeURIComponent(longTopic)}&guidelines=test&sections=intro`);
      expect([200, 422]).toContain(response1.status()); // Either accepts or rejects long topic
      
      // Test empty sections
      const response2 = await page.request.get('http://localhost:8000/sse?topic=test&guidelines=test&sections=');
      expect(response2.status()).toBe(422);
      
      // Test invalid section names
      const response3 = await page.request.get('http://localhost:8000/sse?topic=test&guidelines=test&sections=,,,');
      expect(response3.status()).toBe(422);
    });

    await test.step('Test valid parameters', async () => {
      const response = await page.request.get('http://localhost:8000/sse?topic=Valid%20Topic&guidelines=Valid%20guidelines&sections=Introduction,Conclusion');
      
      expect(response.ok()).toBeTruthy();
      expect(response.headers()['content-type']).toBe('text/plain; charset=utf-8');
      expect(response.headers()['cache-control']).toBe('no-cache');
      expect(response.headers()['connection']).toBe('keep-alive');
    });
  });

  test('CORS and security headers', async ({ page }) => {
    await test.step('Verify CORS headers', async () => {
      const response = await page.request.get('http://localhost:8000/health');
      
      // Should have appropriate CORS headers for development
      const corsOrigin = response.headers()['access-control-allow-origin'];
      expect(corsOrigin).toBeTruthy();
      expect(['*', 'http://localhost:5173']).toContain(corsOrigin);
    });

    await test.step('Verify security headers', async () => {
      const response = await page.request.get('http://localhost:8000/health');
      
      // Check for basic security headers
      const headers = response.headers();
      
      // Should not expose server information
      expect(headers['server']).toBeUndefined();
      
      // Should have appropriate content type
      expect(headers['content-type']).toContain('application/json');
    });

    await test.step('Test preflight requests for CORS', async () => {
      const response = await page.request.fetch('http://localhost:8000/health', {
        method: 'OPTIONS',
        headers: {
          'Origin': 'http://localhost:5173',
          'Access-Control-Request-Method': 'GET',
        }
      });
      
      expect([200, 204]).toContain(response.status());
      
      const allowMethods = response.headers()['access-control-allow-methods'];
      if (allowMethods) {
        expect(allowMethods).toContain('GET');
      }
    });
  });

  test('error handling and status codes', async ({ page }) => {
    await test.step('Test 404 handling', async () => {
      const response = await page.request.get('http://localhost:8000/nonexistent-endpoint');
      expect(response.status()).toBe(404);
      
      const errorData = await response.json().catch(() => ({}));
      expect(errorData).toHaveProperty('detail');
    });

    await test.step('Test method not allowed', async () => {
      const response = await page.request.post('http://localhost:8000/health', {
        data: { test: 'data' }
      });
      expect(response.status()).toBe(405);
    });

    await test.step('Frontend error handling', async () => {
      // Test how frontend handles API errors
      await page.route('**/health', route => route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' })
      }));
      
      // If frontend checks health status, it should handle errors gracefully
      const healthIndicator = page.locator('[data-testid="health-indicator"]');
      if (await healthIndicator.isVisible()) {
        await expect(healthIndicator).toHaveClass(/error|unhealthy/);
      }
    });
  });

  test('rate limiting and performance', async ({ page }) => {
    await test.step('Test concurrent requests', async () => {
      // Make multiple concurrent requests to health endpoint
      const requests = Array(10).fill(null).map(() => 
        page.request.get('http://localhost:8000/health')
      );
      
      const responses = await Promise.all(requests);
      
      // All should succeed (no rate limiting on health endpoint)
      responses.forEach(response => {
        expect(response.ok()).toBeTruthy();
      });
    });

    await test.step('Test SSE connection limits', async () => {
      // Test multiple SSE connections
      const sseRequests = Array(3).fill(null).map((_, i) =>
        page.request.get(`http://localhost:8000/sse?topic=Test${i}&guidelines=Test&sections=Introduction`)
      );
      
      const responses = await Promise.allSettled(sseRequests);
      
      // At least some should succeed
      const successfulResponses = responses.filter(r => 
        r.status === 'fulfilled' && (r.value as any).ok()
      );
      expect(successfulResponses.length).toBeGreaterThan(0);
    });

    await test.step('Measure API response times', async () => {
      const startTime = Date.now();
      const response = await page.request.get('http://localhost:8000/health');
      const responseTime = Date.now() - startTime;
      
      expect(response.ok()).toBeTruthy();
      expect(responseTime).toBeLessThan(5000); // Should respond within 5 seconds
    });
  });

  test('data validation and serialization', async ({ page }) => {
    await test.step('Test JSON response format', async () => {
      const response = await page.request.get('http://localhost:8000/health');
      const data = await response.json();
      
      // Should be valid JSON with expected structure
      expect(typeof data).toBe('object');
      expect(data).not.toBeNull();
      
      // Verify timestamp format
      if (data.timestamp) {
        const timestamp = new Date(data.timestamp);
        expect(timestamp.getTime()).not.toBeNaN();
      }
    });

    await test.step('Test SSE data format', async () => {
      // Make SSE request and check initial response format
      const response = await page.request.get('http://localhost:8000/sse?topic=Format%20Test&guidelines=Test&sections=Introduction');
      
      expect(response.ok()).toBeTruthy();
      
      // Should have correct SSE headers
      expect(response.headers()['content-type']).toBe('text/plain; charset=utf-8');
      expect(response.headers()['cache-control']).toBe('no-cache');
    });

    await test.step('Test special characters and encoding', async () => {
      // Test with special characters in parameters
      const specialTopic = 'Test with émojis 🚀 and spëcial çharacters';
      const specialGuidelines = 'Guidelines with "quotes" and <html> tags';
      
      const response = await page.request.get(
        `http://localhost:8000/sse?topic=${encodeURIComponent(specialTopic)}&guidelines=${encodeURIComponent(specialGuidelines)}&sections=Introduction`
      );
      
      expect(response.ok()).toBeTruthy();
    });
  });

  test('API versioning and compatibility', async ({ page }) => {
    await test.step('Check API version information', async () => {
      const response = await page.request.get('http://localhost:8000/health');
      const data = await response.json();
      
      // Should include version information
      if (data.version) {
        expect(typeof data.version).toBe('string');
        expect(data.version).toMatch(/^\d+\.\d+/); // Should match version pattern
      }
    });

    await test.step('Test backwards compatibility', async () => {
      // Test that existing endpoints still work as expected
      const endpoints = [
        '/health',
        '/settings',
        '/sse?topic=test&guidelines=test&sections=test'
      ];
      
      for (const endpoint of endpoints) {
        const response = await page.request.get(`http://localhost:8000${endpoint}`);
        expect([200, 422]).toContain(response.status()); // Either success or validation error
      }
    });
  });
});