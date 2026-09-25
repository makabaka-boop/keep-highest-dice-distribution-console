<script>
  import { onMount } from 'svelte';
  import BarChart from './lib/BarChart.svelte';

  // 规则参数
  let n = 3;
  let faces = 6;
  let keep = 2;
  let threshold = 12;
  let rerollSet = new Set();

  // 结果状态
  let result = null;
  let error = '';
  let loading = false;
  let timer = null;

  $: if (keep > n) keep = n;
  $: rerollFaces = Array.from({ length: faces }, (_, i) => i + 1);
  // 面数调小后，丢弃超出范围的重掷面
  $: rerollSet = new Set([...rerollSet].filter((v) => v <= faces));

  function toggleReroll(v) {
    const next = new Set(rerollSet);
    if (next.has(v)) next.delete(v);
    else next.add(v);
    rerollSet = next;
    schedule();
  }

  async function compute() {
    loading = true;
    error = '';
    try {
      const resp = await fetch('/api/distribution', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          n,
          faces,
          keep,
          threshold,
          reroll: [...rerollSet].sort((a, b) => a - b),
        }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || `HTTP ${resp.status}`);
      result = data;
    } catch (e) {
      error = e.message;
      result = null;
    } finally {
      loading = false;
    }
  }

  function schedule() {
    clearTimeout(timer);
    timer = setTimeout(compute, 150);
  }

  onMount(compute);
</script>

<main>
  <h1>骰池精确概率</h1>
  <p class="hint">
    每颗骰先掷一次，命中重掷面则恰好重掷一次；最终面为最大面时追加一颗附加骰并相加（附加骰不再重掷或追加）。
    最后从全部骰子中保留最高的 K 颗求和。所有概率均为精确约分分数。
  </p>

  <section class="panel form">
    <label>
      骰子数量（1~6）
      <input data-testid="input-n" type="number" min="1" max="6" bind:value={n} on:input={schedule} />
    </label>
    <label>
      面数（2~8）
      <input data-testid="input-faces" type="number" min="2" max="8" bind:value={faces} on:input={schedule} />
    </label>
    <label>
      保留颗数（1~{n}）
      <input data-testid="input-keep" type="number" min="1" max={n} bind:value={keep} on:input={schedule} />
    </label>
    <label>
      阈值
      <input data-testid="input-threshold" type="number" bind:value={threshold} on:input={schedule} />
    </label>
    <div class="reroll">
      <span>重掷面集合</span>
      <div class="chips">
        {#each rerollFaces as v (v)}
          <button
            type="button"
            class="chip"
            class:active={rerollSet.has(v)}
            data-testid={`reroll-${v}`}
            on:click={() => toggleReroll(v)}
          >{v}</button>
        {/each}
      </div>
    </div>
    <button class="compute" data-testid="compute" on:click={compute} disabled={loading}>
      {loading ? '计算中…' : '计算'}
    </button>
  </section>

  {#if error}
    <p class="error" data-testid="error">{error}</p>
  {/if}

  {#if result}
    <section class="panel stats">
      <div class="stat">
        <span class="label">期望总分</span>
        <span class="value" data-testid="expectation">{result.expectation.num}/{result.expectation.den}</span>
        <span class="decimal">≈ {result.expectation.decimal.toFixed(4)}</span>
      </div>
      <div class="stat">
        <span class="label">P(总分 ≥ {result.at_least.threshold})</span>
        <span class="value" data-testid="at-least">{result.at_least.num}/{result.at_least.den}</span>
        <span class="decimal">≈ {(result.at_least.decimal * 100).toFixed(2)}%</span>
      </div>
      <div class="stat">
        <span class="label">概率合计</span>
        <span class="value" data-testid="total-prob">{result.total_probability}</span>
        <span class="decimal">恒为 1</span>
      </div>
    </section>

    <section class="panel">
      <h2>总分分布</h2>
      <BarChart distribution={result.distribution} threshold={result.at_least.threshold} />
    </section>

    <details class="panel">
      <summary>原始分数响应（JSON）</summary>
      <pre data-testid="raw-json">{JSON.stringify(result, null, 2)}</pre>
    </details>
  {/if}
</main>

<style>
  :global(body) {
    margin: 0;
    font-family: 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
    background: #f4f5f7;
    color: #1f2430;
  }
  main {
    max-width: 960px;
    margin: 0 auto;
    padding: 24px 16px 48px;
  }
  h1 { font-size: 24px; margin: 8px 0; }
  h2 { font-size: 17px; margin: 0 0 12px; }
  .hint { color: #5a6272; font-size: 13px; line-height: 1.7; }
  .panel {
    background: #fff;
    border: 1px solid #e3e6eb;
    border-radius: 10px;
    padding: 16px;
    margin-top: 16px;
  }
  .form {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    align-items: flex-end;
  }
  .form label {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 13px;
    color: #5a6272;
  }
  .form input {
    width: 90px;
    padding: 7px 9px;
    border: 1px solid #c9cfd9;
    border-radius: 6px;
    font-size: 14px;
  }
  .reroll { display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: #5a6272; }
  .chips { display: flex; gap: 6px; }
  .chip {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    border: 1px solid #c9cfd9;
    background: #fff;
    cursor: pointer;
    font-size: 14px;
  }
  .chip.active {
    background: #2f6fdd;
    border-color: #2f6fdd;
    color: #fff;
  }
  .compute {
    padding: 9px 26px;
    border: none;
    border-radius: 6px;
    background: #2f6fdd;
    color: #fff;
    font-size: 14px;
    cursor: pointer;
  }
  .compute:disabled { opacity: 0.6; cursor: default; }
  .error { color: #c0392b; }
  .stats { display: flex; gap: 32px; flex-wrap: wrap; }
  .stat { display: flex; flex-direction: column; gap: 4px; }
  .stat .label { font-size: 12px; color: #5a6272; }
  .stat .value { font-size: 20px; font-weight: 600; font-variant-numeric: tabular-nums; }
  .stat .decimal { font-size: 12px; color: #8a93a5; }
  details summary { cursor: pointer; color: #5a6272; font-size: 13px; }
  pre {
    overflow: auto;
    font-size: 12px;
    background: #0f1420;
    color: #c8e1ff;
    padding: 12px;
    border-radius: 8px;
    max-height: 320px;
  }
</style>
