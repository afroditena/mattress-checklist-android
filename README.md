# 매트리스 점검 체크리스트 Android 앱

웹 체크리스트를 인터넷 없이 실행할 수 있도록 Android WebView 앱으로 구성한 프로젝트입니다.

## Android Studio에서 APK 만들기
1. Android Studio에서 이 폴더를 엽니다.
2. Gradle Sync가 완료될 때까지 기다립니다.
3. 메뉴에서 **Build > Build Bundle(s) / APK(s) > Build APK(s)**를 선택합니다.
4. 생성 파일: `app/build/outputs/apk/debug/app-debug.apk`

## 휴대폰 설치
APK를 휴대폰으로 옮긴 뒤 파일을 누르고, 요청 시 **이 출처의 앱 허용**을 켜서 설치합니다.

## 특징
- 오프라인 실행
- 예/아니요 자동 집계
- 고객명·점검일 및 응답 자동 보존
- 결과 복사, 인쇄, 초기화
- 서버 및 개인정보 전송 없음
