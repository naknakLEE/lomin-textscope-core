# 준비 사항

- docker (>=20.10.12)
- docker-compose (>=1.19.2)
- nvidia-docker (>=2.9.1)
- nvidia-driver
- nvidia-container-toolkit
- python3 (>=3.8, <3.9)

# 퀵스타트
```
1. unzip textscope.zip && cd textscope/assets 
2. sh deploy-setup.sh ../images/ # 도커 이미지 로드
3. sh run.sh run # 텍스트스코프 서비스 실행
```

# 설치 스크립트

- `sh deploy-setup.sh "도커 이미지가 있는 디렉토리 경로"`

# 실행 스크립트

- `sh run.sh [command]`

  ```
  command options

  run: Run service to foreground
  run-bg: Run service to background
  stop: Stop service
  clean: Cleanup all service-related data
  ```

# 로그 확인법

- `docker-compose logs -f`

# API 사용법

- {} 괄호가 쳐져 있는 부분을 수정하여 터미널에 명령어 입력
- token 발급 받기
  ```
    curl -X 'POST' \
      'http://localhost:8050/api/v1/auth' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/x-www-form-urlencoded' \
      -d 'email=guest%40lomin.ai&password=guest'
  ```
  - 응답으로 터미널에 access_token의 값을 저장하고 있다가 ocr 요청할 때 사용
- image 등록 하기
  ```
    curl -X 'POST' \
      'http://localhost:8050/image' \
      -H 'accept: application/json' \
      -H 'x-request-id: test' \
      -H 'Content-Type: multipart/form-data' \
      -F 'image_id={고유한 이미지 아이디}' \
      -F 'image_type=inference' \
      -F 'description=' \
      -F 'file=@{이미지 경로};type=image/{이미지 확장자}'
  ```
- ocr 요청 하기
  ```
    curl -X 'POST' \
      'http://localhost:8050/task/inference/gocr' \
      -H 'accept: application/json' \
      -H 'x-request-id: test' \
      -H 'Authorization: Bearer {발급받은 토큰}' \
      -H 'Content-Type: application/json' \
      -d '{
      "task_id": {고유한 문자열 입력},
      "image_id": {등록한 이미지 아이디},
      "rectify": {
        "rotation_90n": false,  # 90도 단위 이미지 회전 보정 옵션
        "rotation_fine": false  # n(1~89)도 단위 이미지 회전 보정 옵션
      },
      "detection_score_threshold": 0.5,
      "use_text_extraction": false,
      "detection_resize_ratio": 1
    }'
  ```
