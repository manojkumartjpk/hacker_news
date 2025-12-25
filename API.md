# API

Base URL: `http://localhost:8000`

## Authentication
Protected endpoints require a bearer token header (or an auth cookie):

`Authorization: Bearer <access_token>`

When using auth cookies, include `X-CSRF-Token` for POST/PUT/PATCH/DELETE (token is set in the `csrf_token` cookie).

Logout revokes the access token and the client should also clear the JWT cookie.

## Auth

`POST /auth/register`

Request body:
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

Response:
```json
{
  "id": 1,
  "username": "string",
  "email": "string",
  "created_at": "string"
}
```

`POST /auth/login`

Request body:
```json
{
  "username": "string",
  "password": "string"
}
```

Response:
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

`GET /auth/username-available`

Request params:
- `username`: string (required)

Response:
```json
{
  "available": true
}
```

`GET /auth/me`

Auth: required

Response:
```json
{
  "id": 1,
  "username": "string",
  "email": "string",
  "created_at": "string"
}
```

`POST /auth/logout`

Auth: required

Response:
```json
{
  "message": "Logged out"
}
```

## Posts

`POST /posts`

Auth: required

Request body:
```json
{
  "title": "string",
  "url": "string | null",
  "text": "string | null",
  "post_type": "story | ask | show | job"
}
```

Response:
```json
{
  "id": 1,
  "title": "string",
  "url": "string | null",
  "text": "string | null",
  "post_type": "string",
  "score": 0,
  "comment_count": 0,
  "user_id": 1,
  "username": "string",
  "created_at": "string"
}
```

`GET /posts`

Request params:
- `skip`: integer (optional, default: 0)
- `limit`: integer (optional, default: 10, max: 100)
- `sort`: string (optional, default: `new`, options: `new`, `top`, `best`)
- `post_type`: string (optional, options: `story`, `ask`, `show`, `job`)

Response:
```json
[
  {
    "id": 1,
    "title": "string",
    "url": "string | null",
    "text": "string | null",
    "post_type": "string",
    "score": 0,
    "comment_count": 0,
    "user_id": 1,
    "username": "string",
    "created_at": "string"
  }
]
```

`GET /posts/search`

Request params:
- `q`: string (optional, default: "")
- `skip`: integer (optional, default: 0)
- `limit`: integer (optional, default: 30, max: 100)

Response:
```json
[
  {
    "id": 1,
    "title": "string",
    "url": "string | null",
    "text": "string | null",
    "post_type": "string",
    "score": 0,
    "comment_count": 0,
    "user_id": 1,
    "username": "string",
    "created_at": "string"
  }
]
```

`GET /posts/{post_id}`

Response:
```json
{
  "id": 1,
  "title": "string",
  "url": "string | null",
  "text": "string | null",
  "post_type": "string",
  "score": 0,
  "comment_count": 0,
  "user_id": 1,
  "username": "string",
  "created_at": "string"
}
```

`PUT /posts/{post_id}`

Auth: required

Request body:
```json
{
  "title": "string | null",
  "url": "string | null",
  "text": "string | null",
  "post_type": "string | null"
}
```

Response:
```json
{
  "id": 1,
  "title": "string",
  "url": "string | null",
  "text": "string | null",
  "post_type": "string",
  "score": 0,
  "comment_count": 0,
  "user_id": 1,
  "username": "string",
  "created_at": "string"
}
```

`DELETE /posts/{post_id}`

Auth: required

Response: `204 No Content`

## Comments

`POST /posts/{post_id}/comments`

Auth: required

Request body:
```json
{
  "text": "string",
  "parent_id": "integer | null"
}
```

Response:
```json
{
  "id": 1,
  "text": "string",
  "user_id": 1,
  "post_id": 1,
  "parent_id": "integer | null",
  "created_at": "string",
  "username": "string",
  "score": 0
}
```

`GET /posts/{post_id}/comments`

Comments are sorted by total score (the comment's votes plus all nested replies). Ties are broken by `created_at` descending.

Response:
```json
[
  {
    "id": 1,
    "text": "string",
    "user_id": 1,
    "post_id": 1,
    "parent_id": "integer | null",
    "created_at": "string",
    "username": "string",
    "score": 0,
    "replies": []
  }
]
```

`GET /comments/{comment_id}`

Response:
```json
{
  "id": 1,
  "text": "string",
  "user_id": 1,
  "post_id": 1,
  "parent_id": "integer | null",
  "created_at": "string",
  "username": "string",
  "post_title": "string",
  "score": 0
}
```

`PUT /comments/{comment_id}`

Auth: required

Request body:
```json
{
  "text": "string"
}
```

Response:
```json
{
  "id": 1,
  "text": "string",
  "user_id": 1,
  "post_id": 1,
  "parent_id": "integer | null",
  "created_at": "string",
  "username": "string",
  "score": 0
}
```

`DELETE /comments/{comment_id}`

Auth: required

Response: `204 No Content`

`GET /comments/recent`

Comments are sorted by `created_at` descending.

Request params:
- `skip`: integer (optional, default: 0)
- `limit`: integer (optional, default: 30, max: 100)

Response:
```json
[
  {
    "id": 1,
    "text": "string",
    "user_id": 1,
    "post_id": 1,
    "parent_id": "integer | null",
    "created_at": "string",
    "username": "string",
    "post_title": "string",
    "score": 0
  }
]
```

## Votes

`POST /posts/{post_id}/vote`

Auth: required

Request body:
```json
{
  "vote_type": 1
}
```

Response:
```json
{
  "id": 1,
  "user_id": 1,
  "post_id": 1,
  "vote_type": 1
}
```

`GET /posts/{post_id}/vote`

Auth: required

Response:
```json
{
  "vote_type": 1
}
```

`DELETE /posts/{post_id}/vote`

Auth: required

Response:
```json
{
  "vote_type": 0
}
```

`POST /comments/{comment_id}/vote`

Auth: required

Request body:
```json
{
  "vote_type": 1
}
```

Response:
```json
{
  "id": 1,
  "user_id": 1,
  "comment_id": 1,
  "vote_type": 1,
  "created_at": "string"
}
```

`GET /comments/{comment_id}/vote`

Auth: required

Response:
```json
{
  "vote_type": 1
}
```

`DELETE /comments/{comment_id}/vote`

Auth: required

Response:
```json
{
  "vote_type": 0
}
```

## Notifications

`GET /notifications`

Auth: required

Request params:
- `skip`: integer (optional, default: 0)
- `limit`: integer (optional, default: 20, max: 100)

Response:
```json
[
  {
    "id": 1,
    "user_id": 1,
    "actor_id": 1,
    "actor_username": "string",
    "type": "string",
    "message": "string",
    "read": false,
    "post_id": "integer | null",
    "comment_id": "integer | null",
    "created_at": "string"
  }
]
```

`PUT /notifications/{notification_id}/read`

Auth: required

Response:
```json
{
  "message": "string"
}
```

`GET /notifications/unread/count`

Auth: required

Response:
```json
{
  "unread_count": 0
}
```

## Health

`GET /`

Response:
```json
{
  "message": "Hacker News Clone API",
  "version": "1.0.0"
}
```
