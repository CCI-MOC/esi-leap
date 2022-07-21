### DB Migration

#### Create a DB revision
1. Change the data models in `models.py`.
2. Run `esi-leap-dbsync revision -m "xxx" --autogenerate`.
3. Note: `autogenerate` may not detect the changes. See [details](https://alembic.sqlalchemy.org/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-not-detect) here. You can adjust the migration script manually based on your data model changes.

#### Upgrade
`esi-leap-dbsync upgrade --revision <id>`

#### Downgrade
`esi-leap-dbsync downgrade --revision <id>`

#### Version
`esi-leap-dbsync version`

#### Stamp
`esi-leap-dbsync stamp --revision <id>`
