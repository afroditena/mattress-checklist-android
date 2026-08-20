# 매트리스 영업 체크리스트 Android 앱

영업상담·지인소개 체크리스트를 인터넷 없이 실행할 수 있도록 Android WebView 앱으로 구성한 프로젝트입니다.

## APK 바로 받기
이 브랜치에 푸시될 때마다 GitHub Actions가 자동으로 APK를 빌드해서
[Releases](../../releases) 페이지에 올려둡니다. 가장 최근 릴리스에서
`app-debug.apk`를 휴대폰으로 내려받아 설치하면 됩니다 (Android Studio 불필요).

## Android Studio에서 APK 만들기
1. Android Studio에서 이 폴더를 엽니다.
2. Gradle Sync가 완료될 때까지 기다립니다.
3. 메뉴에서 **Build > Build Bundle(s) / APK(s) > Build APK(s)**를 선택합니다.
4. 생성 파일: `app/build/outputs/apk/debug/app-debug.apk`

## 휴대폰 설치
APK를 휴대폰으로 옮긴 뒤 파일을 누르고, 요청 시 **이 출처의 앱 허용**을 켜서 설치합니다.

## 특징
- **상담 체크리스트**: 고객 니즈 파악(선호 경도, 예산, 통증 여부 등)부터 제품 설명·가격·배송 안내까지 빠뜨리지 않도록 체크
- **지인 소개 관리**: 소개자·피소개인 정보와 감사 인사·리워드 안내·첫 연락·상담 일정 협의 여부를 기록
- 오프라인 실행, 서버 및 개인정보 전송 없음
- 완료/미완료 자동 집계, 입력 내용 자동 보존
- 결과 복사, 인쇄, 초기화
