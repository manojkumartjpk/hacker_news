import './globals.css'
import { Suspense } from 'react'
import Header from '../components/Header'
import Footer from '../components/Footer'

export const metadata = {
  title: 'Hacker News Clone',
  description: 'A clone of Hacker News built with Next.js and FastAPI',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <table
          id="hnmain"
          border="0"
          cellPadding="0"
          cellSpacing="0"
          width="85%"
          style={{ margin: '0 auto', backgroundColor: '#f6f6ef' }}
        >
          <tbody>
            <Suspense fallback={<tr><td style={{ backgroundColor: '#ff6600', height: '24px' }}>&nbsp;</td></tr>}>
              <Header />
            </Suspense>
            <tr style={{ height: '10px' }} />
            <tr>
              <td className="hncontent">
                {children}
              </td>
            </tr>
            <Footer />
          </tbody>
        </table>
      </body>
    </html>
  )
}
