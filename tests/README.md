# 구성
## 테스트 유형 구분
1. integration: 통합 API 테스트
1. api: 특정 API 각각의 테스트

## 고객사 구분
1. `./common` : 고객사 구분 없이 공통적으로 필요한 테스트코드
1. `./bsn_2207_lina` : 특정 고객사에만 필요한 테스트코드 예시

# 실행 커맨드 예시
```
cd {project_root}/tests
pytest common bsn_2207_lina
```

# 가이드 문서
> [Test Code 작성 (노션 이동)](https://www.notion.so/lomin/Test-Code-e5e6f852ca464ee0aa64b4576cbaf4f2#deb84b370eef472f904f2133d6cac676)