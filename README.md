# slack-bot-study
study slack bot project.

## how to start

first, install libraries.

```shell
pip install -r requirements.txt
```

second, put in `config-template.json` file's contents, and change file's name -> `config-template.json` to `config.json`.
these contents are at [this site](https://api.slack.com/apps).

```json
{
  "slack_token": "xoxb-bottokentohere",
  "slack_client_id": "client.id",
  "slack_client_secret": "clientsecret",
  "slack_verification": "verification"
}
```

finally, open server.

```
python main.py
```

done!
