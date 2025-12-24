const { test, expect } = require('@playwright/test');
const { lookup } = require('dns').promises;

test.describe.serial('Hacker News e2e flow', () => {
  test('registers, logs in, posts, filters, searches, comments, and votes', async ({ page, request }) => {
    const baseUrl = process.env.E2E_BASE_URL || 'http://localhost:3000';
    let apiBaseUrl = process.env.E2E_API_BASE_URL || 'http://localhost:8000';
    try {
      const apiUrl = new URL(apiBaseUrl);
      if (apiUrl.hostname === 'localhost') {
        const resolved = await lookup(apiUrl.hostname);
        apiUrl.hostname = resolved.address;
        apiBaseUrl = apiUrl.toString().replace(/\/$/, '');
      }
    } catch (error) {
      // Leave apiBaseUrl as-is if resolution fails.
    }
    const apiRoutes = ['**/auth/**', '**/posts/**', '**/comments/**', '**/notifications/**'];
    // Prevent API-rewrite routing from hijacking Next.js internal assets like:
    // `/_next/static/chunks/app/comments/page.js` (which matches `**/comments/**`).
    await page.route('**/_next/**', (route) => route.continue());
    for (const pattern of apiRoutes) {
      await page.route(pattern, async (route) => {
        const requestUrl = new URL(route.request().url());
        const request = route.request();
        if (requestUrl.pathname.startsWith('/_next/')) {
          return route.continue();
        }
        const response = await route.fetch({
          url: `${apiBaseUrl}${requestUrl.pathname}${requestUrl.search}`,
          method: request.method(),
          headers: request.headers(),
          postData: request.postData(),
        });
        const body = await response.text();
        await route.fulfill({
          status: response.status(),
          headers: response.headers(),
          body,
        });
      });
    }
    const suffix = Date.now();
    const username = `e2euser${suffix}`;
    const email = `e2e${suffix}@example.com`;
    const password = 'Password1!';
    const altUsername = `e2euser${suffix}b`;
    const altEmail = `e2e${suffix}b@example.com`;
    const altPassword = 'Password1!';
    const storyTitle = `E2E Story ${suffix}`;
    const showTitle = `E2E Show ${suffix}`;
    const jobTitle = `E2E Job ${suffix}`;
    const postTitle = `E2E Post ${suffix}`;
    const commentText = `E2E Comment ${suffix}`;
    const replyText = `E2E Reply ${suffix}`;
    const commentEditText = `E2E Comment Edited ${suffix}`;
    const noResultsQuery = `no-results-${suffix}`;
    const storyUrl = `https://example.com/story-${suffix}`;
    const showUrl = `https://example.com/show-${suffix}`;

    page.on('console', (msg) => {
      if (msg.type() === 'error' || msg.type() === 'warning') {
        console.log('[browser]', msg.type(), msg.text());
      }
    });
    page.on('pageerror', (error) => {
      console.log('[browser] pageerror', error.message);
    });
    page.on('response', async (response) => {
      const url = response.url();
      if (url.includes('/comments') || url.includes('/posts') || url.includes('/auth')) {
        console.log('[e2e] response', response.status(), url);
      }
    });

    const registerResponse = await request.post(`${apiBaseUrl}/auth/register`, {
      headers: { 'Content-Type': 'application/json' },
      data: { username, email, password },
    });
    const registerBody = await registerResponse.text();
    expect(
      registerResponse.ok(),
      `register ${registerResponse.status()} ${registerBody}`
    ).toBeTruthy();

    const loginResponse = await request.post(`${apiBaseUrl}/auth/login`, {
      headers: { 'Content-Type': 'application/json' },
      data: { username, password },
    });
    expect(loginResponse.ok(), `login ${loginResponse.status()}`).toBeTruthy();
    const loginData = await loginResponse.json();

    await page.context().addCookies([{
      name: 'access_token',
      value: loginData.access_token,
      url: baseUrl,
    }]);

    await page.goto('/');
    await expect(page.getByRole('link', { name: 'logout' })).toBeVisible();

    await page.goto('/submit');
    await page.locator('input[name="title"]').fill(`Invalid Post ${suffix}`);
    await page.getByRole('button', { name: 'Submit' }).click();
    await expect(page.getByText('Please provide either a URL or text content.')).toBeVisible();

    await page.locator('input[name="title"]').fill(storyTitle);
    await page.locator('input[name="url"]').fill(storyUrl);
    await page.locator('textarea[name="text"]').fill('');
    await page.locator('select[name="post_type"]').selectOption('story');
    await page.getByRole('button', { name: 'Submit' }).click();
    await page.waitForURL('**/');
    await expect(page.getByText(storyTitle)).toBeVisible();

    await page.goto('/submit');
    await page.locator('input[name="title"]').fill(postTitle);
    await page.locator('textarea[name="text"]').fill('E2E body');
    await page.locator('select[name="post_type"]').selectOption('ask');
    await page.getByRole('button', { name: 'Submit' }).click();
    await page.waitForURL('**/');
    await expect(page.getByText(postTitle)).toBeVisible();

    await page.goto('/submit');
    await page.locator('input[name="title"]').fill(showTitle);
    await page.locator('input[name="url"]').fill(showUrl);
    await page.locator('textarea[name="text"]').fill('');
    await page.locator('select[name="post_type"]').selectOption('show');
    await page.getByRole('button', { name: 'Submit' }).click();
    await page.waitForURL('**/');
    await page.goto('/show');
    await expect(page.getByText(showTitle)).toBeVisible();

    await page.goto('/submit');
    await page.locator('input[name="title"]').fill(jobTitle);
    await page.locator('textarea[name="text"]').fill('E2E job description');
    await page.locator('select[name="post_type"]').selectOption('job');
    await page.getByRole('button', { name: 'Submit' }).click();
    await page.waitForURL('**/');
    await page.goto('/jobs');
    await expect(page.getByText(jobTitle)).toBeVisible();

    await page.goto('/ask');
    await expect(page.getByText(postTitle)).toBeVisible();

    await page.goto('/?sort=top');
    await expect(page.getByText(postTitle)).toBeVisible();

    await page.goto('/?sort=best');
    await expect(page.getByText(postTitle)).toBeVisible();

    await page.goto(`/search?q=${encodeURIComponent(postTitle.toLowerCase())}`);
    await expect(page.getByText(postTitle)).toBeVisible();
    await page.getByRole('link', { name: 'More' }).click();
    await page.waitForURL(/\/search\?q=.*&p=2/);

    await page.goto('/ask');
    await expect(page.getByText(postTitle)).toBeVisible();
    await page.getByRole('link', { name: postTitle }).first().click();
    await page.waitForURL('**/post/**');
    const postUrl = page.url();
    const postId = postUrl.split('/post/')[1]?.split('?')[0];

    const scoreLocator = page.locator('.subline .score');
    const scoreBefore = await scoreLocator.textContent();
    await page.locator('div.votearrow[title="upvote"]').first().click();
    await expect(scoreLocator).not.toHaveText(scoreBefore || '');

    // Create a comment and verify it appears on the post detail page.
    await page.locator('textarea.comment-box').fill(commentText);
    const commentCreateResponse = page.waitForResponse((response) => (
      response.url().includes('/comments') && response.request().method() === 'POST'
    ));
    await page.getByRole('button', { name: 'add comment' }).click();
    const commentCreate = await commentCreateResponse;
    console.log('[e2e] comment create', commentCreate.status(), commentCreate.url());
    await expect(page.getByText(commentText)).toBeVisible();

    await page.goto('/');
    const feedScoreLocator = page.locator(`#score_${postId}`);
    const feedScoreBefore = await feedScoreLocator.textContent();
    await page.locator(`#down_${postId}`).click();
    await expect(feedScoreLocator).not.toHaveText(feedScoreBefore || '');

    await page.getByRole('link', { name: 'More' }).click();
    await page.waitForURL(/\/\?p=2/);

    await page.goto(`/search?q=${encodeURIComponent(noResultsQuery)}`);
    await expect(page.getByText('No results found.')).toBeVisible();

    // Ensure the global comments feed shows the new comment.
    const commentsFeedResponse = page.waitForResponse((response) => (
      response.url().includes('/comments/recent') && response.request().method() === 'GET'
    ));
    await page.goto('/comments');
    const commentsFeed = await commentsFeedResponse;
    console.log('[e2e] comments feed', commentsFeed.status(), commentsFeed.url());
    try {
      const commentsFeedData = await commentsFeed.json();
      console.log(
        '[e2e] comments feed items',
        Array.isArray(commentsFeedData) ? commentsFeedData.length : 'non-array',
        Array.isArray(commentsFeedData) ? commentsFeedData[0]?.text : null
      );
    } catch (error) {
      console.log('[e2e] comments feed json error', error.message);
    }
    await expect(page.getByText(commentText)).toBeVisible();

    await page.getByRole('link', { name: 'More' }).click();
    await page.waitForURL(/\/comments\?p=2/);

    await page.getByRole('link', { name: 'logout' }).click();
    await expect(page.getByRole('link', { name: 'login' })).toBeVisible();

    await page.goto('/submit');
    await page.waitForURL(/\/login\?next=\/submit/);

    await page.goto('/register');
    await page.locator('input[name="username"]').fill(username);
    await page.locator('input[name="username"]').blur();
    await expect(page.locator('.hn-form-status .hn-error')).toHaveText('taken');
    await page.locator('input[name="email"]').fill(email);
    await page.locator('input[name="password"]').fill(password);
    await page.getByRole('button', { name: 'Create account' }).click();
    await expect(page.locator('div.hn-error')).toBeVisible();

    await page.locator('input[name="password"]').fill('short');
    await page.getByRole('button', { name: 'Create account' }).click();
    await expect(page.locator('div.hn-error', { hasText: 'Password must be at least 9 characters.' })).toBeVisible();

    await page.locator('input[name="username"]').fill(altUsername);
    await page.locator('input[name="username"]').blur();
    await expect(page.locator('.hn-form-status .hn-success')).toHaveText('available');
    await page.locator('input[name="email"]').fill(altEmail);
    await page.locator('input[name="password"]').fill(altPassword);
    await page.getByRole('button', { name: 'Create account' }).click();
    await expect(page.getByText('Account created. Redirecting to login...')).toBeVisible();
    await page.waitForURL('**/login');

    await page.locator('input[name="username"]').fill(altUsername);
    await page.locator('input[name="password"]').fill(altPassword);
    await page.getByRole('button', { name: 'Login' }).click();
    await expect(page.getByRole('link', { name: 'logout' })).toBeVisible();

    await page.goto(`/post/${postId}`);
    const altCommentText = `E2E Comment B ${suffix}`;
    await page.locator('textarea.comment-box').first().fill(altCommentText);
    await page.getByRole('button', { name: 'add comment' }).click();
    await expect(page.getByText(altCommentText)).toBeVisible();

    const baseCommentRow = page.locator('tr.comtr', { hasText: commentText });
    await baseCommentRow.getByRole('link', { name: 'reply' }).click();
    await baseCommentRow.locator('textarea.comment-box').fill(replyText);
    await baseCommentRow.getByRole('button', { name: 'reply' }).click();
    await expect(page.getByText(replyText)).toBeVisible();

    await expect(page.getByText(altCommentText)).toBeVisible();
    const editLink = page.locator('tr.comtr', { hasText: altCommentText }).getByRole('link', { name: 'edit' });
    await expect(editLink).toBeVisible();
    await editLink.click();
    const editForm = page.locator('.comment-edit');
    await expect(editForm).toBeVisible();
    await editForm.locator('textarea.comment-box').fill(commentEditText);
    await editForm.getByRole('button', { name: 'update' }).click();
    await expect(page.getByText(commentEditText)).toBeVisible();
    const editedCommentRow = page.locator('tr.comtr', { hasText: commentEditText });
    await editedCommentRow.getByRole('link', { name: 'delete' }).click();
    await editedCommentRow.getByRole('button', { name: 'Yes' }).click();
    await expect(page.getByText(commentEditText)).not.toBeVisible();

    await page.getByRole('link', { name: 'logout' }).click();
    await expect(page.getByRole('link', { name: 'login' })).toBeVisible();

    await page.goto('/login');
    await page.locator('input[name="username"]').fill(username);
    await page.locator('input[name="password"]').fill(password);
    await page.getByRole('button', { name: 'Login' }).click();
    await expect(page.getByRole('link', { name: 'logout' })).toBeVisible();

    await page.goto('/notifications');
    await expect(page.locator('div', { hasText: altUsername }).first()).toBeVisible();
    const markAsReadButton = page.getByRole('button', { name: '[mark as read]' }).first();
    if (await markAsReadButton.isVisible()) {
      const markAsReadResponse = page.waitForResponse((response) => (
        response.url().includes('/notifications/') && response.request().method() === 'PUT'
      ));
      await markAsReadButton.click();
      await markAsReadResponse;
    }
  });
});
