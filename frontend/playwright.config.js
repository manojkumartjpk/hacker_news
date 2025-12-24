const { defineConfig } = require('@playwright/test');

const baseURL = process.env.E2E_BASE_URL || 'http://localhost:3000';

module.exports = defineConfig({
  testDir: './e2e',
  timeout: 60000,
  expect: {
    timeout: 10000,
  },
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL,
    trace: 'retain-on-failure',
  },
});
