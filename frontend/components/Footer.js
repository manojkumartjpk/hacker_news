export default function Footer() {
  return (
    <>
      <tr>
        <td>
          <img
            src="https://news.ycombinator.com/s.gif"
            height="10"
            width="0"
            alt=""
          />
        </td>
      </tr>
      <tr>
        <td>
          <table border="0" cellPadding="0" cellSpacing="0" width="100%">
            <tbody>
              <tr>
                <td style={{ backgroundColor: '#f6f6ef' }}>
                  <div style={{ borderTop: '2px solid #ff6600', height: '1px' }}></div>
                  <div style={{ textAlign: 'center', padding: '8px 0' }} className="subtext">
                    <a href="https://news.ycombinator.com/newsguidelines.html">Guidelines</a>
                    {' | '}
                    <a href="https://news.ycombinator.com/newsfaq.html">FAQ</a>
                    {' | '}
                    <a href="https://news.ycombinator.com/lists">Lists</a>
                    {' | '}
                    <a href="https://news.ycombinator.com/api">API</a>
                    {' | '}
                    <a href="https://news.ycombinator.com/security.html">Security</a>
                    {' | '}
                    <a href="https://news.ycombinator.com/legal">Legal</a>
                    {' | '}
                    <a href="https://www.ycombinator.com/apply/">Apply to YC</a>
                    {' | '}
                    <a href="mailto:hn@ycombinator.com">Contact</a>
                  </div>
                  <div style={{ textAlign: 'center', paddingBottom: '10px' }} className="subtext">
                    <form action="/search" method="GET">
                      Search:{' '}
                      <input type="text" name="q" size="17" />
                    </form>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </td>
      </tr>
    </>
  );
}
