import { test, expect } from '@playwright/test'

test('home page shows welcome', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('Welcome to FinRack')).toBeVisible()
})


