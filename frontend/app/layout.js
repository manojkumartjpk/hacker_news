import './globals.css'
import Header from '../components/Header'

export const metadata = {
  title: 'Hacker News Clone',
  description: 'A clone of Hacker News built with Next.js and FastAPI',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, padding: 0 }}>
        <Header />
        <main style={{ margin: '0 auto', maxWidth: '1024px', padding: '4px' }}>
          {children}
        </main>
      </body>
    </html>
  )
}