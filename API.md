# Users

### Create a new user

```http
POST /api/users/
```

```json
{
  "username": "tyler_durden",
  "password": "dQw4w9WgXcQ"
}
```

**Request**

```json
{
  "key": "9bZkp7q19f0.KmtzQCSh6xk"
}
```

### Login as a user

```http
POST /api/sessions/
```

```json
{
  "username": "tyler_durden",
  "password": "dQw4w9WgXcQ"
}
```

**Response**

```json
{
  "key": "KmtzQCSh6xk.9bZkp7q19f0"
}
```

### View authenticated user

```http
GET /api/user
```

**Response**

```json
{
  "username": "tyler_durden",
  "team": {
    "id": 1,
    "name": "Fight Club"
  }
}
```

# Teams

### List teams, ranked by score

```http
GET /api/teams/
```

**Response**

```json
{
  "teams": [
    {
      "id": 1,
      "name": "Fight Club",
      "points": 1024
    },
    {
      "id": 2,
      "name": "Police Department",
      "points": 0
    }
  ]
}
```

### View a team

```http
GET /api/teams/1
GET /api/team
```

**Response**

```json
{
  "id": 1,
  "name": "Fight Club"
}
```

### Create a team

```http
POST /api/teams/
```

```json
{
  "name": "Fight Club"
}
```

**Response**

```json
{
  "id": 1,
  "name": "Fight Club"
}
```

### Invite another user to your team

```http
POST /api/team/members/
```

```json
{
  "username": "robert_paulson"
}
```

**Response**

```http
HTTP/2.0 204 No Content
```

### List teams you've been invited to

```http
POST /api/teams/invited
```

```json
{
  "teams": [
    {
      "id": 2,
      "name": "Police Department"
    }
  ]
}
```

**Response**

```http
HTTP/2.0 204 No Content
```

### Join a team

```http
PATCH /api/user
```

```json
{
  "team": 1
}
```

**Response**

```http
HTTP/2.0 204 No Content
```

### Leave team

```http
DELETE /api/team
```

**Response**

```http
HTTP/2.0 204 No Content
```
