# BITAmin_Multimodal

17, 18기 BITAmin 여름방학 멀티모달 프로젝트

데이터셋은 Git이 아닌 **DVC(Data Version Control)** 로 관리하며, 실제 파일은 **Google Drive** 원격 저장소에 저장되어 있습니다.
Git에는 메타데이터(`data.dvc`)만 올라가고, 실제 `data/` 폴더는 `.gitignore` 처리되어 있으니 **절대 `git add data/` 하지 마세요.**

---

## 📊 데이터 개요

| 항목 | 내용 |
|---|---|
| 경로 | `data/` (Git 추적 제외) |
| 용량 | 약 6.6 GB |
| 파일 수 | 22,046개 |
| 원격 저장소 | Google Drive (`myremote`) |
| 추적 파일 | `data.dvc` |

---

## 🚀 처음 세팅하는 팀원용 가이드

### 0. 사전 준비 (팀장에게 요청할 것)

`dvc pull` 전에 아래 두 가지가 반드시 필요합니다. 팀장에게 요청하세요.

1. **본인 Google 계정을 Drive 폴더에 공유 요청** (뷰어 권한 이상)
   - 공유가 안 되어 있으면 인증은 통과해도 파일을 못 받습니다.
2. **`gdrive_client_secret` 값 전달받기**
   - 이 값은 보안상 GitHub에 올라가 있지 않습니다 (`.dvc/config`에는 `client_id`만 있음).
   - **카카오톡/슬랙 DM 등 비공개 채널로만 공유**하고, 절대 Git에 커밋하지 마세요.

---

### 1. 저장소 클론

```bash
git clone https://github.com/scuty31/BITAmin_Multimodal.git
cd BITAmin_Multimodal
```

### 2. 패키지 설치

```bash
pip install dvc dvc-gdrive
```

> 가상환경(conda/venv) 안에서 설치하는 것을 권장합니다.

### 3. Client Secret 로컬 등록 ⚠️ 필수

전달받은 secret을 **`--local` 옵션으로** 등록합니다.
`--local`을 붙이면 `.dvc/config.local`에 저장되며, 이 파일은 Git에 올라가지 않습니다.

```bash
dvc remote modify myremote --local gdrive_client_secret "전달받은_secret_문자열"
```

설정 확인:

```bash
cat .dvc/config.local     # secret이 들어있는지 확인
git status                # config.local이 안 잡히는지 확인 (안 잡히는 게 정상)
```

### 4. 데이터 내려받기

```bash
dvc pull
```

**최초 실행 시 Google 인증 절차**

1. 터미널에 Google 로그인 URL이 출력되고, 보통 브라우저가 자동으로 열립니다.
2. 폴더를 공유받은 **본인 Google 계정**으로 로그인합니다.
3. "Google에서 확인하지 않은 앱" 경고가 뜨면 → **[고급]** → **[dvc-app(으)로 이동(안전하지 않음)]** 클릭.
   (팀장이 직접 발급한 Google Cloud 프로젝트이므로 문제없습니다.)
4. 권한 허용 후 인증 토큰이 `.dvc/tmp/gdrive-user-credentials.json`에 저장되며, 이후에는 재인증 없이 동작합니다.

완료되면 `data/` 폴더에 원본 파일명 그대로 데이터가 채워집니다.

### 5. 확인

```bash
dvc status        # "Data and pipelines are up to date." 면 성공
du -sh data/      # 약 6.6G
```

---

## 🔄 데이터를 추가/수정했을 때 (DVC Push)

전처리 결과나 새 데이터를 팀에 공유할 때만 사용합니다. (Drive 폴더에 **편집자 권한**이 필요합니다.)

```bash
# 1. 변경된 data 폴더를 DVC에 다시 등록
dvc add data

# 2. 실제 파일을 Google Drive로 업로드
dvc push

# 3. 메타데이터만 Git에 커밋
git add data.dvc .gitignore
git commit -m "Data: update dataset (내용 요약)"
git push origin <본인_브랜치>
```

> ⚠️ `data.dvc`는 팀 전체가 공유하는 파일입니다. 데이터 구조를 바꾸는 push는 **팀에 미리 공지**해 주세요.
> 충돌 방지를 위해 `dvc push` 전에 `git pull` → `dvc pull`로 먼저 최신 상태를 맞추는 것을 권장합니다.

---

## 🧭 일상적인 작업 흐름

```bash
git pull            # 코드 + data.dvc 최신화
dvc pull            # 바뀐 데이터만 증분 다운로드
# ... 작업 ...
git add <코드파일> && git commit && git push
```

`git pull` 후 `data.dvc`가 변경되었다면 반드시 `dvc pull`을 함께 실행해야 데이터가 동기화됩니다.

---

## 🛠 트러블슈팅

<details>
<summary><b>연결 끊김 / 타임아웃 (WinError 10053, 10060 등)</b></summary>

동시 전송 개수가 많으면 방화벽이나 Google 측에서 비정상 트래픽으로 차단할 수 있습니다.
본인 환경에서만 병렬 수를 낮춰서 재시도하세요.

```bash
dvc remote modify myremote --local jobs 1
dvc pull
```
</details>

<details>
<summary><b>403 access_denied / 인증 실패</b></summary>

- `gdrive_client_secret`이 등록되어 있는지 확인: `cat .dvc/config.local`
- 로그인한 Google 계정이 Drive 폴더를 공유받은 계정과 같은지 확인
- 토큰이 꼬였다면 캐시된 인증 정보를 지우고 재인증:
  ```bash
  rm .dvc/tmp/gdrive-user-credentials.json
  dvc pull
  ```
</details>

<details>
<summary><b>SSH로 접속한 서버(GUI 없음)에서 인증이 안 될 때</b></summary>

브라우저를 띄울 수 없는 환경에서는, 로컬 PC에서 먼저 인증을 마친 뒤 생성된
`.dvc/tmp/gdrive-user-credentials.json`의 **내용**을 서버 환경변수로 넘겨줍니다.

```bash
export GDRIVE_CREDENTIALS_DATA='{ ...json 파일 내용 전체... }'
dvc pull
```
</details>

<details>
<summary><b>다운로드가 중간에 멈췄을 때</b></summary>

DVC는 이미 받은 파일을 건너뛰므로 그냥 다시 실행하면 이어받습니다.

```bash
dvc pull
```
캐시가 손상된 것 같다면 `dvc doctor`로 환경을 점검해 보세요.
</details>

<details>
<summary><b>실수로 secret을 공용 config에 넣었을 때</b></summary>

```bash
dvc remote modify myremote --unset gdrive_client_secret
dvc remote modify myremote --local gdrive_client_secret "secret"
```
이미 커밋했다면 GitHub Push Protection에 걸리며, 해당 커밋을 되돌리고
**secret을 반드시 재발급**해야 합니다.
</details>

---

## ⚠️ 주의사항 요약

- `data/` 폴더는 **절대 Git에 커밋하지 않습니다.**
- `.dvc/config.local`은 **절대 커밋하지 않습니다.** (secret 포함)
- 데이터를 지우고 싶을 땐 `rm -rf data/` 후 `dvc pull`로 언제든 복구 가능합니다.
