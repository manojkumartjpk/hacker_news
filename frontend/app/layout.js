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
      <body className="text-black">
        <table
          id="hnmain"
          border="0"
          cellPadding="0"
          cellSpacing="0"
          width="85%"
          className="mx-auto bg-[#f6f6ef] w-[85%] min-w-[796px]"
        >
          <tbody>
            <Suspense fallback={<tr><td className="bg-[#ff6600] h-6">&nbsp;</td></tr>}>
              <Header />
            </Suspense>
            <tr className="h-[10px]" />
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
