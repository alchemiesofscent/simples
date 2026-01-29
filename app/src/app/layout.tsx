import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "simples",
  description: "Ancient Simples MVP"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
