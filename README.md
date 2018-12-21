# my-friend-briefer

**My friend, Briefer(내 친구 브리퍼)**는 아침 9시마다 오늘의 날씨, 뉴스, 일정을 브리핑해주는 슬랙 챗봇입니다!

<p align="center">
  <img src="https://user-images.githubusercontent.com/6284140/50320829-7d859480-0511-11e9-8b9e-8f9e3d6fbc1b.png" width="500">
</p>


## how to install

먼저, 라이브러리를 설치합니다.

```shell
pip install -r requirements.txt
```

두번째로, `config-template.json` 파일의 이름을 `config.json`으로 변경한 후, 내용을 양식에 맞게 변경합니다.
토큰과 유효값은 [슬랙 API 사이트](https://api.slack.com/apps)에서 확인하실 수 있습니다.

```json
{
  "slack_token": "xoxb-로 시작하는 토큰 입력",
  "slack_verification": "bot의 유효값 입력"
}
```

마지막으로, 서버를 실행하고, 테스트를 해봅니다.

```
python main.py
```


## collaborators

- Han SangWoo([github](https://www.github.com/tkddn204))
- Park Shin Jong
- Yoon Hyun Gyu


## License
[MIT](https://github.com/tkddn204/my-friend-briefer/blob/master/LICENSE)
