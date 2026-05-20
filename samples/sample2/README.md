# Ethical Hacking: CTF Challenge

## Challenge Description

A corporate intranet web portal (Node.js) with a backend PostgreSQL database. The challenge involves discovering exposed services, exploiting a Path Traversal vulnerability to retrieve database credentials, and accessing the database to retrieve the flag.

The challenge can be run with `docker compose up -d`.

## Solution

### Step 1: Port Scanning

Scan the target to discover open services:

```sh
nmap -sV -p- <TARGET_IP>
```

This reveals that port 80 (HTTP) and port 5432 (PostgreSQL) are open.

### Step 2: Web Enumeration

Browse to `http://<TARGET_IP>` and explore the navigation links:
- `/?page=home.html`
- `/?page=about.html`
- `/?page=contact.html`

Notice the `?page=` parameter loads different content.

### Step 3: Path Traversal vulnerability

Test by passing in different `path` parameters to read server files:

```sh
curl "http://<TARGET_IP>/?page=../package.json"
```

This gives a note that the database configuration is stored in the file `db-config.js`:

```sh
curl "http://<TARGET_IP>/?page=../db-config.json"
```

This reveals database credentials in `db-config.js`.

### Step 4: Database Access

Connect to PostgreSQL using the stolen credentials:

```sh
psql -h <TARGET_IP> -p 5432 -U <DATABASE_USERNAME> -d intranet_db
```

Query the database for the flag:

```sql
SELECT * FROM system_config;
```

## Hints

**Hint 1**: What happens when you try to access a web page that does not exist?

**Hint 2:** Web applications built with Node.js (such as Express) always have a `package.json` file listing their dependencies.

## Additional Tools

To connect to the PostgreSQL database, the `postgresql` package is needed in order to use the `psql` command:
```sh
apt install postgresql
```
(it is already available on the VMs)
