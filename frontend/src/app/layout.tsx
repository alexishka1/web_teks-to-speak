import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TaSTP Studio — Platform Text-to-Speech Self-Hosted",
  description: "Platform Text-to-Speech mandiri untuk kreator konten video dan audio, ditenagai engine open-source lokal.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id">
      <body className="bg-background text-fg antialiased selection:bg-primary selection:text-primary-fg min-h-screen">
        {children}
      </body>
    </html>
  );
}
