/**
 * 시간 파싱 모듈 (Time Parser)
 *
 * 한국어 음성 텍스트에서 시간 정보를 추출하고 제목과 분리한다.
 *
 * 파싱 규칙 (func-spec.md F-06 기준):
 *   "10시에 피자집 가기"    → { title: "피자집 가기", time: "10:00" }
 *   "오후 3시 회의"         → { title: "회의", time: "15:00" }
 *   "오전 9시 반 운동"      → { title: "운동", time: "09:30" }
 *   "2시 30분에 병원"       → { title: "병원", time: "14:30" }
 *   "장보기"               → { title: "장보기", time: null }
 */

window.TimeParser = (function() {
  'use strict';

  /**
   * 시간 문자열을 "HH:MM" 형식으로 포맷한다.
   * @param {number} hour - 시 (0-23)
   * @param {number} minute - 분 (0-59)
   * @returns {string} "HH:MM" 형식
   */
  function formatTime(hour, minute) {
    return String(hour).padStart(2, '0') + ':' + String(minute).padStart(2, '0');
  }

  /**
   * 모호한 시간(오전/오후 지정 없음)을 현재 시각 기준으로 가까운 미래로 결정한다.
   * 예: 현재 14시인데 "3시"라고 하면 → 15시(오후 3시)
   * @param {number} hour - 1~12 범위의 시
   * @returns {number} 0~23 범위의 24시간 형식 시
   */
  function resolveAmbiguousHour(hour) {
    var now = new Date();
    var currentHour = now.getHours();
    var currentMinute = now.getMinutes();

    // hour가 이미 13 이상이면 모호하지 않음
    if (hour >= 13) return hour;

    // 오전(hour) vs 오후(hour+12) 중 현재보다 가까운 미래 선택
    var amHour = hour;           // 예: 3 → 3시
    var pmHour = hour + 12;      // 예: 3 → 15시

    // 12시는 특수: 오전 0시(자정) vs 오후 12시(정오)
    if (hour === 12) {
      amHour = 0;
      pmHour = 12;
    }

    var currentTotal = currentHour * 60 + currentMinute;
    var amTotal = amHour * 60;
    var pmTotal = pmHour * 60;

    // 미래 시간만 고려 (현재 이후)
    var amFuture = amTotal > currentTotal;
    var pmFuture = pmTotal > currentTotal;

    if (amFuture && pmFuture) {
      // 둘 다 미래면 더 가까운 쪽
      return (amTotal - currentTotal) <= (pmTotal - currentTotal) ? amHour : pmHour;
    } else if (amFuture) {
      return amHour;
    } else if (pmFuture) {
      return pmHour;
    } else {
      // 둘 다 과거면 내일 오전으로 (가장 가까운 미래)
      return amHour;
    }
  }

  /**
   * 텍스트에서 시간과 제목을 분리한다.
   * @param {string} text - 음성 인식 또는 사용자 입력 텍스트
   * @returns {{ title: string, time: string|null }}
   */
  function parse(text) {
    if (!text || typeof text !== 'string') {
      return { title: '', time: null };
    }

    text = text.trim();
    if (!text) {
      return { title: '', time: null };
    }

    // 시간 패턴 정규식
    // 매치 그룹: (오전|오후)? + (숫자)시 + (반|(숫자)분)? + (에)?
    // 다양한 패턴을 하나의 정규식으로 처리
    var timeRegex = /(오전|오후)?\s*(\d{1,2})\s*시\s*(?:(반)|(\d{1,2})\s*분?)?\s*(에)?/;

    var match = text.match(timeRegex);

    if (!match) {
      // 시간 패턴이 없으면 전체 텍스트를 제목으로
      return { title: text, time: null };
    }

    var period = match[1];       // "오전" 또는 "오후" 또는 undefined
    var hourRaw = parseInt(match[2], 10);  // 시
    var isHalf = !!match[3];     // "반" 여부
    var minuteRaw = match[4] ? parseInt(match[4], 10) : 0;  // 분
    var minute = isHalf ? 30 : minuteRaw;

    // 유효성 검사
    if (hourRaw < 0 || hourRaw > 24 || minute < 0 || minute > 59) {
      return { title: text, time: null };
    }

    // 시간 결정
    var hour;
    if (period === '오후') {
      // 오후: 12시는 그대로, 1~11시는 +12
      hour = (hourRaw === 12) ? 12 : hourRaw + 12;
    } else if (period === '오전') {
      // 오전: 12시는 0, 나머지는 그대로
      hour = (hourRaw === 12) ? 0 : hourRaw;
    } else {
      // 오전/오후 미지정 → 가까운 미래 시간으로 결정
      hour = resolveAmbiguousHour(hourRaw);
    }

    // 24시간 범위 제한
    if (hour > 23) hour = 23;

    var time = formatTime(hour, minute);

    // 제목 추출: 시간 관련 부분을 제거
    var title = text.replace(timeRegex, ' ').trim();

    // 제목이 비어있으면 원본 텍스트 사용
    if (!title) {
      title = text;
    }

    return { title: title, time: time };
  }

  return {
    parse: parse
  };
})();
