const DEFAULT_ERROR_CODES = {
  400: '请求参数/格式有问题',
  401: '没登录或 token/key 无效',
  403: '没权限或被禁止',
  413: '请求体太大',
  502: '网关拿到上游错误响应',
  503: '服务当前不可用，通常是临时状态',
  504: '网关等上游超时',
};

const DEFAULT_API_BASE = location.hostname === '127.0.0.1' || location.hostname === 'localhost'
  ? 'http://127.0.0.1:8767'
  : '';

const form = document.querySelector('#probe-form');
const submit = document.querySelector('#submit');
const errorCodes = document.querySelector('#error-codes');
const results = document.querySelector('#results');
const resultTitle = document.querySelector('#result-title');
const recommended = document.querySelector('#recommended');

function escapeHtml(input = '') {
  return String(input).replace(/[&<>"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]));
}

function renderErrorCodes(data) {
  errorCodes.innerHTML = Object.entries(data).map(([code, text]) => `
    <article class="error-card"><strong>${code}</strong><span>${escapeHtml(text)}</span></article>
  `).join('');
}

function getApiBase() {
  const input = form.elements.api_base;
  return (input?.value || DEFAULT_API_BASE).trim().replace(/\/$/, '');
}

async function loadErrorCodes() {
  form.elements.api_base.value = DEFAULT_API_BASE;
  renderErrorCodes(DEFAULT_ERROR_CODES);
  const apiBase = getApiBase();
  if (!apiBase) return;
  const res = await fetch(`${apiBase}/api/error-explanations`);
  renderErrorCodes(await res.json());
}

function modelLines(text) {
  return text.split('\n').map(line => line.trim()).filter(Boolean);
}

function renderReport(report) {
  resultTitle.textContent = `${report.name} · ${report.models_ok ? 'models OK' : 'models failed'}`;
  recommended.textContent = report.recommended_model ? `推荐：${report.recommended_model}` : '暂无可推荐模型';
  results.innerHTML = report.results.map(item => `
    <article class="result-card ${item.ok ? 'ok' : 'fail'}">
      <h3>${escapeHtml(item.model)}</h3>
      <p class="${item.ok ? 'good' : 'bad'}">${item.ok ? '可用' : escapeHtml(item.error || '不可用')}</p>
      <p class="meta">HTTP: ${item.status_code ?? '-'} · ${Number(item.latency_ms).toFixed(0)}ms</p>
    </article>
  `).join('') || `<p>没有模型结果。/v1/models：${escapeHtml(report.models_error || '无')}</p>`;
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  const data = new FormData(form);
  const apiBase = getApiBase();
  if (!apiBase) {
    resultTitle.textContent = '需要后端 API URL';
    results.innerHTML = '<p class="bad">GitHub Pages 只能托管静态前端。请先填写一个可访问的 ModelPulse API 地址，例如 http://127.0.0.1:8767。</p>';
    return;
  }
  const payload = {
    name: data.get('name'),
    base_url: data.get('base_url'),
    api_key: data.get('api_key'),
    models: modelLines(data.get('models') || ''),
  };
  submit.disabled = true;
  submit.textContent = '测速中...';
  resultTitle.textContent = '测速中';
  recommended.textContent = '';
  results.innerHTML = '<p>正在请求 /v1/models 和 /v1/chat/completions...</p>';
  try {
    const res = await fetch(`${apiBase}/api/probe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`API ${res.status}`);
    renderReport(await res.json());
  } catch (err) {
    resultTitle.textContent = '测速失败';
    results.innerHTML = `<p class="bad">${escapeHtml(err.message)}</p>`;
  } finally {
    submit.disabled = false;
    submit.textContent = '开始测速';
  }
});

loadErrorCodes().catch(err => {
  renderErrorCodes(DEFAULT_ERROR_CODES);
  console.warn('Remote error-code API unavailable, using static fallback.', err);
});
