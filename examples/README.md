### Example cURL reqest flow

In **development** start the app

```
./run_development.sh
```

then you should be able to do:

```curl -i -H "Authorization: Bearer development-oauth-access-token" http://0.0.0.0:3103/data-sets```

In **production** curl requests should look something like this:

```curl -i -H "Authorization: Bearer <SIGNON_API_USER_TOKEN>" https://stagecraft.performance.service.gov.uk/data-sets/<name_of_data_set>```

