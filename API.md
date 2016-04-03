API Spec
========

### Create a new user

    POST /api/users/

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

    POST /api/sessions/

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

### User data

    GET /api/user

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
