# API

Base URL: `http://localhost:8000`

## Authentication
Protected endpoints require a bearer token:

`Authorization: Bearer <access_token>`

## Auth

POST /auth/register
Request body:
{
  username: string,
  email: string,
  password: string
}

Response:
{
  id: integer,
  username: string,
  email: string,
  created_at: string
}

POST /auth/login
Request body:
{
  username: string,
  password: string
}

Response:
{
  access_token: string,
  token_type: "bearer"
}

GET /auth/username-available
Request params:
- username: string (required)

Response:
{
  available: boolean
}

GET /auth/me
Auth: required

Response:
{
  id: integer,
  username: string,
  email: string,
  created_at: string
}

## Posts

POST /posts
Auth: required
Request body:
{
  title: string,
  url: string | null,
  text: string | null,
  post_type: string (optional, default: "story", options: "story", "ask", "show", "job")
}

Response:
{
  id: integer,
  title: string,
  url: string | null,
  text: string | null,
  post_type: string,
  score: integer,
  comment_count: integer,
  user_id: integer,
  username: string,
  created_at: string
}

GET /posts
Request params:
- skip: integer (optional, default: 0)
- limit: integer (optional, default: 10, max: 100)
- sort: string (optional, default: "new", options: "new", "top", "best")
- post_type: string (optional, options: "story", "ask", "show", "job")

Response:
[
  {
    id: integer,
    title: string,
    url: string | null,
    text: string | null,
    post_type: string,
    score: integer,
    comment_count: integer,
    user_id: integer,
    username: string,
    created_at: string
  }
]

GET /posts/search
Request params:
- q: string (optional, default: "")
- skip: integer (optional, default: 0)
- limit: integer (optional, default: 30, max: 100)

Response:
[
  {
    id: integer,
    title: string,
    url: string | null,
    text: string | null,
    post_type: string,
    score: integer,
    comment_count: integer,
    user_id: integer,
    username: string,
    created_at: string
  }
]

GET /posts/{post_id}
Response:
{
  id: integer,
  title: string,
  url: string | null,
  text: string | null,
  post_type: string,
  score: integer,
  comment_count: integer,
  user_id: integer,
  username: string,
  created_at: string
}

PUT /posts/{post_id}
Auth: required
Request body:
{
  title: string | null,
  url: string | null,
  text: string | null,
  post_type: string | null
}

Response:
{
  id: integer,
  title: string,
  url: string | null,
  text: string | null,
  post_type: string,
  score: integer,
  comment_count: integer,
  user_id: integer,
  username: string,
  created_at: string
}

DELETE /posts/{post_id}
Auth: required

Response:
{
  message: string
}

## Comments

POST /posts/{post_id}/comments
Auth: required
Request body:
{
  text: string,
  parent_id: integer | null
}

Response:
{
  id: integer,
  text: string,
  user_id: integer,
  post_id: integer,
  parent_id: integer | null,
  created_at: string,
  username: string,
  score: integer
}

GET /posts/{post_id}/comments
Response:
[
  {
    id: integer,
    text: string,
    user_id: integer,
    post_id: integer,
    parent_id: integer | null,
    created_at: string,
    username: string,
    score: integer,
    replies: [/* same shape as a comment */]
  }
]

PUT /comments/{comment_id}
Auth: required
Request body:
{
  text: string
}

Response:
{
  id: integer,
  text: string,
  user_id: integer,
  post_id: integer,
  parent_id: integer | null,
  created_at: string,
  username: string,
  score: integer
}

DELETE /comments/{comment_id}
Auth: required

Response:
{
  message: string
}

GET /comments/recent
Request params:
- skip: integer (optional, default: 0)
- limit: integer (optional, default: 30, max: 100)

Response:
[
  {
    id: integer,
    text: string,
    user_id: integer,
    post_id: integer,
    parent_id: integer | null,
    created_at: string,
    username: string,
    post_title: string,
    score: integer
  }
]

## Votes

POST /posts/{post_id}/vote
Auth: required
Request body:
{
  vote_type: integer (required, options: 1, -1)
}

Response:
{
  id: integer,
  user_id: integer,
  post_id: integer,
  vote_type: integer
}

GET /posts/{post_id}/vote
Auth: required

Response:
{
  vote_type: integer (1, -1, or 0 if no vote)
}

POST /comments/{comment_id}/vote
Auth: required
Request body:
{
  vote_type: integer (required, options: 1, -1)
}

Response:
{
  id: integer,
  user_id: integer,
  comment_id: integer,
  vote_type: integer,
  created_at: string
}

## Notifications

GET /notifications
Auth: required
Request params:
- skip: integer (optional, default: 0)
- limit: integer (optional, default: 20, max: 100)

Response:
[
  {
    id: integer,
    user_id: integer,
    actor_id: integer,
    actor_username: string,
    type: string,
    message: string,
    read: boolean,
    post_id: integer | null,
    comment_id: integer | null,
    created_at: string
  }
]

PUT /notifications/{notification_id}/read
Auth: required

Response:
{
  message: string
}

GET /notifications/unread/count
Auth: required

Response:
{
  unread_count: integer
}

## Health

GET /
Response:
{
  message: string,
  version: string
}
