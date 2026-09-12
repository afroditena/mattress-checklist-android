import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: '쇼츠 대본 AI | 쇼핑 쇼츠 대본 자동 생성',
  description: '쿠팡 파트너스, 스마트스토어 셀러를 위한 AI 쇼핑 쇼츠 대본 생성 SaaS',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
