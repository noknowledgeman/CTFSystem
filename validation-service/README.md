# Validation Service

# Setup

```bash
docker compose up -d
```

Go to http://localhost:8000/ to setup a ctf and an admin account. In this admin account you can go to the /settings page and generate a new access token. You can paste this access token into the .evn under 

```
VAL_CTFD_API_TOKEN=replace-with-ctfd-admin-api-token
```

And then run:

```bash
docker compose up -d --force-recreate validation-service
```

To load the .env into the validation service image.
