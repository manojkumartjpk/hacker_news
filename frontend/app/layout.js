import './globals.css'

export const metadata = {
  title: 'Hacker News Clone',
  description: 'A clone of Hacker News built with Next.js and FastAPI',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}