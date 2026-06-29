/** 羽毛球 21 分制比分校验（20 平后延分，领先 2 分获胜，封顶 30） */

export function isFinalScore(a: number, b: number): boolean {
  const w = Math.max(a, b);
  const l = Math.min(a, b);
  const d = w - l;
  return (
    (w === 21 && l <= 19) ||
    (w >= 22 && w <= 29 && d === 2) ||
    (w === 30 && l >= 28 && l <= 29)
  );
}

export function validateScorePair(a: number, b: number): string | null {
  if (a < 0 || b < 0 || a > 30 || b > 30) return "比分范围 0-30";

  const w = Math.max(a, b);
  const l = Math.min(a, b);
  const d = w - l;

  if (w === 21 && l <= 19) return null;
  if (w < 21) return null;
  if (w === 21 && l === 20) return null;

  if (d > 2) return "无效比分：分差不能超过 2 分";
  if (l < 20) return "无效比分";
  if (w === 30 && l !== 28 && l !== 29) return "无效比分：30 分时对方须为 28 或 29 分";
  if (d <= 2) return null;
  return "无效比分";
}

export function validateDirectScore(a: number, b: number): string | null {
  const base = validateScorePair(a, b);
  if (base) return base;
  if (isFinalScore(a, b)) return null;

  const w = Math.max(a, b);
  const l = Math.min(a, b);
  const d = w - l;

  if (w < 21) return null;
  if (w === 21 && l === 20) return null;
  if (d === 0 && l >= 20) return null;
  if (d === 1 && w >= 22) {
    return "无效比分：请录入完整终局比分（如 23-21、26-24），或使用 +1 逐分计分";
  }
  return "无效比分";
}
