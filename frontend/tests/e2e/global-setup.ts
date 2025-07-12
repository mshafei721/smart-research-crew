import { chromium, FullConfig } from '@playwright/test';

/**
 * Global setup for Playwright tests.
 * 
 * This runs once before all tests and can be used to:
 * - Set up test data
 * - Authenticate users
 * - Start additional services
 * - Validate environment prerequisites
 */
async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting global setup for Smart Research Crew E2E tests...');
  
  const { baseURL } = config.projects[0].use;
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    // Verify frontend is running
    console.log(`📱 Checking frontend at ${baseURL}...`);
    await page.goto(baseURL!);
    await page.waitForSelector('h1', { timeout: 30000 });
    console.log('✅ Frontend is responsive');
    
    // Verify backend health
    console.log('🔧 Checking backend health...');
    const healthResponse = await page.request.get('http://localhost:8000/health');
    if (!healthResponse.ok()) {
      throw new Error(`Backend health check failed: ${healthResponse.status()}`);
    }
    console.log('✅ Backend is healthy');
    
    // Verify SSE endpoint is accessible
    console.log('📡 Testing SSE endpoint accessibility...');
    const sseResponse = await page.request.get('http://localhost:8000/sse?topic=test&sections=intro&guidelines=test');
    if (!sseResponse.ok()) {
      throw new Error(`SSE endpoint not accessible: ${sseResponse.status()}`);
    }
    console.log('✅ SSE endpoint is accessible');
    
  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
  
  console.log('🎉 Global setup completed successfully!');
}

export default globalSetup;