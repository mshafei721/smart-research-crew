import { FullConfig } from '@playwright/test';

/**
 * Global teardown for Playwright tests.
 * 
 * This runs once after all tests have completed and can be used to:
 * - Clean up test data
 * - Stop additional services
 * - Generate test reports
 * - Archive test artifacts
 */
async function globalTeardown(config: FullConfig) {
  console.log('🧹 Starting global teardown...');
  
  try {
    // Clean up any test data if needed
    console.log('📊 Cleaning up test data...');
    // Add any cleanup logic here
    
    // Log test completion
    console.log('📈 Test run completed');
    
  } catch (error) {
    console.error('❌ Global teardown error:', error);
    // Don't throw - teardown errors shouldn't fail the build
  }
  
  console.log('✅ Global teardown completed');
}

export default globalTeardown;