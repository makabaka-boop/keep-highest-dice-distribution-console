// 浏览器主流程：编辑规则 -> 画图 -> 核对图表与原始分数响应一致。
// 运行前：启动 ui（vite preview 或 compose 的 ui 容器）与 odds 服务。
//   UI_BASE_URL=http://localhost:8080 npx playwright test   # 对 compose
//   npx playwright test                                     # 默认 vite preview(4173)
import { test, expect } from '@playwright/test';

const PARAMS = { n: 3, faces: 4, keep: 2, reroll: [1], threshold: 6 };

test.describe('骰池概率主流程', () => {
  test('图表分数标签与原始响应一致，且与直接 API 响应一致', async ({ page, request }) => {
    await page.goto('/');

    // 编辑规则
    await page.getByTestId('input-n').fill(String(PARAMS.n));
    await page.getByTestId('input-faces').fill(String(PARAMS.faces));
    await page.getByTestId('input-keep').fill(String(PARAMS.keep));
    await page.getByTestId('input-threshold').fill(String(PARAMS.threshold));
    await page.getByTestId('reroll-1').click();

    // 点击计算并等待本次响应真正渲染到页面（避免读到上一次防抖计算的结果）
    const [resp] = await Promise.all([
      page.waitForResponse(
        (r) => r.url().includes('/api/distribution') && r.status() === 200
      ),
      page.getByTestId('compute').click(),
    ]);
    expect(resp.ok()).toBeTruthy();
    await expect(page.getByTestId('raw-json')).toContainText('"threshold": 6');
    await expect(page.getByTestId('raw-json')).toContainText('"reroll": [\n      1\n    ]');

    // 页面上的原始分数响应
    const rawText = await page.getByTestId('raw-json').textContent();
    const shown = JSON.parse(rawText);
    expect(shown.params).toEqual(PARAMS);

    // 直接调同一服务的 API（经 ui 容器/预览服务器反代，走真实 HTTP）
    const apiResp = await request.post('/api/distribution', { data: PARAMS });
    expect(apiResp.ok()).toBeTruthy();
    const direct = await apiResp.json();

    // 页面展示与直接 API 完全一致
    expect(shown.distribution).toEqual(direct.distribution);
    expect(shown.expectation).toEqual(direct.expectation);
    expect(shown.at_least).toEqual(direct.at_least);
    expect(shown.total_probability).toBe('1/1');

    // 每根柱子的分数标签 == 原始响应中的 num/den
    for (const row of shown.distribution) {
      const label = await page.getByTestId(`bar-label-${row.total}`).textContent();
      expect(label.trim()).toBe(`${row.num}/${row.den}`);
      const prob = await page.getByTestId(`bar-${row.total}`).getAttribute('data-probability');
      expect(prob).toBe(`${row.num}/${row.den}`);
    }

    // 期望与尾部概率展示 == 原始响应
    await expect(page.getByTestId('expectation')).toHaveText(
      `${shown.expectation.num}/${shown.expectation.den}`
    );
    await expect(page.getByTestId('at-least')).toHaveText(
      `${shown.at_least.num}/${shown.at_least.den}`
    );

    // 阈值高亮：总分 >= 阈值的柱子带 hit 类，其余不带
    for (const row of shown.distribution) {
      const cls = await page.getByTestId(`bar-${row.total}`).getAttribute('class');
      if (row.total >= PARAMS.threshold) expect(cls).toContain('hit');
      else expect(cls ?? '').not.toContain('hit');
    }

    // 概率合计为 1（用分数精确相加）
    const sum = shown.distribution.reduce(
      (acc, row) => acc + Number(row.num) / Number(row.den),
      0
    );
    expect(sum).toBeCloseTo(1, 12);
  });
});
