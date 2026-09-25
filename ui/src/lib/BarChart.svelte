<script>
  export let distribution = [];
  export let threshold = 0;

  const slot = 46;
  const height = 300;
  const padTop = 92;
  const padBottom = 30;

  $: width = Math.max(360, distribution.length * slot + 24);
  $: maxP = Math.max(...distribution.map((d) => d.decimal), 1e-12);
  $: bars = distribution.map((d, i) => {
    const h = Math.max((d.decimal / maxP) * (height - padTop - padBottom), 1);
    return { ...d, x: 12 + i * slot, h, y: height - padBottom - h };
  });
</script>

<div class="chart-scroll">
  <svg {width} {height} viewBox="0 0 {width} {height}" role="img" aria-label="总分概率分布柱状图">
    <line class="axis" x1="0" y1={height - padBottom} x2={width} y2={height - padBottom} />
    {#each bars as b (b.total)}
      <rect
        data-testid={`bar-${b.total}`}
        data-probability={`${b.num}/${b.den}`}
        class:hit={b.total >= threshold}
        x={b.x + 5}
        y={b.y}
        width={slot - 12}
        height={b.h}
      >
        <title>总分 {b.total}：{b.num}/{b.den} ≈ {(b.decimal * 100).toFixed(2)}%</title>
      </rect>
      <text
        data-testid={`bar-label-${b.total}`}
        class="frac"
        transform={`rotate(-55 ${b.x + slot / 2} ${b.y - 8})`}
        x={b.x + slot / 2}
        y={b.y - 8}
      >{b.num}/{b.den}</text>
      <text class="total" x={b.x + slot / 2} y={height - padBottom + 18}>{b.total}</text>
    {/each}
  </svg>
</div>
<p class="legend">
  <span class="swatch hit"></span> 总分 ≥ 阈值 {threshold}
  <span class="swatch"></span> 其余总分（柱上为约分分数概率）
</p>

<style>
  .chart-scroll {
    overflow-x: auto;
  }
  svg {
    display: block;
  }
  .axis {
    stroke: #9aa3b2;
    stroke-width: 1;
  }
  rect {
    fill: #9db8e8;
  }
  rect.hit {
    fill: #2f6fdd;
  }
  .frac {
    font-size: 10px;
    fill: #5a6272;
    text-anchor: end;
    font-variant-numeric: tabular-nums;
  }
  .total {
    font-size: 11px;
    fill: #1f2430;
    text-anchor: middle;
  }
  .legend {
    font-size: 12px;
    color: #5a6272;
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 8px 0 0;
  }
  .swatch {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 3px;
    background: #9db8e8;
    margin-left: 10px;
  }
  .swatch.hit {
    background: #2f6fdd;
    margin-left: 0;
  }
</style>
