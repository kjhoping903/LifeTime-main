# LifeTime 공공데이터 필드 매핑

## 응급의료기관

원천은 공공데이터포털의 `국립중앙의료원_전국 응급의료기관 정보 조회 서비스` 중 `응급의료기관 목록정보 조회` 응답이다. 아래 매핑은 2026-10-20에 실제 응답 10건에서 확인한 필드만 사용한다.

| LifeTime 필드 | 원본 필드 | 처리 방식 | 확인 상태 |
| --- | --- | --- | --- |
| `facility_type` | 해당 없음 | 고정값 `emergency_room` | 확인 |
| `source_id` | `hpid` | 값이 없으면 해당 항목 제외 | 확인 |
| `name` | `dutyName` | 빈 값은 `null` | 확인 |
| `address` | `dutyAddr` | 빈 값은 `null` | 확인 |
| `latitude` | `wgs84Lat` | WGS84 숫자형, 범위 밖이거나 변환 불가하면 `null` | 확인 |
| `longitude` | `wgs84Lon` | WGS84 숫자형, 범위 밖이거나 변환 불가하면 `null` | 확인 |
| `contact_phone` | `dutyTel1` | 빈 값은 `null` | 확인 |
| `emergency_phone` | `dutyTel3` | 빈 값은 `null` | 확인 |
| `source_name` | 해당 없음 | 공공데이터 서비스명 고정값 | 확인 |
| `source_updated_at` | 미확인 | 목록 응답에 갱신일 필드가 없어 `null` | 미확인 |
| `data_collected_at` | 해당 없음 | 변환 시점의 UTC ISO 8601 값 | 확인 |

실제 목록 응답에서 추가로 `dutyEmcls`, `dutyEmclsName`, `phpid`, `rnum`을 확인했으나 현재 LifeTime 정규화 샘플에는 포함하지 않는다. 응급실 수용 가능 여부는 이 목록 응답으로 판단하지 않는다.
