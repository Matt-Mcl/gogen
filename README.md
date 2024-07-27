Copy postgres files for container to use + create log file:
```bash
cp ~/.pgpass ./gogensite
cp ~/.pg_service.conf ./gogensite
touch ./gogensite/error.log
```

Ensure Postgres server is configured to allow connections from all hosts/docker containers. 
Done in Config file `/etc/postgresql/{Version}/main/postgresql.conf`

Also edit (/etc/postgresql/{Version}/main/pg_hba.conf) and include the line to allow docker to connect to postgres + allow gogen script to access postgres:
```
host all all 10.0.0.0/0 scram-sha-256
local all postgresmd5 md5
```

.env file structure:
```env
SECRET_KEY=<SECRET_KEY>
PG_PUZZLE_DBNAME=<PG_PUZZLE_DBNAME>
PG_PUZZLE_USER=<PG_PUZZLE_USER>
PG_PUZZLE_PASSWORD=<PG_PUZZLE_PASSWORD>
PG_DEV_DBNAME=<PG_DEV_DBNAME>
PG_TEST_DBNAME=<PG_TEST_DBNAME>
PG_USER=<PG_USER>
PG_PASSWORD=<PG_PASSWORD>
PG_HOST=<PG_HOST>
PG_PORT=<PG_PORT>
```

For tests:
```bash
sudo apt-get install chromium-browser
```

Run `/usr/bin/chromium-browser --version`

Get chrome driver that matches the installed chromium version:
`https://googlechromelabs.github.io/chrome-for-testing/` or `https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json` for a specific version `>` copy to `/usr/bin/chromedriver`
