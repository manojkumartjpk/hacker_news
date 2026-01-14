const { test, expect } = require('@playwright/test');
const { lookup } = require('dns').promises;

const baseUrl = process.env.E2E_BASE_URL || 'http://localhost:3000';
const apiRoutes = ['**/auth/**', '**/posts/**', '**/comments/**', '**/notifications/**'];

const buildUser = (suffix, tag = '') => ({
  username: `e2euser${suffix}${tag}`,
  email: `e2e${suffix}${tag}@example.com`,
  password: 'Password1!',
});

const resolveApiBaseUrl = async () => {
  let apiBaseUrl = process.env.E2E_API_BASE_URL || 'http://localhost:8000';
  try {
    const apiUrl = new URL(apiBaseUrl);
    if (apiUrl.hostname === 'localhost') {
      const resolved = await lookup(apiUrl.hostname);
      apiUrl.hostname = resolved.address;
      apiBaseUrl = apiUrl.toString();
    }
  } catch (error) {
    // Leave apiBaseUrl as-is if resolution fails.
  }
  return apiBaseUrl.replace(/\/$/, '');
};

const setupApiRouting = async (page, apiBaseUrl) => {
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
};

const getCookieDomain = () => new URL(baseUrl).hostname;

const setAuthCookie = async (page, token, csrfToken) => {
  const domain = getCookieDomain();
  await page.context().addCookies([{
    name: 'access_token',
    value: token,
    domain,
    path: '/',
    httpOnly: true,
    sameSite: 'Lax',
  }, {
    name: 'auth_status',
    value: '1',
    domain,
    path: '/',
    sameSite: 'Lax',
  }, {
    name: 'csrf_token',
    value: csrfToken || '',
    domain,
    path: '/',
    sameSite: 'Lax',
  }]);
};

const waitForText = async (page, text, { refresh = false, retries = 6 } = {}) => {
  const locator = page.getByText(text);
  for (let attempt = 0; attempt < retries; attempt += 1) {
    if ((await locator.count()) > 0 && await locator.first().isVisible()) {
      return;
    }
    if (refresh) {
      await page.reload();
    } else {
      await page.waitForTimeout(500);
    }
  }
  await expect(locator).toBeVisible();
};

const waitForTextToDisappear = async (page, text, { refresh = false, retries = 6 } = {}) => {
  const locator = page.getByText(text);
  for (let attempt = 0; attempt < retries; attempt += 1) {
    if ((await locator.count()) === 0) {
      return;
    }
    if (refresh) {
      await page.reload();
    } else {
      await page.waitForTimeout(500);
    }
  }
  await expect(locator).toHaveCount(0);
};

test.describe.serial('Hacker News e2e flows', () => {
  const state = {
    suffix: Date.now(),
    posts: {},
    comments: {},
  };
  let apiBaseUrl = '';

  test.beforeAll(async ({ request }) => {
    apiBaseUrl = await resolveApiBaseUrl();
    state.user = buildUser(state.suffix);

    const registerResponse = await request.post(`${apiBaseUrl}/auth/register`, {
      headers: { 'Content-Type': 'application/json' },
      data: state.user,
    });
    const registerBody = await registerResponse.text();
    expect(
      registerResponse.ok(),
      `register ${registerResponse.status()} ${registerBody}`
    ).toBeTruthy();

    const loginResponse = await request.post(`${apiBaseUrl}/auth/login`, {
      headers: { 'Content-Type': 'application/json' },
      data: { username: state.user.username, password: state.user.password },
    });
    expect(loginResponse.ok(), `login ${loginResponse.status()}`).toBeTruthy();
    state.userToken = (await loginResponse.json()).access_token;
    state.userCsrfToken = loginResponse.headers()['x-csrf-token'];
  });

  test.beforeEach(async ({ page }) => {
    await setupApiRouting(page, apiBaseUrl);
  });

  test('auth: login and logout', async ({ page }) => {
    await page.context().clearCookies();
    await setAuthCookie(page, state.userToken, state.userCsrfToken);
    await page.goto('/');
    await expect(page.getByRole('link', { name: 'logout' })).toBeVisible();

    await page.getByRole('link', { name: 'logout' }).click();
    await expect(page.getByRole('link', { name: 'login' })).toBeVisible();
  });

  test('auth: register validation and success', async ({ page, request }) => {
    await page.context().clearCookies();
    await page.goto('/register');
    await page.locator('input[name="username"]').fill(state.user.username);
    await page.locator('input[name="username"]').blur();
    await expect(page.locator('.hn-form-status .hn-error')).toHaveText('taken');

    await page.locator('input[name="email"]').fill(state.user.email);
    await page.locator('input[name="password"]').fill(state.user.password);
    await page.getByRole('button', { name: 'Create account' }).click();
    await expect(page.locator('div.hn-error')).toBeVisible();

    await page.locator('input[name="password"]').fill('short');
    await page.getByRole('button', { name: 'Create account' }).click();
    await expect(page.locator('div.hn-error', { hasText: 'Password must be at least 9 characters.' })).toBeVisible();

    state.altUser = buildUser(state.suffix, 'b');
    await page.locator('input[name="username"]').fill(state.altUser.username);
    await page.locator('input[name="username"]').blur();
    await expect(page.locator('.hn-form-status .hn-success')).toHaveText('available');
    await page.locator('input[name="email"]').fill(state.altUser.email);
    await page.locator('input[name="password"]').fill(state.altUser.password);
    await page.getByRole('button', { name: 'Create account' }).click();
    await expect(page.getByText('Account created. Redirecting to login...')).toBeVisible();
    await page.waitForURL('**/login');

    const altLogin = await request.post(`${apiBaseUrl}/auth/login`, {
      headers: { 'Content-Type': 'application/json' },
      data: { username: state.altUser.username, password: state.altUser.password },
    });
    expect(altLogin.ok(), `alt login ${altLogin.status()}`).toBeTruthy();
    state.altUserToken = (await altLogin.json()).access_token;
    state.altUserCsrfToken = altLogin.headers()['x-csrf-token'];
  });

  test('posts: submit and filter feeds', async ({ page }) => {
    await setAuthCookie(page, state.userToken, state.userCsrfToken);
    await page.goto('/submit');
    await page.locator('input[name="title"]').fill(`Invalid Post ${state.suffix}`);
    await page.getByRole('button', { name: 'Submit' }).click();
    await expect(page.getByText('Please provide either a URL or text content.')).toBeVisible();

    state.posts.storyTitle = `E2E Story ${state.suffix}`;
    await page.locator('input[name="title"]').fill(state.posts.storyTitle);
    await page.locator('input[name="url"]').fill(`https://example.com/story-${state.suffix}`);
    await page.locator('textarea[name="text"]').fill('');
    await page.locator('select[name="post_type"]').selectOption('story');
    await page.getByRole('button', { name: 'Submit' }).click();
    await page.waitForURL('**/');
    await expect(page.getByText(state.posts.storyTitle)).toBeVisible();

    state.posts.askTitle = `E2E Ask ${state.suffix}`;
    await page.goto('/submit');
    await page.locator('input[name="title"]').fill(state.posts.askTitle);
    await page.locator('textarea[name="text"]').fill('E2E ask body');
    await page.locator('select[name="post_type"]').selectOption('ask');
    await page.getByRole('button', { name: 'Submit' }).click();
    await page.waitForURL('**/');
    await expect(page.getByText(state.posts.askTitle)).toBeVisible();

    state.posts.showTitle = `E2E Show ${state.suffix}`;
    await page.goto('/submit');
    await page.locator('input[name="title"]').fill(state.posts.showTitle);
    await page.locator('input[name="url"]').fill(`https://example.com/show-${state.suffix}`);
    await page.locator('textarea[name="text"]').fill('');
    await page.locator('select[name="post_type"]').selectOption('show');
    await page.getByRole('button', { name: 'Submit' }).click();
    await page.waitForURL('**/');
    await page.goto('/show');
    await expect(page.getByText(state.posts.showTitle)).toBeVisible();

    state.posts.jobTitle = `E2E Job ${state.suffix}`;
    await page.goto('/submit');
    await page.locator('input[name="title"]').fill(state.posts.jobTitle);
    await page.locator('textarea[name="text"]').fill('E2E job description');
    await page.locator('select[name="post_type"]').selectOption('job');
    await page.getByRole('button', { name: 'Submit' }).click();
    await page.waitForURL('**/');
    await page.goto('/jobs');
    await expect(page.getByText(state.posts.jobTitle)).toBeVisible();

    await page.goto('/ask');
    await expect(page.getByText(state.posts.askTitle)).toBeVisible();
    await page.getByRole('link', { name: state.posts.askTitle }).first().click();
    await page.waitForURL('**/post/**');
    const postUrl = page.url();
    state.posts.askId = postUrl.split('/post/')[1]?.split('?')[0];
    expect(state.posts.askId, 'ask post id').toBeTruthy();

    const pointsLocator = page.locator('.subline .points');
    const pointsBefore = await pointsLocator.textContent();
    await page.locator('div.votearrow[title="upvote"]').first().click();
    await expect.poll(
      async () => (await pointsLocator.textContent()) || '',
      { timeout: 10000 }
    ).not.toBe((pointsBefore || '').trim());
  });

  test('search: results, pagination, no results', async ({ page }) => {
    await setAuthCookie(page, state.userToken, state.userCsrfToken);
    await page.goto(`/search?q=${encodeURIComponent(state.posts.askTitle.toLowerCase())}`);
    await expect(page.getByText(state.posts.askTitle)).toBeVisible();
    await page.getByRole('link', { name: 'More' }).click();
    await page.waitForURL(/\/search\?q=.*&p=2/);

    await page.goto(`/?sort=past`);
    await expect(page.getByText(state.posts.askTitle)).toBeVisible();

    const noResultsQuery = `no-results-${state.suffix}`;
    await page.goto(`/search?q=${encodeURIComponent(noResultsQuery)}`);
    await expect(page.getByText('No results found.')).toBeVisible();
  });

  test('comments: create, reply, edit, delete', async ({ page }) => {
    await setAuthCookie(page, state.altUserToken, state.altUserCsrfToken);
    await page.goto(`/post/${state.posts.askId}`);

    state.comments.notifyText = `E2E Notify Comment ${state.suffix}`;
    await page.locator('textarea.comment-box').first().fill(state.comments.notifyText);
    const notifyCreateResponse = page.waitForResponse((response) => (
      response.url().includes('/comments') && response.request().method() === 'POST'
    ));
    await page.getByRole('button', { name: 'add comment' }).click();
    await notifyCreateResponse;
    await waitForText(page, state.comments.notifyText, { refresh: true });

    state.comments.editText = `E2E Edit Comment ${state.suffix}`;
    await page.locator('textarea.comment-box').first().fill(state.comments.editText);
    const editCreateResponse = page.waitForResponse((response) => (
      response.url().includes('/comments') && response.request().method() === 'POST'
    ));
    await page.getByRole('button', { name: 'add comment' }).click();
    await editCreateResponse;
    await waitForText(page, state.comments.editText, { refresh: true });

    const editRow = page.locator('tr.comtr', { hasText: state.comments.editText });
    await editRow.getByRole('link', { name: 'edit' }).click();
    const editForm = page.locator('.comment-edit');
    await expect(editForm).toBeVisible();
    state.comments.updatedText = `E2E Comment Updated ${state.suffix}`;
    await editForm.locator('textarea.comment-box').fill(state.comments.updatedText);
    const editUpdateResponse = page.waitForResponse((response) => (
      response.url().includes('/comments/') && response.request().method() === 'PUT'
    ));
    await editForm.getByRole('button', { name: 'update' }).click();
    await editUpdateResponse;
    await waitForText(page, state.comments.updatedText, { refresh: true });

    const replyBase = page.locator('tr.comtr', { hasText: state.comments.notifyText });
    const replyLink = replyBase.getByRole('link', { name: 'reply' });
    const replyHref = await replyLink.getAttribute('href');
    await replyLink.click();
    if (replyHref) {
      await page.waitForURL(replyHref);
    }
    state.comments.replyText = `E2E Reply ${state.suffix}`;
    await page.locator('textarea.comment-box').fill(state.comments.replyText);
    const replyCreateResponse = page.waitForResponse((response) => (
      response.url().includes('/comments') && response.request().method() === 'POST'
    ));
    await page.getByRole('button', { name: 'reply' }).click();
    await replyCreateResponse;
    await page.waitForURL(/\/post\/\d+/);
    await waitForText(page, state.comments.replyText, { refresh: true });

    const updatedRow = page.locator('tr.comtr', { hasText: state.comments.updatedText });
    await updatedRow.getByRole('link', { name: 'delete' }).click();
    const deleteResponse = page.waitForResponse((response) => (
      response.url().includes('/comments/') && response.request().method() === 'DELETE'
    ));
    await updatedRow.getByRole('button', { name: 'Yes' }).click();
    await deleteResponse;
    await waitForTextToDisappear(page, state.comments.updatedText, { refresh: true });

    await page.goto('/comments');
    await waitForText(page, state.comments.notifyText, { refresh: true });
  });

  test('notifications: see and mark as read', async ({ page }) => {
    await setAuthCookie(page, state.userToken, state.userCsrfToken);
    await page.goto('/notifications');
    await expect(page.locator('div', { hasText: state.altUser.username }).first()).toBeVisible();
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
