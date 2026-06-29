import { useRef, useCallback } from "react";
import html2canvas from "html2canvas";

export function useImageExport() {
  const exportRef = useRef<HTMLDivElement>(null);

  const captureAndDownload = useCallback(async (filename: string) => {
    if (!exportRef.current) return;
    try {
      const canvas = await html2canvas(exportRef.current, {
        backgroundColor: "#ffffff",
        scale: 2,
        useCORS: true,
        allowTaint: false,
      });
      canvas.toBlob(blob => {
        if (!blob) return;
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.download = `${filename}.png`;
        link.href = url;
        link.click();
        URL.revokeObjectURL(url);
      }, "image/png");
    } catch (err) {
      console.warn("导出图片失败:", err);
    }
  }, []);

  return { exportRef, captureAndDownload };
}
