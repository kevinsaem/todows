/**
 * 음성 입력 모듈 (Voice Input)
 *
 * Web Speech API를 사용하여 한국어 음성을 텍스트로 변환한다.
 * 변환된 텍스트는 TimeParser로 시간을 파싱하고, 폼 필드에 자동 입력한다.
 *
 * 의존성: time-parser.js (window.TimeParser)
 */

window.VoiceInput = (function() {
  'use strict';

  // --- 상태 변수 ---
  var recognition = null;
  var isRecording = false;
  var noSpeechTimer = null;          // 5초 무음 타이머
  var NO_SPEECH_TIMEOUT = 5000;      // 무음 감지 타임아웃 (ms)

  // --- 에러 메시지 (한국어) ---
  var MSG = {
    PERMISSION_DENIED: '마이크 권한이 필요합니다. 브라우저 설정에서 허용해 주세요',
    NO_SPEECH: '음성이 감지되지 않았습니다',
    RECOGNITION_ERROR: '인식하지 못했습니다. 다시 말씀해 주세요',
    NOT_SUPPORTED: '이 브라우저에서는 음성 입력을 지원하지 않습니다'
  };

  // --- DOM 헬퍼 ---

  /**
   * 음성 입력 영역의 Alpine.js recording 상태를 업데이트한다.
   * @param {boolean} state - 녹음 상태
   */
  function setRecordingState(state) {
    var voiceArea = document.getElementById('voice-input-area');
    if (voiceArea && voiceArea.__x) {
      voiceArea.__x.$data.recording = state;
    }
  }

  /**
   * 음성 미리보기 영역에 텍스트를 표시한다.
   * @param {string} text - 표시할 텍스트
   * @param {boolean} show - 표시 여부
   */
  function updatePreview(text, show) {
    var preview = document.getElementById('voice-preview');
    var previewText = document.getElementById('voice-preview-text');
    if (preview && previewText) {
      if (show) {
        preview.classList.remove('hidden');
        previewText.textContent = text;
      } else {
        preview.classList.add('hidden');
        previewText.textContent = '';
      }
    }
  }

  /**
   * 에러 메시지를 미리보기 영역에 표시한다.
   * @param {string} message - 에러 메시지
   */
  function showError(message) {
    var preview = document.getElementById('voice-preview');
    var previewText = document.getElementById('voice-preview-text');
    if (preview && previewText) {
      preview.classList.remove('hidden');
      // 에러 스타일로 변경
      preview.classList.remove('bg-blue-50', 'text-blue-700');
      preview.classList.add('bg-red-50', 'text-red-600');
      previewText.textContent = message;

      // 3초 후 에러 스타일 복원 및 숨김
      setTimeout(function() {
        preview.classList.remove('bg-red-50', 'text-red-600');
        preview.classList.add('bg-blue-50', 'text-blue-700');
        preview.classList.add('hidden');
        previewText.textContent = '';
      }, 3000);
    }
  }

  /**
   * 무음 타이머를 초기화한다.
   * 음성이 감지되면 타이머를 리셋하고, 5초 동안 무음이면 자동 종료한다.
   */
  function resetNoSpeechTimer() {
    clearNoSpeechTimer();
    noSpeechTimer = setTimeout(function() {
      if (isRecording) {
        stop();
        showError(MSG.NO_SPEECH);
      }
    }, NO_SPEECH_TIMEOUT);
  }

  /**
   * 무음 타이머를 해제한다.
   */
  function clearNoSpeechTimer() {
    if (noSpeechTimer) {
      clearTimeout(noSpeechTimer);
      noSpeechTimer = null;
    }
  }

  // --- 핵심 기능 ---

  /**
   * Web Speech API 지원 여부 확인
   * @returns {boolean}
   */
  function isSupported() {
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  /**
   * SpeechRecognition 인스턴스를 생성하고 이벤트를 바인딩한다.
   * @returns {boolean} 초기화 성공 여부
   */
  function init() {
    if (!isSupported()) {
      console.warn('[VoiceInput] Web Speech API를 지원하지 않는 브라우저입니다.');
      return false;
    }

    var SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognitionAPI();
    recognition.lang = 'ko-KR';
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    // --- 이벤트 핸들러 ---

    recognition.onstart = function() {
      isRecording = true;
      console.log('[VoiceInput] 녹음 시작');
      setRecordingState(true);
      updatePreview('듣고 있습니다...', true);
      resetNoSpeechTimer();
    };

    recognition.onresult = function(event) {
      // 음성이 감지되었으므로 무음 타이머 리셋
      resetNoSpeechTimer();

      var interimTranscript = '';
      var finalTranscript = '';

      for (var i = event.resultIndex; i < event.results.length; i++) {
        var transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      // 중간 결과 실시간 표시
      if (interimTranscript) {
        updatePreview(interimTranscript, true);
      }

      // 최종 결과 처리
      if (finalTranscript) {
        clearNoSpeechTimer();
        applyToForm(finalTranscript);
      }
    };

    recognition.onerror = function(event) {
      console.error('[VoiceInput] 오류:', event.error);
      clearNoSpeechTimer();
      isRecording = false;
      setRecordingState(false);

      switch (event.error) {
        case 'not-allowed':
          showError(MSG.PERMISSION_DENIED);
          break;
        case 'no-speech':
          showError(MSG.NO_SPEECH);
          break;
        default:
          showError(MSG.RECOGNITION_ERROR);
          break;
      }
    };

    recognition.onend = function() {
      console.log('[VoiceInput] 녹음 종료');
      clearNoSpeechTimer();
      isRecording = false;
      setRecordingState(false);
    };

    return true;
  }

  /**
   * 녹음 시작
   * 마이크 권한을 요청하고, 음성 인식을 시작한다.
   */
  function start() {
    if (!isSupported()) {
      showError(MSG.NOT_SUPPORTED);
      return;
    }

    // 매 시작마다 새 인스턴스 생성 (이전 세션 상태 간섭 방지)
    if (!recognition) {
      if (!init()) return;
    }

    // 이미 녹음 중이면 중지
    if (isRecording) {
      stop();
      return;
    }

    // 미리보기 스타일 초기화 (에러 표시 후 다시 시도할 때)
    var preview = document.getElementById('voice-preview');
    if (preview) {
      preview.classList.remove('bg-red-50', 'text-red-600');
      preview.classList.add('bg-blue-50', 'text-blue-700');
    }

    try {
      recognition.start();
    } catch (e) {
      console.error('[VoiceInput] 시작 실패:', e);
      // 이전 recognition이 아직 실행 중일 수 있으므로 재생성
      recognition = null;
      if (init()) {
        try {
          recognition.start();
        } catch (e2) {
          console.error('[VoiceInput] 재시작 실패:', e2);
          showError(MSG.RECOGNITION_ERROR);
        }
      }
    }
  }

  /**
   * 녹음 수동 중지
   */
  function stop() {
    clearNoSpeechTimer();
    if (recognition && isRecording) {
      recognition.stop();
    }
  }

  /**
   * 인식 결과를 TimeParser로 파싱하고 폼 필드에 반영한다.
   * @param {string} text - 인식된 텍스트
   */
  function applyToForm(text) {
    // TimeParser로 시간/제목 분리
    var parsed;
    if (window.TimeParser && typeof window.TimeParser.parse === 'function') {
      parsed = window.TimeParser.parse(text);
    } else {
      // TimeParser가 없으면 전체 텍스트를 제목으로
      parsed = { title: text.trim(), time: null };
    }

    // 파싱 결과 미리보기 표시
    var previewMsg = '✓ ' + parsed.title;
    if (parsed.time) {
      previewMsg += ' (' + parsed.time + ')';
    }
    updatePreview(previewMsg, true);

    // 폼 필드에 값 설정
    var titleInput = document.getElementById('form-title');
    if (titleInput) {
      titleInput.value = parsed.title;
      // Alpine.js x-model 동기화를 위해 input 이벤트 발생
      titleInput.dispatchEvent(new Event('input', { bubbles: true }));
    }

    var timeInput = document.getElementById('form-time');
    if (timeInput && parsed.time) {
      timeInput.value = parsed.time;
      timeInput.dispatchEvent(new Event('input', { bubbles: true }));
    }

    // 3초 후 미리보기 숨김
    setTimeout(function() {
      updatePreview('', false);
    }, 3000);
  }

  // --- 공개 API ---
  return {
    isSupported: isSupported,
    start: start,
    stop: stop,
    isRecording: function() { return isRecording; }
  };
})();
